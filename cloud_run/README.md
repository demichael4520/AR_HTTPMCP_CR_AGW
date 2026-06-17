# MCP Weather Server

This is a Model Context Protocol (MCP) server that provides weather information for a given location. It exposes an SSE (Server-Sent Events) endpoint.

## Prerequisites

- Python 3.13 or later

## Setup

1.  **Create a virtual environment**:
    ```bash
    python3 -m venv venv
    ```

2.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running Locally

To start the server locally, run:

```bash
python main.py
```

The server will start on `http://0.0.0.0:8080`. The SSE endpoint will be at `http://localhost:8080/sse`.

## Deployment to Cloud Run

This project includes a `Dockerfile` and can be easily deployed to Google Cloud Run.

To deploy using source code:

```bash
gcloud run deploy mcp-weather-server --source . --region=us-central1 --allow-unauthenticated
```
*Note: Adjust the region and authentication settings as needed.*
