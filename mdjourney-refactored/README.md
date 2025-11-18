# MDJourney Refactored - Local Development Guide

This guide provides instructions for setting up and running the refactored MDJourney application on a local machine.

## Prerequisites

- Node.js and npm
- Python 3.7+ and pip

## Installation

### 1. Backend

```bash
cd mdjourney-backend
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd mdjourney-webapp
npm install
```

### 3. Gateway

```bash
cd mdjourney-gateway
pip install -r requirements.txt
```

## Configuration

Before starting the application, you need to create a `sample-config.yaml` file in the root of the `mdjourney-refactored` directory. You can use the provided `sample-config.yaml` as a starting point.

```yaml
# Sample configuration for MDJourney development and testing.

# Directory to monitor for new or modified files.
# Use a relative path for easy local testing.
watchDirectory: './test-data/files-to-watch'

# Directory containing custom Jinja2 templates for rendering.
templateDirectory: './test-data/templates'

# A list of glob patterns to determine which files to monitor.
# This is highly flexible.
# Example 1: Monitor everything: ['*']
# Example 2: Monitor only markdown and text files: ['*.md', '*.txt']
watchPatterns:
  - '*'

# A simple key-value schema for expected metadata.
metadataSchema:
  author: string
  version: number
  status: ['draft', 'published', 'archived']
```

Also, make sure the directories specified in your `sample-config.yaml` exist. For the sample configuration, you can create them with:

```bash
mkdir -p mdjourney-refactored/test-data/files-to-watch mdjourney-refactored/test-data/templates
```

## Running the Application

1. **Start the Gateway:**

   ```bash
   cd mdjourney-gateway
   python main.py
   ```

   The gateway will start on `http://localhost:8000`.

2. **Start the Frontend:**

   ```bash
   cd mdjourney-webapp
   npm start
   ```

   The frontend development server will start on `http://localhost:3000`.

## How it Works

1. The **Gateway** is the central entry point for the application. It manages user sessions and reverse proxies requests to the appropriate backend instance.
2. When you open the **Frontend**, you will be prompted to select a configuration file. Select the `sample-config.yaml` file you created.
3. When you click "Start Session", the **Frontend** parses the YAML file and sends the configuration as JSON to the gateway.
4. The **Gateway** saves the configuration to a temporary file, starts a new **Backend** process on an available port (passing the path to the config file), and stores the port in your session.
5. All subsequent API requests from the **Frontend** are sent to the **Gateway**, which then forwards them to your dedicated **Backend** instance.
