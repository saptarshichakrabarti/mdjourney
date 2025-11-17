import type { MetadataFile } from '../types/api';
import { humanizeIdentifier } from './schemaUtils';

export interface FormFieldAnalysis {
  id: string;
  title: string;
  required: boolean;
  completed: boolean;
  hasError: boolean;
  isEmpty: boolean;
  value: any;
}

export interface FormSectionAnalysis {
  id: string;
  title: string;
  fields: FormFieldAnalysis[];
  progress: number;
  requiredProgress: number;
}

export interface FormAnalysis {
  sections: FormSectionAnalysis[];
  totalFields: number;
  completedFields: number;
  requiredFields: number;
  completedRequiredFields: number;
  errorFields: number;
  overallProgress: number;
  requiredProgress: number;
}

/**
 * Creates logical sections based on metadata type and field patterns
 */
const createSections = (
  properties: Record<string, any>,
  metadataType: string,
  schemaTitle: string
): Array<{id: string, title: string, fieldNames: string[]}> => {
  const fieldNames = Object.keys(properties);

  // Define section patterns based on metadata type
  if (metadataType === 'experiment_contextual') {
    return [
      {
        id: 'experiment_info',
        title: 'Experiment Information',
        fieldNames: fieldNames.filter(name =>
          name.includes('experiment_') ||
          name.includes('protocol_') ||
          name === 'experimenters' ||
          name === 'experiment_dates'
        )
      },
      {
        id: 'sample_info',
        title: 'Sample Information',
        fieldNames: fieldNames.filter(name =>
          name.includes('sample_') ||
          name.includes('batch_') ||
          name === 'unique_sample_batch_identifiers'
        )
      },
      {
        id: 'instrumentation',
        title: 'Instrumentation & Methods',
        fieldNames: fieldNames.filter(name =>
          name.includes('instrument_') ||
          name.includes('software_') ||
          name.includes('sequencing_') ||
          name.includes('microscope_') ||
          name.includes('imaging_') ||
          name.includes('objective_') ||
          name.includes('reagent_')
        )
      },
      {
        id: 'quality_data',
        title: 'Quality Control & Data',
        fieldNames: fieldNames.filter(name =>
          name.includes('quality_') ||
          name.includes('qc_') ||
          name.includes('data_') ||
          name.includes('links_') ||
          name.includes('raw_')
        )
      },
      {
        id: 'notes_metadata',
        title: 'Notes & Metadata',
        fieldNames: fieldNames.filter(name =>
          name.includes('notes') ||
          name.includes('observations') ||
          name.includes('created_') ||
          name.includes('modified_') ||
          name.includes('identifier') ||
          name === 'dataset_identifier_link'
        )
      }
    ];
  } else if (metadataType === 'dataset_administrative') {
    return [
      {
        id: 'basic_info',
        title: 'Basic Information',
        fieldNames: fieldNames.filter(name =>
          name.includes('title') ||
          name.includes('description') ||
          name.includes('identifier') ||
          name.includes('version')
        )
      },
      {
        id: 'people_organizations',
        title: 'People & Organizations',
        fieldNames: fieldNames.filter(name =>
          name.includes('creator') ||
          name.includes('contributor') ||
          name.includes('contact') ||
          name.includes('organization') ||
          name.includes('affiliation')
        )
      },
      {
        id: 'dates_lifecycle',
        title: 'Dates & Lifecycle',
        fieldNames: fieldNames.filter(name =>
          name.includes('date') ||
          name.includes('created') ||
          name.includes('modified') ||
          name.includes('published')
        )
      },
      {
        id: 'access_rights',
        title: 'Access & Rights',
        fieldNames: fieldNames.filter(name =>
          name.includes('license') ||
          name.includes('rights') ||
          name.includes('access') ||
          name.includes('embargo')
        )
      }
    ];
  } else if (metadataType === 'dataset_structural') {
    return [
      {
        id: 'structure',
        title: 'Data Structure',
        fieldNames: fieldNames.filter(name =>
          name.includes('format') ||
          name.includes('type') ||
          name.includes('structure') ||
          name.includes('schema')
        )
      },
      {
        id: 'files_storage',
        title: 'Files & Storage',
        fieldNames: fieldNames.filter(name =>
          name.includes('file') ||
          name.includes('path') ||
          name.includes('storage') ||
          name.includes('location')
        )
      },
      {
        id: 'technical',
        title: 'Technical Details',
        fieldNames: fieldNames.filter(name =>
          name.includes('encoding') ||
          name.includes('compression') ||
          name.includes('checksum') ||
          name.includes('size')
        )
      }
    ];
  }

  // Default: single section for other metadata types
  return [
    {
      id: 'general',
      title: schemaTitle || 'Metadata Fields',
      fieldNames: fieldNames
    }
  ];
};

