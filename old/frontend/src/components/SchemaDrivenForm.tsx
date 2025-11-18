import React from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Card,
  CardContent,
  Button,
  IconButton,
} from '@mui/material';
import { Add as AddIcon, Remove as RemoveIcon } from '@mui/icons-material';
import { Controller, useFormContext } from 'react-hook-form';
import { getFieldDescription, getFieldTitle, humanizeIdentifier } from '../utils/schemaUtils';
import type { MetadataFile } from '../types/api';

import FieldStatusIndicator from './FieldStatusIndicator';

interface SchemaDrivenFormProps {
  metadataFile: MetadataFile;
  onDataChange: (data: Record<string, any>) => void;
  sections?: Array<{
    id: string;
    title: string;
    fields: Array<{
      id: string;
      title: string;
      required: boolean;
      completed: boolean;
      hasError: boolean;
      isEmpty: boolean;
    }>;
  }>;
  activeSection?: string;
  fieldStatus?: ReturnType<typeof import('../hooks/useFieldStatus').useFieldStatus>;
}

const SchemaDrivenForm: React.FC<SchemaDrivenFormProps> = ({
  metadataFile,
  onDataChange,
  sections,
  activeSection,
  fieldStatus
}) => {
  const { content, schema_info, schema_definition: schema } = metadataFile;
  // const [focusedField, setFocusedField] = React.useState<string | null>(null);

  const { control, watch, setValue, formState: { errors } } = useFormContext();
  // Determine if a field (by full JSON pointer-like path) is required in schema
  const isRequiredAtPath = React.useCallback((fullPath: string): boolean => {
    if (!schema) return false;
    const parts = fullPath.split('.');
    if (parts.length === 0) return false;
    // We need the parent schema of the last segment
    let current: any = schema;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      // Skip numeric indices for arrays
      const isIndex = /^\d+$/.test(part);
      if (current?.type === 'array') {
        current = current.items || {};
        if (isIndex) continue; // move to next path segment
      }
      if (!isIndex && current?.properties && current.properties[part]) {
        current = current.properties[part];
      }
    }
    const lastKey = parts[parts.length - 1];
    const parent = current;
    const req: string[] = Array.isArray(parent?.required) ? parent.required : [];
    return req.includes(lastKey);
  }, [schema]);

  const watchedValues = watch();

  // Clean up invalid enum values
  const cleanInvalidEnumValues = (data: Record<string, any>, schema: Record<string, any>): Record<string, any> => {
    if (!schema || !schema.properties) return data;

    const cleaned = { ...data };
    Object.entries(schema.properties).forEach(([fieldName, fieldSchema]: [string, any]) => {
      if (fieldSchema.enum && Array.isArray(fieldSchema.enum)) {
        const value = cleaned[fieldName];
        if (value && !fieldSchema.enum.includes(value)) {
          // Replace invalid enum values with empty string
          cleaned[fieldName] = '';
        }
      }
    });
    return cleaned;
  };

  // Update parent when form data changes
  React.useEffect(() => {
    const cleanedValues = cleanInvalidEnumValues(watchedValues, schema);
    onDataChange(cleanedValues);
  }, [watchedValues, onDataChange, schema]);

  // Also update parent when individual fields change
  // const handleFieldChange = (fieldPath: string, value: any) => {
  //   setValue(fieldPath, value);
  //   // Trigger parent update
  //   const updatedData = { ...watchedValues, [fieldPath]: value };
  //   onDataChange(updatedData);
  // };

  const renderField = (
    fieldName: string,
    fieldSchema: Record<string, any>,
    fieldPath: string = '',
    parentData: Record<string, any> = content
  ): React.ReactNode => {
    const fullPath = fieldPath ? `${fieldPath}.${fieldName}` : fieldName;
    const fieldValue = parentData[fieldName];
    const error = errors[fullPath];
    const isRequired = isRequiredAtPath(fullPath);

    const fieldTitle = getFieldTitle(schema, fullPath) || humanizeIdentifier(fieldName);
    const fieldDescription = getFieldDescription(schema, fullPath);

    const handleFocus = () => {
      // setFocusedField(fullPath);
    };

    const handleBlur = () => {
      // setFocusedField(null);
    };

    // Check if this is a system field that should be read-only
    const isSystemField = (
      ['created_by', 'created_date', 'last_modified_by', 'last_modified_date'].includes(fieldName)
      || fieldSchema?.readOnly === true
      || ['project_identifier', 'dataset_identifier', 'associated_project_identifier', 'dataset_identifier_link', 'experiment_identifier_run_id', 'experiment_template_type'].includes(fieldName)
    );

    // Render system fields as read-only display
    if (isSystemField) {
      return (
        <Box data-field-id={fieldName} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {fieldTitle}
              {fieldStatus && (
                <FieldStatusIndicator
                  status={fieldStatus.getFieldStatus(fieldName)}
                  variant="icon"
                  size="small"
                />
              )}
            </Box>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {fieldDescription}
          </Typography>
          <Typography variant="body1" sx={{
            p: 1,
            backgroundColor: 'var(--fair-surface)',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'var(--fair-border-light)',
            color: 'var(--fair-text-primary)',
            fontFamily: 'monospace',
            fontSize: '0.875rem'
          }}>
            {fieldValue || 'Not set'}
          </Typography>
        </Box>
      );
    }

    switch (fieldSchema.type) {
      case 'string':
        if (fieldSchema.enum) {
          return (
            <Box data-field-id={fieldName}>
              <Controller
              name={fullPath}
              control={control}
              defaultValue={fieldValue || ''}
              render={({ field }) => (
                <FormControl fullWidth error={!!error} required={isRequired} sx={{
                  mb: 1,
                  ...(isRequired && {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'rgba(25, 118, 210, 0.3)',
                        borderWidth: '1px',
                      },
                    },
                  }),
                }}>
                  <InputLabel>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {fieldTitle}

                      {fieldStatus && (
                        <FieldStatusIndicator
                          status={fieldStatus.getFieldStatus(fieldName)}
                          variant="icon"
                          size="small"
                        />
                      )}
                    </Box>
                  </InputLabel>
                  <Select
                    {...field}
                    label={fieldTitle}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    disabled={isSystemField}
                  >
                    {fieldSchema.enum.map((option: string) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                  {error && (
                    <Typography variant="caption" color="error">
                      {error.message as string}
                    </Typography>
                  )}

                </FormControl>
              )}
              />
            </Box>
          );
        }

        if (fieldSchema.format === 'date-time') {
          return (
            <Box data-field-id={fieldName}>
              <Controller
              name={fullPath}
              control={control}
              defaultValue={fieldValue || ''}
              render={({ field }) => (
                <TextField
                  {...field}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {fieldTitle}

                      {fieldStatus && (
                        <FieldStatusIndicator
                          status={fieldStatus.getFieldStatus(fieldName)}
                          variant="icon"
                          size="small"
                        />
                      )}
                    </Box>
                  }
                  type="datetime-local"
                  fullWidth
                  required={isRequired}
                  error={!!error}
                  helperText={error?.message?.toString() || fieldDescription}
                  onFocus={handleFocus}
                  onBlur={handleBlur}
                  InputLabelProps={{ shrink: true }}
                  disabled={isSystemField}
                />
              )}
              />
            </Box>
          );
        }

        // Build validation rules and placeholders for string inputs
        const rules: any = {};
        let placeholder: string | undefined;
        let type: string | undefined;
        if (fieldSchema.format === 'email') {
          type = 'email';
          rules.pattern = {
            value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Enter a valid email (e.g., name@example.com)'
          };
          placeholder = 'name@example.com';
        }
        if (fieldSchema.pattern && /orcid\.org/.test(fieldSchema.pattern)) {
          try {
            const rx = new RegExp(fieldSchema.pattern);
            rules.pattern = { value: rx, message: 'Enter a valid ORCID URL (e.g., https://orcid.org/0000-0000-0000-0000)' };
          } catch {}
          placeholder = 'https://orcid.org/0000-0000-0000-0000';
        }
        return (
          <Box data-field-id={fieldName}>
            <Controller
            name={fullPath}
            control={control}
            defaultValue={fieldValue || ''}
            rules={rules}
            render={({ field }) => (
              <TextField
                {...field}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {fieldTitle}
                    {fieldStatus && (
                      <FieldStatusIndicator
                        status={fieldStatus.getFieldStatus(fieldName)}
                        variant="icon"
                        size="small"
                      />
                    )}
                  </Box>
                }
                fullWidth
                required={isRequired}
                error={!!error}
                helperText={error?.message?.toString() || fieldDescription}
                onFocus={handleFocus}
                onBlur={handleBlur}
                type={type}
                placeholder={placeholder}
                multiline={fieldSchema.maxLength > 100}
                rows={fieldSchema.maxLength > 100 ? 4 : 1}
                sx={{
                  mb: 1,
                  ...(isRequired && {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'rgba(25, 118, 210, 0.3)',
                        borderWidth: '1px',
                      },
                    },
                  }),
                }}
                disabled={isSystemField}
              />
            )}
          />
          </Box>
        );

      case 'number':
      case 'integer':
        return (
          <Box data-field-id={fieldName}>
            <Controller
            name={fullPath}
            control={control}
            defaultValue={fieldValue || ''}
            render={({ field }) => (
              <TextField
                {...field}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {fieldTitle}
                    {fieldStatus && (
                      <FieldStatusIndicator
                        status={fieldStatus.getFieldStatus(fieldName)}
                        variant="icon"
                        size="small"
                      />
                    )}
                  </Box>
                }
                type="number"
                fullWidth
                required={isRequired}
                error={!!error}
                                  helperText={error?.message?.toString() || fieldDescription}
                onFocus={handleFocus}
                onBlur={handleBlur}
                inputProps={{
                  min: fieldSchema.minimum,
                  max: fieldSchema.maximum,
                  step: fieldSchema.type === 'integer' ? 1 : 'any',
                }}
                sx={{
                  mb: 1,
                  ...(isRequired && {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: 'rgba(25, 118, 210, 0.3)',
                        borderWidth: '1px',
                      },
                    },
                  }),
                }}
                disabled={isSystemField}
              />
            )}
            />
          </Box>
        );

      case 'boolean':
        return (
          <Box data-field-id={fieldName}>
            <Controller
            name={fullPath}
            control={control}
            defaultValue={fieldValue || false}
            render={({ field }) => (
              <Box sx={{ mb: 1 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      {...field}
                      checked={field.value}
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {fieldTitle}

                      {fieldStatus && (
                        <FieldStatusIndicator
                          status={fieldStatus.getFieldStatus(fieldName)}
                          variant="icon"
                          size="small"
                        />
                      )}
                    </Box>
                  }
                />

              </Box>
            )}
            />
          </Box>
        );

      case 'array':
        return (
          <Box data-field-id={fieldName} sx={{
            mb: 3,
            ...(isRequired && {
              border: '1px solid rgba(25, 118, 210, 0.3)',
              borderRadius: 1,
              p: 2,
              bgcolor: 'rgba(25, 118, 210, 0.02)',
            }),
          }}>
            <Typography variant="subtitle2" gutterBottom>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {fieldTitle}
                {fieldStatus && (
                  <FieldStatusIndicator
                    status={fieldStatus.getFieldStatus(fieldName)}
                    variant="icon"
                    size="small"
                  />
                )}
              </Box>
            </Typography>

            {fieldDescription && (
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom sx={{ mb: 2 }}>
                {fieldDescription}
              </Typography>
            )}
            <ArrayField
              fieldPath={fullPath}
              fieldSchema={fieldSchema}
              fieldValue={fieldValue || []}
              control={control}
              setValue={setValue}
              watch={watch}
              onFocus={handleFocus}
              onBlur={handleBlur}
              renderField={renderField}
            />
          </Box>
        );

      case 'object':
        return (
                    <Card data-field-id={fieldName} variant="outlined" sx={{
            mb: 3,
            p: 2,
            ...(isRequired && {
              borderColor: 'rgba(25, 118, 210, 0.5)',
              bgcolor: 'rgba(25, 118, 210, 0.02)',
            }),
          }}>
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Typography variant="subtitle2" gutterBottom>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {fieldTitle}
                  {fieldStatus && (
                    <FieldStatusIndicator
                      status={fieldStatus.getFieldStatus(fieldName)}
                      variant="icon"
                      size="small"
                    />
                  )}
                </Box>
              </Typography>

              {fieldDescription && (
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom sx={{ mb: 2 }}>
                  {fieldDescription}
                </Typography>
              )}
              <Box sx={{ pl: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                {fieldSchema.properties &&
                  Object.entries(fieldSchema.properties).map(([propName, propSchema]) => (
                    <Box key={propName}>
                      {renderField(propName, propSchema as Record<string, any>, fullPath, fieldValue || {})}
                    </Box>
                  ))}
              </Box>
            </CardContent>
          </Card>
        );

      default:
        return (
          <TextField
            label={fieldTitle}
            value={fieldValue || ''}
            fullWidth
            disabled
            helperText="Unsupported field type"
          />
        );
    }
  };

  // Render sections if provided, otherwise render flat form
  if (sections && sections.length > 0) {
    return (
      <Box sx={{ height: '100%', overflow: 'auto' }}>
        {sections.map((section) => (
          <Box
            key={section.id}
            id={`section-${section.id}`}
            data-section-id={section.id}
            className={`form-section ${activeSection === section.id ? 'active-section' : ''}`}
            sx={{
              mt: 2,
              mb: 4,
              p: 3,
              pt: 1,
              backgroundColor: 'var(--fair-surface)',
              border: '1px solid var(--fair-border-light)',
              borderRadius: 'var(--fair-radius-lg)',
              boxShadow: 'var(--fair-shadow-sm)',
              scrollMarginTop: 'var(--fair-spacing-xl)',
              transition: 'all 0.3s ease-in-out',
              position: 'relative',
              ...(activeSection === section.id && {
                borderColor: 'var(--fair-primary)',
                boxShadow: 'var(--fair-shadow-md)',
                transform: 'translateY(-2px)',
              }),
            }}
          >
            <Typography
              variant="h6"
              gutterBottom
              sx={{
                color: 'var(--fair-text-primary)',
                fontWeight: 600,
                mb: 2,
              }}
            >
              {section.title}
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {section.fields.map((field) => {
                const fieldSchema = schema?.properties?.[field.id];
                if (!fieldSchema) return null;

                return (
                  <Box key={field.id} sx={{ mb: 1 }}>
                    {renderField(field.id, fieldSchema as Record<string, any>)}
                  </Box>
                );
              })}
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  // Fallback to flat form rendering
  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        {schema_info.schema_title}
      </Typography>
      <Typography variant="caption" color="text.secondary" gutterBottom display="block" sx={{ mb: 3 }}>
        Schema: {schema_info.schema_id} ({schema_info.source})
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {schema && schema.properties &&
          Object.entries(schema.properties).map(([fieldName, fieldSchema]) => (
            <Box key={fieldName} sx={{ mb: 2 }}>
              {renderField(fieldName, fieldSchema as Record<string, any>)}
            </Box>
          ))}
        {(!schema || !schema.properties) && (
          <Typography variant="body2" color="text.secondary">
            No schema definition available for this metadata type.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

// Array field component
interface ArrayFieldProps {
  fieldPath: string;
  fieldSchema: Record<string, any>;
  fieldValue: any[];
  control: any;
  setValue: any;
  watch: any;
  onFocus: () => void;
  onBlur: () => void;
  renderField?: (
    fieldName: string,
    fieldSchema: Record<string, any>,
    fieldPath: string,
    parentData: Record<string, any>
  ) => React.ReactNode;
}

const ArrayField: React.FC<ArrayFieldProps> = ({
  fieldPath,
  fieldSchema,
  // fieldValue,
  control,
  setValue,
  watch,
  onFocus,
  onBlur,
  renderField,
}) => {
  // Watch the current value of this array field to ensure we're working with the latest data
  const currentArrayValue = watch(fieldPath) || [];

  const addItem = () => {
    console.log('Add item clicked for field:', fieldPath);
    console.log('Current array value:', currentArrayValue);
    console.log('Field schema items type:', fieldSchema.items?.type);

    const newValue = [...currentArrayValue];
    if (fieldSchema.items?.type === 'object') {
      const props = fieldSchema.items?.properties || {};
      const req: string[] = Array.isArray(fieldSchema.items?.required) ? fieldSchema.items.required : [];
      const defaultObj: any = {};
      Object.entries(props).forEach(([propName, propSchema]: [string, any]) => {
        if (req.includes(propName)) {
          if (propSchema?.format === 'email') defaultObj[propName] = '';
          else if (propSchema?.pattern && /orcid\.org/.test(propSchema.pattern)) defaultObj[propName] = '';
          else defaultObj[propName] = '';
        } else {
          // initialize optional fields to empty string for user to fill
          defaultObj[propName] = '';
        }
      });
      newValue.push(defaultObj);
    } else if (fieldSchema.items?.type === 'string') {
      newValue.push('');
    } else if (fieldSchema.items?.type === 'number') {
      newValue.push(0);
    } else {
      newValue.push(null);
    }

    console.log('New array value:', newValue);
    setValue(fieldPath, newValue);
    console.log('setValue called for:', fieldPath);
  };

  const removeItem = (index: number) => {
    console.log('Remove item clicked for index:', index, 'field:', fieldPath);
    const newValue = currentArrayValue.filter((_: any, i: number) => i !== index);
    setValue(fieldPath, newValue);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {currentArrayValue.map((item: any, index: number) => (
        <Box key={index} sx={{ mb: 1 }}>
          {fieldSchema.items?.type === 'object' && fieldSchema.items?.properties && renderField ? (
            <Card variant="outlined" sx={{ p: 1 }}>
              <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Item {index + 1}</Typography>
                  <IconButton onClick={() => removeItem(index)} color="error" size="small">
                    <RemoveIcon />
                  </IconButton>
                </Box>
                <Box sx={{ pl: 1, display: 'grid', gridTemplateColumns: '1fr', gap: 1 }}>
                  {Object.entries(fieldSchema.items.properties).map(([propName, propSchema]: [string, any]) => (
                    <Box key={propName}>
                      {renderField(propName, propSchema as Record<string, any>, `${fieldPath}.${index}`, currentArrayValue[index] || {})}
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Controller
                name={`${fieldPath}.${index}`}
                control={control}
                defaultValue={item}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={`Item ${index + 1}`}
                    fullWidth
                    onFocus={onFocus}
                    onBlur={onBlur}
                    sx={{ mb: 1 }}
                  />
                )}
              />
              <IconButton onClick={() => removeItem(index)} color="error" size="small">
                <RemoveIcon />
              </IconButton>
            </Box>
          )}
        </Box>
      ))}
      <Button
        startIcon={<AddIcon />}
        onClick={addItem}
        variant="outlined"
        size="small"
        onFocus={onFocus}
        onBlur={onBlur}
        sx={{ alignSelf: 'flex-start' }}
      >
        Add Item
      </Button>
    </Box>
  );
};

export default SchemaDrivenForm;