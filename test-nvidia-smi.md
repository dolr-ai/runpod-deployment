# RunPod NVIDIA-SMI Testing Guide

## Manual Deployment Steps (Recommended by RunPod)

### 1. Build Image (Automatic via GitHub Actions)
When you push to main, GitHub Actions builds and pushes the image to Google Artifact Registry.

### 2. Create RunPod Endpoint
1. Go to [RunPod Console → Serverless](https://www.runpod.io/console/serverless)
2. Click **"New Endpoint"**
3. Choose **"Custom Image"**
4. Enter image URL: `us-central1-docker.pkg.dev/jay-dhanwant-experiments/talking-head-registry/runpod-nvidia-smi:latest`
5. Configure:
   - **Name**: `nvidia-smi-test`
   - **GPU Type**: Any available (RTX A4000, A40, etc.)
   - **Max Workers**: 1-3
   - **Min Workers**: 0
   - **Container Disk**: 10GB
   - **Worker Timeout**: 300s

### 3. Alternative: GitHub Integration (RunPod Native)
1. **Connect GitHub to RunPod:**
   - RunPod Console → Settings → Connections → GitHub → Connect
   - Authorize repository access

2. **Create Endpoint from GitHub:**
   - New Endpoint → GitHub Repository
   - Select this repository (`runpod-deployment`)
   - Branch: `main`
   - RunPod auto-builds from Dockerfile

## Testing the Endpoint

### Basic Test (No Input Required)
```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

### With Optional Input
```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "nvidia-smi-check"}}'
```

### Async Test
```bash
# Submit job
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'

# Check status (replace JOB_ID)
curl "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID"
```

## Expected Response Structure

```json
{
  "delayTime": 1234,
  "executionTime": 2000,
  "id": "job-uuid-here",
  "status": "COMPLETED",
  "output": {
    "status": "success",
    "nvidia_smi_output": "Wed Sep  2 20:30:00 2024\n+-----------------------------------------------------------------------------+\n| NVIDIA-SMI 525.60.11    Driver Version: 525.60.11    CUDA Version: 12.1     |\n|-------------------------------+----------------------+----------------------+\n| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |\n| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |\n|===============================+======================+======================|\n|   0  NVIDIA RTX A4000    Off  | 00000000:00:05.0 Off |                  Off |\n| 41%   30C    P8    18W / 140W |      1MiB / 16376MiB |      0%      Default |\n+-------------------------------+----------------------+----------------------+",
    "gpu_details": [
      {
        "gpu_id": 0,
        "name": "NVIDIA RTX A4000",
        "driver_version": "525.60.11",
        "memory_total_mb": "16376",
        "memory_used_mb": "1",
        "memory_free_mb": "16375",
        "temperature_c": "30",
        "power_draw_w": "18"
      }
    ],
    "cuda_info": "nvcc: NVIDIA (R) Cuda compiler driver, release 12.1",
    "gpu_count": 1,
    "environment": {
      "cuda_visible_devices": "0",
      "runpod_endpoint_id": "your-endpoint-id"
    }
  }
}
```

## Troubleshooting

### ✅ Success Indicators:
- `"status": "COMPLETED"`
- `nvidia_smi_output` contains GPU table
- `gpu_count > 0`
- `cuda_info` shows CUDA version

### ❌ Common Issues:
- **"No workers available"**: Endpoint still initializing (wait 2-3 min)
- **"FAILED" status**: Check RunPod Logs tab for errors
- **Empty nvidia_smi_output**: GPU not accessible in container
- **Subprocess error**: nvidia-smi command failed

### Debug Commands:
```bash
# Test with verbose output
curl -v -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {"debug": true}}'
```

## Files Structure
```
runpod-deployment/
├── handler.py              # Main serverless handler
├── Dockerfile              # Container definition
├── requirements.txt         # Python dependencies (just runpod)
└── .github/workflows/
    ├── build-image.yml      # Builds and pushes image
    └── deploy-runpod.yml.disabled  # Old broken workflow
```

## Quick Start
1. **Push to main** → GitHub Actions builds image
2. **Create RunPod endpoint** with the image URL from Actions summary
3. **Test** with the curl commands above
4. **Check logs** in RunPod console if issues occur

The handler is designed to be simple and focused - it just runs nvidia-smi and returns GPU information in a structured format.