import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';

interface FileUploadDialogProps {
  open: boolean;
  selectedFile: File | null;
  uploadComment: string;
  uploading: boolean;
  onClose: () => void;
  onUpload: (file: File, comment: string) => void;
  onFileChange: (file: File) => void;
  onCommentChange: (comment: string) => void;
}

export const FileUploadDialog: React.FC<FileUploadDialogProps> = ({
  open,
  selectedFile,
  uploadComment,
  uploading,
  onClose,
  onUpload,
  onFileChange,
  onCommentChange,
}) => {
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileChange(file);
    }
  };

  const handleUploadConfirm = () => {
    if (selectedFile) {
      onUpload(selectedFile, uploadComment);
    }
  };

  const handleUploadCancel = () => {
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleUploadCancel} maxWidth="sm" fullWidth>
      <DialogTitle>Upload File</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 1 }}>
          {/* File Input */}
          <Box sx={{ mb: 2 }}>
            <input
              type="file"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="file-upload-input"
            />
            <label htmlFor="file-upload-input">
              <Button variant="outlined" component="span" fullWidth>
                Choose File
              </Button>
            </label>
          </Box>

          {selectedFile && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Selected file:
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                {selectedFile.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Size: {(selectedFile.size / 1024).toFixed(1)} KB
              </Typography>
            </Box>
          )}
          
          <TextField
            fullWidth
            label="File Description (Optional)"
            placeholder="Describe what this file contains or its purpose..."
            multiline
            rows={3}
            value={uploadComment}
            onChange={(e) => onCommentChange(e.target.value)}
            sx={{ mt: 1 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            This file and description will be added to the dataset's structural metadata under "File Descriptions".
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleUploadCancel} disabled={uploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUploadConfirm}
          variant="contained"
          disabled={uploading || !selectedFile}
          startIcon={<UploadIcon />}
        >
          {uploading ? 'Uploading...' : 'Upload File'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

