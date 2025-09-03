# RunPod Serverless Endpoint Test Commands

This document contains the correct curl commands for testing RunPod serverless endpoints based on the official documentation.

## Base URL Format
```
https://api.runpod.ai/v2/[ENDPOINT_ID]/runsync
```

## Authentication
All requests require your RunPod API key in the authorization header:
```
authorization: $RUNPOD_API_KEY
```

## Test Commands

### 1. Basic GPU Information Test
```bash
curl --request POST \
  --url "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync" \
  --header "accept: application/json" \
  --header "authorization: $RUNPOD_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "input": {}
  }'
```

### 2. Download Models from GCS
```bash
curl --request POST \
  --url "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync" \
  --header "accept: application/json" \
  --header "authorization: $RUNPOD_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "input": {
      "action": "download_models"
    }
  }'
```

### 3. List Files in Workspace
```bash
curl --request POST \
  --url "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync" \
  --header "accept: application/json" \
  --header "authorization: $RUNPOD_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "input": {
      "action": "list_files",
      "path": "/workspace"
    }
  }'
```

### 4. List Files in Models Directory
```bash
curl --request POST \
  --url "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync" \
  --header "accept: application/json" \
  --header "authorization: $RUNPOD_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "input": {
      "action": "list_files",
      "path": "/runpod-volume/models"
    }
  }'
```

## Usage Instructions

1. Replace `$ENDPOINT_ID` with your actual RunPod endpoint ID
2. Replace `$RUNPOD_API_KEY` with your RunPod API key
3. Use `/runsync` for synchronous requests (wait for immediate results)
4. Use `/run` for asynchronous requests (returns job ID for later polling)

## Handler Actions Supported

| Action | Description | Required Parameters |
|--------|-------------|-------------------|
| (none) | Get GPU information via nvidia-smi | None |
| `download_models` | Download models from GCS bucket | None (uses env vars) |
| `list_files` | List files in specified directory | `path` (optional, defaults to "/workspace") |

## Response Format

All endpoints return JSON with the following structure:
```json
{
  "status": "success" | "error",
  "data": {...},
  "error": "error message if status is error"
}
```

## Notes

- All requests must include an `input` object in the request body
- The handler supports three main actions: GPU info, model download, and file listing
- Model downloads use GCP credentials from environment variables
- File listing works with any accessible directory path
- Execution timeout is configurable via the deployment workflow (default: 3600 seconds)