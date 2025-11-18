import { z } from 'zod';

// Convert JSON Schema to Zod schema
export function jsonSchemaToZod(schema: Record<string, any> | undefined): z.ZodType<any> {
  if (!schema) return z.unknown();

  const { type, properties, required = [], items, enum: enumValues } = schema;

  switch (type) {
    case 'string':
      let stringSchema = z.string();

      if (enumValues && Array.isArray(enumValues) && enumValues.length > 0) {
        return z.string().refine((val) => enumValues.includes(val), {
          message: `Must be one of: ${enumValues.join(', ')}`,
        });
      }

      if (schema.format === 'date-time') {
        return z.string().datetime();
      }

      if (schema.format === 'date') {
        return z.string().date();
      }

      if (schema.format === 'email') {
        return z.string().email();
      }

      if (schema.minLength) {
        stringSchema = stringSchema.min(schema.minLength);
      }

      if (schema.maxLength) {
        stringSchema = stringSchema.max(schema.maxLength);
      }

      return stringSchema;

    case 'number':
    case 'integer':
      let numberSchema = type === 'integer' ? z.number().int() : z.number();

      if (schema.minimum !== undefined) {
        numberSchema = numberSchema.min(schema.minimum);
      }

      if (schema.maximum !== undefined) {
        numberSchema = numberSchema.max(schema.maximum);
      }

      return numberSchema;

    case 'boolean':
      return z.boolean();

    case 'array':
      if (items) {
        const itemSchema = jsonSchemaToZod(items);
        let arraySchema = z.array(itemSchema);

        if (schema.minItems) {
          arraySchema = arraySchema.min(schema.minItems);
        }

        if (schema.maxItems) {
          arraySchema = arraySchema.max(schema.maxItems);
        }

        return arraySchema;
      }
      return z.array(z.unknown());

    case 'object':
      if (properties) {
        const shape: Record<string, z.ZodType<any>> = {};

        for (const [key, propSchema] of Object.entries(properties)) {
          const isRequired = required.includes(key);
          const zodSchema = jsonSchemaToZod(propSchema as Record<string, any>);

          shape[key] = isRequired ? zodSchema : zodSchema.optional();
        }

        return z.object(shape);
      }
      return z.record(z.string(), z.unknown());

    default:
      return z.unknown();
  }
}

// Convert an identifier like "first_word_last_word" to "First Word Last Word"
export function humanizeIdentifier(identifier: string): string {
  if (!identifier) return '';
  // Replace underscores with spaces and collapse multiple underscores
  const spaced = identifier.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
  // Title-case each word
  return spaced
    .split(' ')
    .map(word => (word.length > 0 ? word[0].toUpperCase() + word.slice(1).toLowerCase() : word))
    .join(' ');
}

// Get field description from schema
export function getFieldDescription(
  schema: Record<string, any> | undefined,
  fieldPath: string
): string | undefined {
  if (!schema) return undefined;

  const pathParts = fieldPath.split('.');
  let currentSchema = schema;

  for (const part of pathParts) {
    if (currentSchema.properties && currentSchema.properties[part]) {
      currentSchema = currentSchema.properties[part];
    } else if (currentSchema.items) {
      currentSchema = currentSchema.items;
    } else {
      return undefined;
    }
  }

  return currentSchema.description;
}

// Get field title from schema
export function getFieldTitle(
  schema: Record<string, any> | undefined,
  fieldPath: string
): string | undefined {
  if (!schema) return undefined;

  const pathParts = fieldPath.split('.');
  let currentSchema = schema;

  for (const part of pathParts) {
    if (currentSchema.properties && currentSchema.properties[part]) {
      currentSchema = currentSchema.properties[part];
    } else if (currentSchema.items) {
      currentSchema = currentSchema.items;
    } else {
      return undefined;
    }
  }

  // Prefer explicit title from schema; otherwise humanize the field identifier
  return currentSchema.title || humanizeIdentifier(pathParts[pathParts.length - 1]);
}

