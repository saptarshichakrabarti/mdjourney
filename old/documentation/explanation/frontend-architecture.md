# Frontend Architecture Documentation

## Overview

The FAIR Metadata Enrichment Frontend is a modern React-based web application built with TypeScript, providing an intuitive interface for managing and enriching research metadata. The application follows a three-pane layout design optimized for metadata editing workflows.

## Technology Stack

### Core Technologies
- **React 18** - Modern React with concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Material-UI (MUI)** - Component library and theming system
- **Vite** - Fast build tool and development server

### State Management
- **TanStack Query** - Server state management and caching
- **Zustand** - Lightweight client state management
- **React Hook Form** - Form state management and validation

### Development Tools
- **ESLint** - Code linting and quality assurance
- **TypeScript Compiler** - Type checking and compilation
- **Vite Dev Server** - Hot module replacement and fast builds

## Architecture Overview

### Component Hierarchy

```
App
├── ThemeProvider
├── QueryClientProvider
├── LocalizationProvider
├── AppBar (Header)
└── Main Content
    ├── ProjectBrowser (Left Pane)
    ├── MetadataEditor (Center Pane)
    └── ContextPanel (Right Pane)
```

### Three-Pane Layout

The application uses a responsive three-pane layout:

1. **Project Browser (Left Pane - 24%)**
   - Project and dataset navigation
   - Status indicators
   - Auto-refresh functionality

2. **Metadata Editor (Center Pane - Flexible)**
   - Schema-driven form generation
   - Real-time validation
   - Save/load functionality

3. **Context Panel (Right Pane - 22%)**
   - Field help and descriptions
   - Validation error summary
   - Action buttons and progress tracking

## Core Components

### App Component (`src/App.tsx`)

**Purpose**: Main application component and layout orchestrator

**Key Features**:
- Theme management (light/dark mode toggle)
- Error boundary integration
- Responsive layout management
- Provider setup (QueryClient, LocalizationProvider)

**State Management**:
- Theme state via `useAppTheme` hook
- Global error handling via ErrorBoundary

### Project Browser (`src/components/ProjectBrowser.tsx`)

**Purpose**: Project and dataset navigation interface

**Key Features**:
- Hierarchical project/dataset tree view
- Real-time status indicators (V1_Ingested, V2_Finalized)
- Auto-refresh every 5 seconds
- Selection management
- Toast notifications for user feedback

**State Management**:
- Server state via TanStack Query
- Client state via Zustand store
- Local toast notification state

**API Integration**:
- `APIService.getProjects()` - Fetch project list
- `APIService.getProjectDatasets()` - Fetch dataset list
- Automatic refetch on selection changes

### Metadata Editor (`src/components/MetadataEditor.tsx`)

**Purpose**: Primary metadata editing interface

**Key Features**:
- Dynamic form generation from JSON schemas
- Real-time validation with immediate feedback
- Save/load functionality with optimistic updates
- Field status tracking and indicators
- Responsive form layout

**State Management**:
- Form state via React Hook Form
- Server state via TanStack Query
- Validation state via custom hooks

**Schema Integration**:
- Dynamic form field generation
- Type-specific input components
- Validation rule enforcement
- Field help integration

### Schema-Driven Form (`src/components/SchemaDrivenForm.tsx`)

**Purpose**: Dynamic form generation from JSON schemas

**Key Features**:
- Automatic form field generation based on schema properties
- Type-specific input components (text, number, date, select, etc.)
- Nested object and array support
- Conditional field rendering
- Validation integration

**Supported Field Types**:
- `string` - Text input, textarea, email, URL
- `number` - Number input with min/max validation
- `integer` - Integer input with range validation
- `boolean` - Checkbox input
- `array` - Dynamic list with add/remove functionality
- `object` - Nested form sections

### Context Panel (`src/components/ContextPanel.tsx`)

**Purpose**: Contextual information and action interface

**Key Features**:
- Field help and description display
- Validation error summary with field highlighting
- Action buttons (Create Template, Finalize Dataset)
- Progress tracking and status indicators
- Contextual guidance and tips