/**
 * Analyzes form data and schema to provide navigation and progress information
 */
export const analyzeFormData = (
  metadataFile: MetadataFile,
  formData: Record<string, any>,
  formErrors: Record<string, any> = {}
): FormAnalysis => {
  const { content, schema_definition: schema, schema_info } = metadataFile;
  // Infer metadata type from schema_id
  const metadata_type = schema_info.schema_id.replace('.json', '');
  const properties = schema?.properties || {};
  const requiredFields = schema?.required || [];
  const schemaTitle = schema?.title || 'Metadata';

  // Create logical sections
  const sectionDefinitions = createSections(properties, metadata_type, schemaTitle);

  // Build sections with field analysis
  const sections: FormSectionAnalysis[] = sectionDefinitions.map(sectionDef => {
    const sectionFields: FormFieldAnalysis[] = sectionDef.fieldNames
      .filter(fieldName => properties[fieldName]) // Only include fields that exist in schema
      .map(fieldName => {
        const fieldSchema = properties[fieldName];
        const value = formData[fieldName] ?? content[fieldName];
        const isRequired = requiredFields.includes(fieldName);
        const hasError = !!formErrors[fieldName];

        // Determine if field is completed
        const isEmpty = value === null || value === undefined || value === '' ||
                       (Array.isArray(value) && value.length === 0) ||
                       (typeof value === 'object' && value !== null && Object.keys(value).length === 0);

        const isPlaceholder = typeof value === 'string' && value === 'To be filled';
        const completed = !isEmpty && !isPlaceholder;

        return {
          id: fieldName,
          title: fieldSchema?.title || humanizeIdentifier(fieldName),
          required: isRequired,
          completed,
          hasError,
          isEmpty: isEmpty || isPlaceholder,
          value,
        };
      });

    return {
      id: sectionDef.id,
      title: sectionDef.title,
      fields: sectionFields,
      progress: sectionFields.length > 0 ? (sectionFields.filter(f => f.completed).length / sectionFields.length) * 100 : 0,
      requiredProgress: sectionFields.filter(f => f.required).length > 0
        ? (sectionFields.filter(f => f.required && f.completed).length / sectionFields.filter(f => f.required).length) * 100
        : 100,
    };
  }).filter(section => section.fields.length > 0); // Only include sections with fields

  // Calculate overall statistics
  const allFields = sections.flatMap(s => s.fields);
  const totalFields = allFields.length;
  const completedFields = allFields.filter(f => f.completed).length;
  const requiredFieldsList = allFields.filter(f => f.required);
  const completedRequiredFields = requiredFieldsList.filter(f => f.completed).length;
  const errorFields = allFields.filter(f => f.hasError).length;

  return {
    sections,
    totalFields,
    completedFields,
    requiredFields: requiredFieldsList.length,
    completedRequiredFields,
    errorFields,
    overallProgress: totalFields > 0 ? (completedFields / totalFields) * 100 : 0,
    requiredProgress: requiredFieldsList.length > 0 ? (completedRequiredFields / requiredFieldsList.length) * 100 : 100,
  };
};

/**
 * Scrolls to a specific field in the form
 */
export const scrollToField = (fieldId: string) => {
  const element = document.querySelector(`[data-field-id="${fieldId}"]`);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });

    // Focus the field if it's an input
    const input = element.querySelector('input, textarea, select') as HTMLElement;
    if (input && typeof input.focus === 'function') {
      setTimeout(() => input.focus(), 300);
    }
  }
};

/**
 * Determines if a field should be considered a system field (read-only)
 */
export const isSystemField = (fieldName: string, fieldSchema?: any): boolean => {
  const systemFields = [
    'created_by',
    'created_date',
    'last_modified_by',
    'last_modified_date',
    'project_identifier',
    'dataset_identifier',
    'associated_project_identifier',
    'dataset_identifier_link',
    'experiment_identifier_run_id',
    'experiment_template_type'
  ];

  return systemFields.includes(fieldName) || fieldSchema?.readOnly === true;
};