
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

*(Note: A `requirements.txt` file will need to be created for the backend)*

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

*(Note: A `requirements.txt` file will need to be created for the gateway)*

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
2. When you click "Start Session" on the **Frontend**, it sends a request to the gateway.
3. The **Gateway** starts a new **Backend** process on an available port and stores the port in your session.
4. All subsequent API requests from the **Frontend** are sent to the **Gateway**, which then forwards them to your dedicated **Backend** instance.
