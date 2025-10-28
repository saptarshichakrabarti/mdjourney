# FAIR Metadata Enrichment GUI

A modern React-based web interface for the FAIR Metadata Enrichment Tool, providing an intuitive way to manage and enrich research metadata.

## Features

- **Three-Pane Layout**: Project browser, metadata editor, and context panel
- **Schema-Driven Forms**: Dynamically generated forms based on JSON schemas
- **Real-time Validation**: Client-side validation with immediate feedback
- **Contextual Templates**: Create experiment-specific metadata templates
- **Dataset Finalization**: Generate V2 complete metadata files
- **Schema Resolution**: Support for local overrides and packaged defaults

## Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **TanStack Query** for server state management
- **React Hook Form** with Zod validation
- **Zustand** for client state management
- **Vite** for fast development and building

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- The FAIR Metadata API server running on `http://localhost:8000`

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Usage

1. **Project Browser (Left Pane)**: Navigate through projects and datasets
2. **Metadata Editor (Center Pane)**: Edit metadata using schema-driven forms
3. **Context Panel (Right Pane)**: View field help, validation errors, and perform actions

### Workflows

#### Editing Project Metadata
1. Select a project from the browser
2. Choose "Project Descriptive" from the metadata type dropdown
3. Edit fields and save changes

#### Creating Contextual Metadata
1. Select a dataset in V1 status
2. Use the context panel to create a contextual template
3. Choose an experiment type (e.g., "Genomics Sequencing")
4. Fill in the contextual metadata
5. Finalize the dataset to generate V2 metadata

## Development

### Project Structure

```
src/
├── components/          # React components
│   ├── ProjectBrowser.tsx
│   ├── MetadataEditor.tsx
│   ├── SchemaDrivenForm.tsx
│   └── ContextPanel.tsx
├── services/           # API service layer
│   └── api.ts
├── store/              # State management
│   └── appStore.ts
├── types/              # TypeScript type definitions
│   └── api.ts
├── utils/              # Utility functions
│   └── schemaUtils.ts
└── App.tsx             # Main application component
```

### Key Components

- **ProjectBrowser**: Displays project/dataset tree with status indicators
- **MetadataEditor**: Manages form state and API interactions
- **SchemaDrivenForm**: Renders dynamic forms based on JSON schemas
- **ContextPanel**: Shows field help, validation, and action buttons

### State Management

- **TanStack Query**: Server state (projects, datasets, metadata)
- **Zustand**: Client state (selected items, UI state)
- **React Hook Form**: Form state and validation

## API Integration

The frontend communicates with the FastAPI backend through the `APIService` class, which provides:

- Project and dataset discovery
- Metadata CRUD operations
- Schema resolution and validation
- Contextual template creation
- Dataset finalization

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Use the established component structure
4. Test with the API server running locally

## License

This project is part of the FAIR Metadata Automation System.