// Normalize form data based on JSON schema types to satisfy backend validation
export function normalizeDataBySchema(
  schema: Record<string, any> | undefined,
  data: Record<string, any>
): Record<string, any> {
  if (!schema || !schema.properties || typeof data !== 'object' || data === null) {
    return data;
  }

  const normalized: Record<string, any> = Array.isArray(data) ? [...(data as any[])] : { ...data };

  for (const [key, value] of Object.entries(data)) {
    const propSchema = schema.properties[key];
    if (!propSchema) continue;

    // Handle $ref or allOf/anyOf minimally by skipping deep resolution
    const type = propSchema.type as string | undefined;

    // Handle empty strings carefully
    if (value === '') {
      if (type === 'string') {
        // Keep empty string for required fields; drop for optional strings
        const reqList: string[] = Array.isArray(schema.required) ? schema.required : [];
        const isRequired = reqList.includes(key);
        if (!isRequired) {
          delete normalized[key];
          continue;
        }
      } else if (type) {
        // For non-string types, drop empty strings
        delete normalized[key];
        continue;
      }
    }

    if (type === 'number' || type === 'integer') {
      if (value === '' || value === null || value === undefined) {
        delete normalized[key];
      } else if (typeof value === 'string') {
        const num = type === 'integer' ? parseInt(value, 10) : parseFloat(value);
        if (!isNaN(num)) normalized[key] = num; else delete normalized[key];
      }
    } else if (type === 'boolean') {
      if (typeof value === 'string') {
        if (value.toLowerCase() === 'true') normalized[key] = true;
        else if (value.toLowerCase() === 'false') normalized[key] = false;
      }
    } else if (type === 'array') {
      if (!Array.isArray(value)) {
        // Convert single value to array if not empty
        if (value !== '' && value !== null && value !== undefined) {
          normalized[key] = [value];
        } else {
          delete normalized[key];
        }
      } else {
        // Optionally normalize items by item type
        const itemSchema = propSchema.items as Record<string, any> | undefined;
        if (itemSchema && itemSchema.type && (itemSchema.type === 'number' || itemSchema.type === 'integer')) {
          normalized[key] = (value as any[])
            .filter(v => v !== '' && v !== null && v !== undefined)
            .map(v => typeof v === 'string' ? (itemSchema.type === 'integer' ? parseInt(v, 10) : parseFloat(v)) : v)
            .filter(v => typeof v === 'number' && !isNaN(v as number));
        } else if (itemSchema && itemSchema.type === 'object') {
          // Normalize each object item and remove empty objects
          normalized[key] = (value as any[])
            .map(v => (typeof v === 'object' && v !== null) ? normalizeDataBySchema(itemSchema, v as Record<string, any>) : v)
            .filter(v => {
              if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
                return Object.keys(v as Record<string, any>).length > 0;
              }
              return v !== '' && v !== null && v !== undefined;
            });
        } else if (itemSchema && itemSchema.type === 'string') {
          normalized[key] = (value as any[]).filter(v => typeof v === 'string' ? v.trim() !== '' : v !== null && v !== undefined);
        } else {
          normalized[key] = (value as any[]).filter(v => v !== '' && v !== null && v !== undefined);
        }
        if ((normalized[key] as any[]).length === 0) delete normalized[key];
      }
    } else if (type === 'object') {
      if (typeof value === 'object' && value !== null) {
        const child = normalizeDataBySchema(propSchema as Record<string, any>, value as Record<string, any>);
        if (typeof child === 'object' && child !== null && Object.keys(child).length > 0) {
          normalized[key] = child;
        } else {
          delete normalized[key];
        }
      }
    }
  }

  return normalized;
}

// Check if field is required
export function isFieldRequired(
  schema: Record<string, any> | undefined,
  fieldPath: string
): boolean {
  if (!schema) return false;

  const pathParts = fieldPath.split('.');
  let currentSchema = schema;
  const required = schema.required || [];

  for (let i = 0; i < pathParts.length - 1; i++) {
    const part = pathParts[i];
    if (currentSchema.properties && currentSchema.properties[part]) {
      currentSchema = currentSchema.properties[part];
    } else {
      return false;
    }
  }

  const fieldName = pathParts[pathParts.length - 1];
  return required.includes(fieldName);
}