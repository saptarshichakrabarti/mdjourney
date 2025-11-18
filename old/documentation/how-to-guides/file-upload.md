# File Upload Feature Guide

## Overview

The file upload feature allows users to upload files directly to a dataset's metadata folder (`.metadata` directory) and automatically tracks these files in the dataset's structural metadata. This provides a convenient way to attach documentation, protocols, or other supporting files to datasets while maintaining proper metadata tracking.

## Features

- **Direct Upload**: Upload files through the web interface
- **Automatic Metadata Integration**: File information is automatically added to dataset structural metadata
- **Comment Support**: Add descriptions or comments about uploaded files
- **File Organization**: Files are stored in the `.metadata` folder alongside other metadata files
- **Security**: Filename sanitization and conflict resolution
- **Real-time Updates**: Frontend immediately reflects changes after upload

## How to Use

### Via Web Interface

1. **Select a Dataset**: Navigate to the dataset you want to upload files to
2. **Open Metadata Editor**: Click on the dataset to open the metadata editor
3. **Click Upload Button**: Look for the "Upload File" button in the action bar
4. **Select File**: Choose the file you want to upload from your system
5. **Add Description** (Optional): In the upload dialog, add a description of what the file contains
6. **Confirm Upload**: Click "Upload File" to complete the upload

### Via API

```bash
# Upload a file with a comment
curl -X POST "http://localhost:8000/api/v1/datasets/{dataset_id}/upload?comment=Protocol%20documentation" \
  -F "file=@protocol.pdf"

# Upload a file without a comment
curl -X POST "http://localhost:8000/api/v1/datasets/{dataset_id}/upload" \
  -F "file=@data_summary.xlsx"
```

## File Storage

### Physical Storage
- Files are stored in: `{dataset_path}/.metadata/{filename}`
- The `.metadata` folder is created automatically if it doesn't exist
- Filenames are sanitized to prevent security issues
- Duplicate filenames are automatically handled with unique naming

### Metadata Storage
File information is automatically added to the dataset's structural metadata (`dataset_structural.json`) in the `file_descriptions` array:

```json
{
  "file_descriptions": [
    {
      "file_name": "protocol.pdf",
      "role": "uploaded_file",
      "file_path": ".metadata/protocol.pdf",
      "file_description": "Protocol documentation",
      "file_extension": "pdf",
      "file_size_bytes": 245760,
      "file_type_os": "file",
      "file_created_utc": "2024-01-15T10:30:00Z",
      "file_modified_utc": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## File Information Fields

Each uploaded file entry includes:

- **file_name**: The original filename
- **role**: Set to "uploaded_file" to distinguish from other file types
- **file_path**: Relative path from the dataset root
- **file_description**: User-provided comment/description
- **file_extension**: File extension (without the dot)
- **file_size_bytes**: File size in bytes
- **file_type_os**: Always "file" for uploaded files
- **file_created_utc**: Upload timestamp
- **file_modified_utc**: Upload timestamp

## Use Cases

### Documentation Files
- Upload protocol documents, README files, or methodology descriptions
- Add comments explaining the purpose or version of the document

### Supporting Data
- Upload reference files, calibration data, or supplementary datasets
- Use comments to explain the relationship to the main dataset

### Configuration Files
- Upload configuration files, parameter sets, or analysis scripts
- Document the purpose and usage of configuration files

### Quality Control
- Upload QC reports, validation results, or quality metrics
- Track quality assessment files alongside the main data

## Best Practices

### File Naming
- Use descriptive filenames that clearly indicate the file's purpose
- Avoid special characters that might cause issues
- Consider using consistent naming conventions across your project

### Comments
- Always add meaningful descriptions to uploaded files
- Explain the file's purpose, version, or relationship to the dataset
- Include any important usage notes or warnings

### File Organization
- Keep related files together in the same dataset
- Use consistent file types for similar purposes
- Consider file size limits for web uploads

### Security Considerations
- Be aware that uploaded files are stored in the dataset's metadata folder
- Ensure sensitive information is not included in uploaded files
- Review file contents before uploading

## Troubleshooting

### Upload Fails
- Check that the dataset exists and is accessible
- Verify file permissions and disk space
- Ensure the file is not corrupted or locked

### File Not Appearing in Metadata
- Refresh the metadata editor after upload
- Check that the dataset structural metadata exists
- Verify the upload completed successfully

### File Conflicts
- The system automatically handles filename conflicts
- Check the actual filename used if conflicts occurred
- Consider renaming files before upload to avoid conflicts

## API Reference

For detailed API documentation, see the [API Endpoints Reference](../reference/api-endpoints.md#file-upload-endpoints).

## Integration with Other Features

### Metadata Editor
- Uploaded files appear in the dataset structural metadata
- File information can be edited through the metadata editor
- Changes to file descriptions are tracked in metadata

### Dataset Finalization
- Uploaded files are included in the complete metadata when finalizing datasets
- File information is preserved in the V2 metadata structure

### Version Control
- File uploads trigger metadata commits
- Uploaded files are tracked in the version control system
- File changes are logged in the metadata history
