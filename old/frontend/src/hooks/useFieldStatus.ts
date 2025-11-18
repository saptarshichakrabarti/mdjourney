import { useEffect, useRef, useState } from 'react';
import type { FieldErrors } from 'react-hook-form';

export interface FieldStatus {
  id: string;
  isModified: boolean;
  isCompleted: boolean;
  hasError: boolean;
  isRequired: boolean;
  isEmpty: boolean;
  isSystemField: boolean;
  originalValue: any;
  currentValue: any;
  errorMessage?: string;
}

export interface UseFieldStatusOptions {
  formMethods: {
    watch: () => Record<string, any>;
    formState: {
      errors: FieldErrors;
      dirtyFields: Record<string, any>;
    };
  };
  originalData: Record<string, any>;
  requiredFields: string[];
  systemFields: string[];
}

/**
 * Hook to track field status (modified, completed, error, required)
 */
export const useFieldStatus = ({
  formMethods,
  originalData,
  requiredFields,
  systemFields
}: UseFieldStatusOptions) => {
  const { watch, formState: { errors, dirtyFields } } = formMethods;
  const [fieldStatuses, setFieldStatuses] = useState<Map<string, FieldStatus>>(new Map());
  const originalDataRef = useRef(originalData);

  // Update original data reference when it changes
  useEffect(() => {
    originalDataRef.current = originalData;
  }, [originalData]);

  // Watch all form values
  const currentValues = watch();

  // Helper function to check if a value is empty
  const isValueEmpty = (value: any): boolean => {
    if (value === null || value === undefined || value === '') return true;
    if (Array.isArray(value) && value.length === 0) return true;
    if (typeof value === 'object' && value !== null && Object.keys(value).length === 0) return true;
    if (typeof value === 'string' && value.trim() === 'To be filled') return true;
    return false;
  };

  // Helper function to check if a value indicates completion
  const isValueCompleted = (value: any): boolean => {
    if (isValueEmpty(value)) return false;
    if (typeof value === 'string' && value.trim() === 'To be filled') return false;
    return true;
  };

  // Helper function to check if a field is a system field
  const isSystemField = (fieldId: string): boolean => {
    return systemFields.includes(fieldId);
  };

  // Update field statuses when form values change
  useEffect(() => {
    const newStatuses = new Map<string, FieldStatus>();

    // Get all field names from both original data and current values
    const allFieldNames = new Set([
      ...Object.keys(originalDataRef.current),
      ...Object.keys(currentValues)
    ]);

    allFieldNames.forEach(fieldId => {
      const originalValue = originalDataRef.current[fieldId];
      const currentValue = currentValues[fieldId];
      const error = errors[fieldId];
      const isDirty = dirtyFields[fieldId];
      const isRequired = requiredFields.includes(fieldId);
      const isEmpty = isValueEmpty(currentValue);
      const isCompleted = isValueCompleted(currentValue);
      const isSystem = isSystemField(fieldId);

      // Check if field is modified (comparing with original value)
      const isModified = isDirty || JSON.stringify(originalValue) !== JSON.stringify(currentValue);

      const status: FieldStatus = {
        id: fieldId,
        isModified,
        isCompleted,
        hasError: !!error,
        isRequired,
        isEmpty,
        isSystemField: isSystem,
        originalValue,
        currentValue,
        errorMessage: error?.message?.toString(),
      };

      newStatuses.set(fieldId, status);
    });

    setFieldStatuses(newStatuses);
  }, [
    JSON.stringify(currentValues),
    JSON.stringify(errors),
    JSON.stringify(dirtyFields),
    JSON.stringify(requiredFields),
    JSON.stringify(systemFields)
  ]);

  // Get status for a specific field
  const getFieldStatus = (fieldId: string): FieldStatus | undefined => {
    return fieldStatuses.get(fieldId);
  };

  // Get overall statistics
  const getOverallStats = () => {
    const statuses = Array.from(fieldStatuses.values());
    return {
      total: statuses.length,
      modified: statuses.filter(s => s.isModified && !s.isSystemField).length,
      completed: statuses.filter(s => s.isCompleted).length,
      errors: statuses.filter(s => s.hasError).length,
      required: statuses.filter(s => s.isRequired).length,
      requiredCompleted: statuses.filter(s => s.isRequired && s.isCompleted).length,
      system: statuses.filter(s => s.isSystemField).length,
    };
  };

  // Get statuses for a list of field IDs
  const getFieldStatuses = (fieldIds: string[]): FieldStatus[] => {
    return fieldIds.map(id => fieldStatuses.get(id)).filter(Boolean) as FieldStatus[];
  };

  return {
    fieldStatuses,
    getFieldStatus,
    getOverallStats,
    getFieldStatuses,
  };
};