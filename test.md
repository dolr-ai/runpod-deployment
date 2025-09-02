# RunPod GPU Test Endpoint Testing Guide

Your RunPod endpoint is deployed at: `https://api.runpod.ai/v2/8ed127agbn8h3h`

**Note**: This is a **Queue-based endpoint**, not Load Balancing, so it uses `/runsync` and `/run` endpoints.

## Queue-Based API Tests

### 1. Test synchronous request (Main GPU test)
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}'
```

### 2. Test with custom tokens
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [10, 20, 30, 40, 50, 60, 70, 80]}}'
```

### 3. Test asynchronous request (returns job ID)
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/run" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}'
```

### 4. Check job status (replace JOB_ID with returned ID)
```bash
curl -X GET "https://api.runpod.ai/v2/8ed127agbn8h3h/status/JOB_ID" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "success",
  "gpu_info": {
    "pytorch_version": "2.1.0+cu121",
    "cuda_available": true,
    "device_count": 1,
    "devices": [
      {
        "id": 0,
        "name": "NVIDIA A40",
        "memory_gb": 45.0
      }
    ]
  },
  "inference_result": {
    "prediction": 0,
    "confidence": 0.5123,
    "device_used": "cuda:0"
  },
  "gpu_memory": {
    "allocated_mb": 52.3,
    "reserved_mb": 100.0,
    "max_allocated_mb": 52.3
  },
  "input_tokens": [1, 2, 3, 4, 5],
  "message": "GPU test completed successfully!"
}
```

## Debugging Commands

### 5. Test with verbose output
```bash
curl -v -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}'
```

### 6. Test with timeout
```bash
curl --connect-timeout 30 --max-time 120 \
  -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}'
```

### 7. Test async job with polling
```bash
# Submit async job
JOB_ID=$(curl -s -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/run" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}' | jq -r '.id')

echo "Job ID: $JOB_ID"

# Poll for results
curl -X GET "https://api.runpod.ai/v2/8ed127agbn8h3h/status/$JOB_ID"
```

## Error Scenarios to Test

### 8. Test with invalid JSON
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'
```

### 9. Test with empty input
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

### 10. Test with missing input wrapper
```bash
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"tokens": [1, 2, 3]}'
```

## Success Indicators

✅ **Healthy Queue-based Endpoint:**
- `/runsync` returns output with `"cuda_available": true`
- Response includes GPU info and inference results
- Async `/run` returns job ID, `/status` shows COMPLETED

✅ **Expected Response Structure:**
```json
{
  "delayTime": 1234,
  "executionTime": 2345,
  "id": "job-id-here",
  "output": {
    "status": "success",
    "gpu_info": {"cuda_available": true, "device_count": 1},
    "inference_result": {"device_used": "cuda:0"},
    "message": "GPU test completed successfully!"
  },
  "status": "COMPLETED"
}
```

❌ **Common Issues:**
- **No workers available**: Endpoint initializing (wait 2-3 minutes)
- **IN_QUEUE status**: Request waiting for available worker
- **FAILED status**: Check logs for container errors
- **Timeout**: Container taking too long (check Worker timeout settings)
- **Empty output**: Handler function not returning properly

## Queue-based API Workflow

1. **Synchronous** (`/runsync`): Submit → Wait → Get result immediately
2. **Asynchronous** (`/run`): Submit → Get job ID → Poll `/status/{job_id}` → Get result
3. **Job Status**: `IN_QUEUE` → `IN_PROGRESS` → `COMPLETED`/`FAILED`

## Next Steps After Testing

1. **If `/runsync` works**: Your GPU test endpoint is working correctly!
2. **If jobs stay IN_QUEUE**: Check worker status in dashboard (may be initializing)
3. **If FAILED status**: Check RunPod dashboard → Logs tab for container errors
4. **For debugging**: Use the verbose curl commands and async polling above

## RunPod Dashboard Links
- **Endpoint Dashboard**: https://www.runpod.io/console/serverless/8ed127agbn8h3h
- **Logs**: Click your endpoint → Logs tab  
- **Workers**: Click your endpoint → Workers tab
- **Metrics**: Click your endpoint → Metrics tab

## Quick Start Test
```bash
# Test the endpoint (wait for workers to initialize first)
curl -X POST "https://api.runpod.ai/v2/8ed127agbn8h3h/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"tokens": [1, 2, 3, 4, 5]}}'
```