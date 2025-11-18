import React from 'react';
import { Box, Skeleton } from '@mui/material';

interface LoadingSkeletonProps {
  variant?: 'form' | 'navigation' | 'progress';
  lines?: number;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  variant = 'form',
  lines = 5
}) => {
  const renderFormSkeleton = () => (
    <Box sx={{ p: 3 }}>
      {/* Header skeleton */}
      <Skeleton
        variant="text"
        width="60%"
        height={40}
        sx={{ mb: 3 }}
      />

      {/* Form sections skeleton */}
      {Array.from({ length: 3 }).map((_, sectionIndex) => (
        <Box
          key={sectionIndex}
          sx={{
            mb: 4,
            p: 3,
            border: '1px solid var(--fair-border-light)',
            borderRadius: 'var(--fair-radius-lg)',
            backgroundColor: 'var(--fair-surface)'
          }}
        >
          {/* Section title */}
          <Skeleton
            variant="text"
            width="40%"
            height={32}
            sx={{ mb: 2 }}
          />

          {/* Form fields */}
          {Array.from({ length: lines }).map((_, fieldIndex) => (
            <Box key={fieldIndex} sx={{ mb: 2 }}>
              <Skeleton
                variant="text"
                width="30%"
                height={20}
                sx={{ mb: 1 }}
              />
              <Skeleton
                variant="rounded"
                width="100%"
                height={56}
                sx={{ borderRadius: 'var(--fair-radius-md)' }}
              />
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );

  const renderNavigationSkeleton = () => (
    <Box sx={{ p: 3 }}>
      {/* Navigation header */}
      <Skeleton
        variant="text"
        width="70%"
        height={32}
        sx={{ mb: 3 }}
      />

      {/* Navigation sections */}
      {Array.from({ length: 5 }).map((_, index) => (
        <Box key={index} sx={{ mb: 3 }}>
          <Skeleton
            variant="rounded"
            width="100%"
            height={48}
            sx={{
              mb: 1,
              borderRadius: 'var(--fair-radius-md)'
            }}
          />
          <Skeleton
            variant="rounded"
            width="100%"
            height={6}
            sx={{
              mb: 2,
              borderRadius: 3
            }}
          />
        </Box>
      ))}
    </Box>
  );

  const renderProgressSkeleton = () => (
    <Box sx={{
      p: 3,
      backgroundColor: 'var(--fair-surface)',
      border: '1px solid var(--fair-border-light)',
      borderRadius: 'var(--fair-radius-lg)',
      mb: 3
    }}>
      <Skeleton
        variant="text"
        width="50%"
        height={32}
        sx={{ mb: 2 }}
      />

      {/* Progress bars */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Skeleton variant="text" width="40%" height={16} />
          <Skeleton variant="text" width="15%" height={16} />
        </Box>
        <Skeleton
          variant="rounded"
          width="100%"
          height={8}
          sx={{ borderRadius: 4 }}
        />
      </Box>

      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Skeleton variant="text" width="35%" height={16} />
          <Skeleton variant="text" width="20%" height={16} />
        </Box>
        <Skeleton
          variant="rounded"
          width="100%"
          height={6}
          sx={{ borderRadius: 3 }}
        />
      </Box>

      {/* Status chips */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Skeleton variant="rounded" width={80} height={24} sx={{ borderRadius: 12 }} />
        <Skeleton variant="rounded" width={70} height={24} sx={{ borderRadius: 12 }} />
        <Skeleton variant="rounded" width={60} height={24} sx={{ borderRadius: 12 }} />
      </Box>

      <Skeleton variant="text" width="80%" height={16} sx={{ mx: 'auto' }} />
    </Box>
  );

  switch (variant) {
    case 'navigation':
      return renderNavigationSkeleton();
    case 'progress':
      return renderProgressSkeleton();
    case 'form':
    default:
      return renderFormSkeleton();
  }
};

export default LoadingSkeleton;