**Dynamic Content**:
- Field-specific help text
- Validation error details
- Available actions based on current state
- Progress indicators for multi-step processes

### Navigation Panel (`src/components/NavigationPanel.tsx`)

**Purpose**: Form navigation and field jumping

**Key Features**:
- Form section navigation
- Field highlighting and jumping
- Progress indicators
- Quick access to form sections

## Supporting Components

### Error Boundary (`src/components/ErrorBoundary.tsx`)

**Purpose**: Error handling and recovery

**Key Features**:
- Catches JavaScript errors in component tree
- Displays fallback UI for errors
- Error reporting and logging
- Graceful degradation

### Loading Skeleton (`src/components/LoadingSkeleton.tsx`)

**Purpose**: Loading state management

**Key Features**:
- Skeleton loading animations
- Consistent loading states
- Responsive skeleton layouts
- Smooth transitions to content

### Field Status Indicator (`src/components/FieldStatusIndicator.tsx`)

**Purpose**: Field validation status display

**Key Features**:
- Visual status indicators (valid, invalid, pending)
- Color-coded status representation
- Tooltip with detailed error information
- Accessibility support

### Progress Tracker (`src/components/ProgressTracker.tsx`)

**Purpose**: Progress visualization

**Key Features**:
- Multi-step progress indication
- Current step highlighting
- Completion status tracking
- Visual progress representation

## Services Layer

### API Service (`src/services/api.ts`)

**Purpose**: Backend API communication layer

**Key Features**:
- HTTP client configuration with base URL
- Request/response interceptors
- Error handling and transformation
- Type-safe API methods
- Automatic retry logic

**API Methods**:
- `getProjects()` - Fetch all projects
- `getProjectDatasets(projectId)` - Fetch datasets for project
- `getMetadata(datasetId, metadataType)` - Fetch metadata file
- `updateMetadata(datasetId, metadataType, content)` - Save metadata
- `createContextualTemplate(datasetId, schemaId)` - Create experiment template
- `finalizeDataset(datasetId, experimentId?)` - Finalize dataset
- `getContextualSchemas()` - Fetch available contextual schemas
- `getSchema(schemaType, schemaId)` - Fetch specific schema

**Error Handling**:
- HTTP status code handling
- Network error recovery
- User-friendly error messages
- Retry logic for transient failures

## State Management

### Server State (TanStack Query)

**Purpose**: Server data management and caching

**Key Features**:
- Automatic caching and background updates
- Optimistic updates for better UX
- Error handling and retry logic
- Loading state management
- Cache invalidation strategies

**Query Keys**:
- `['projects']` - Project list cache
- `['project-datasets', projectId]` - Dataset list cache
- `['metadata', datasetId, metadataType]` - Metadata cache
- `['schemas', 'contextual']` - Contextual schemas cache

**Cache Configuration**:
- 5-second refetch interval for dynamic data
- Stale-while-revalidate strategy
- Background refetch on window focus
- Automatic retry on failure

### Client State (Zustand)

**Purpose**: Client-side application state

**Key Features**:
- Lightweight state management
- Type-safe state updates
- Persistence for user preferences
- DevTools integration

**State Structure**:
```typescript
interface AppState {
  selectedProjectId: string | null;
  selectedDatasetId: string | null;
  selectedMetadataType: string | null;
  setSelectedProject: (id: string | null) => void;
  setSelectedDataset: (id: string | null) => void;
  setSelectedMetadataType: (type: string | null) => void;
  resetSelection: () => void;
}
```

### Form State (React Hook Form)

**Purpose**: Form state management and validation

**Key Features**:
- Uncontrolled components for performance
- Built-in validation support
- Field-level error handling
- Form submission management

**Validation Integration**:
- Schema-based validation
- Real-time validation feedback
- Custom validation rules
- Error message display

## Custom Hooks

### useAppTheme (`src/hooks/useAppTheme.ts`)

**Purpose**: Theme management hook

