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

export ENDPOINT_ID=l5ipv4uem6n1by

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

### 2. List Files in Workspace
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

### 3. List Files in Network Volume (Persistent Storage)
```bash
curl --request POST \
  --url "https://api.runpod.ai/v2/$ENDPOINT_ID/runsync" \
  --header "accept: application/json" \
  --header "authorization: $RUNPOD_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "input": {
      "action": "list_files",
      "path": "/runpod-volume"
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
- The handler supports **two main actions**: GPU info and file listing
- File listing works with any accessible directory path (`/workspace`, `/runpod-volume`, etc.)
- Models are managed manually on the persistent network volume at `/runpod-volume/`
- Unrecognized actions return detailed error messages with debug information
- Execution timeout is configurable via the deployment workflow (default: 3600 seconds)

## Expected GPU Response Structure

When calling with no action (GPU info), you'll get:
```json
{
  "status": "success",
  "nvidia_smi_output": "full nvidia-smi output...",
  "gpu_details": [
    {
      "gpu_id": 0,
      "name": "NVIDIA RTX A5000",
      "driver_version": "535.104.05",
      "memory_total_mb": "24564",
      "memory_used_mb": "1024", 
      "memory_free_mb": "23540",
      "temperature_c": "45",
      "power_draw_w": "75"
    }
  ],
  "cuda_info": "Cuda compilation tools, release 12.1, V12.1.105",
  "gpu_count": 1,
  "environment": {
    "cuda_visible_devices": "0",
    "runpod_endpoint_id": "Not set"
  },
  "input_received": {}
}
```