**Key Features**:
- Light/dark mode toggle
- Theme persistence
- Material-UI theme integration
- System preference detection

### useFieldStatus (`src/hooks/useFieldStatus.ts`)

**Purpose**: Field validation status hook

**Key Features**:
- Field validation state tracking
- Error message management
- Status indicator updates
- Real-time validation feedback

### useScrollSync (`src/hooks/useScrollSync.ts`)

**Purpose**: Synchronized scrolling hook

**Key Features**:
- Synchronized scrolling between components
- Scroll position management
- Smooth scroll animations
- Performance optimization

## Utilities

### Form Analyzer (`src/utils/formAnalyzer.ts`)

**Purpose**: Form analysis and validation utilities

**Key Features**:
- Form completion analysis
- Validation rule processing
- Field dependency resolution
- Progress calculation

### Schema Utils (`src/utils/schemaUtils.ts`)

**Purpose**: Schema processing utilities

**Key Features**:
- Schema property extraction
- Field type determination
- Validation rule processing
- Schema transformation utilities

## Type Definitions

### API Types (`src/types/api.ts`)

**Purpose**: TypeScript type definitions for API communication

**Key Types**:
- `ProjectSummary` - Project information
- `DatasetSummary` - Dataset information
- `SchemaInfo` - Schema metadata
- `MetadataFile` - Metadata content with schema info
- `MetadataUpdatePayload` - Update request payload
- `ContextualTemplatePayload` - Template creation payload
- `FinalizePayload` - Dataset finalization payload

## Styling and Theming

### Material-UI Integration

**Theme Configuration**:
- Light and dark mode support
- Custom color palette
- Typography scale
- Component theming

**Responsive Design**:
- Mobile-first approach
- Breakpoint management
- Flexible layouts
- Touch-friendly interfaces

### CSS Architecture

**Global Styles** (`src/index.css`):
- CSS reset and normalization
- Global utility classes
- Font loading optimization
- Performance optimizations

**Component Styles**:
- Styled components with Material-UI
- CSS-in-JS approach
- Theme-aware styling
- Responsive design patterns

## Performance Optimization

### Code Splitting

**Lazy Loading**:
- Route-based code splitting
- Component-level lazy loading
- Dynamic imports for heavy components
- Bundle size optimization

### Caching Strategy

**Browser Caching**:
- Static asset caching
- API response caching
- Service worker integration
- Offline support

### Performance Monitoring

**Metrics Tracking**:
- Core Web Vitals monitoring
- Performance API integration
- User interaction tracking
- Error reporting

## Accessibility

### WCAG Compliance

**Accessibility Features**:
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Focus management
- ARIA labels and descriptions

### User Experience

**UX Enhancements**:
- Loading states and skeletons
- Error handling and recovery
- Toast notifications
- Progress indicators
- Responsive design

## Development Workflow

### Build Process

**Development**:
- Vite dev server with HMR
- TypeScript compilation
- ESLint integration
- Hot module replacement

**Production**:
- Optimized bundle generation
- Code minification
- Asset optimization
- Source map generation

### Testing Strategy

**Testing Approach**:
- Component testing with React Testing Library
- Integration testing
- E2E testing with Playwright
- Visual regression testing

## Deployment

### Build Configuration

**Vite Configuration** (`vite.config.ts`):
- Development server setup
- Build optimization
- Proxy configuration for API
- Environment variable handling

### Docker Integration

**Container Configuration**:
- Multi-stage builds
- Nginx serving for production
- Development container with hot reload
- Environment-specific configurations

## Future Enhancements

### Planned Features

**Upcoming Improvements**:
- Advanced form validation
- Bulk operations support
- Export/import functionality
- Advanced search and filtering
- Real-time collaboration

**Technical Improvements**:
- Service worker implementation
- Progressive Web App features
- Advanced caching strategies
- Performance optimizations
- Accessibility enhancements

This architecture provides a solid foundation for a scalable, maintainable, and user-friendly metadata management interface that integrates seamlessly with the FAIR Metadata Automation System backend.