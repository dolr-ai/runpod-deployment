# RunPod Serverless Deployment

Production-ready CI/CD pipeline for RunPod serverless GPU workloads with automated deployment and persistent storage.

## Features

- 🐳 **Automated Docker builds** to Google Artifact Registry
- 💾 **100GB persistent network volume** for model storage
- 🔧 **Template and endpoint** lifecycle management
- 🔐 **Runtime environment variables** (secrets injection)
- 🧪 **Automated testing** and deployment verification
- 📊 **GPU monitoring** via nvidia-smi with detailed metrics

## Architecture

### Storage Architecture
- **Container Disk**: 20GB temporary
- **Local Volume**: 100GB at `/workspace` (temporary persistent)
- **Network Volume**: 100GB at `/runpod-volume` (persistent across deployments)

### Handler Functions
The deployed endpoint (`handler.py`) supports:

1. **GPU Information** (default) - Returns nvidia-smi output, GPU details, CUDA info, environment variables
2. **File Listing** (`list_files` action) - Lists files/directories in any specified path

```python
# GPU info (no action specified)
{"input": {}}

# List network volume models
{"input": {"action": "list_files", "path": "/runpod-volume"}}

# List any directory
{"input": {"action": "list_files", "path": "/workspace"}}
```

## Quick Start

### Prerequisites
1. **RunPod Account** with API key
2. **Google Cloud Project** with Artifact Registry enabled
3. **GitHub Repository** with required secrets configured

### Required GitHub Secrets
```bash
GCP_CREDENTIALS    # Google Cloud service account JSON
RUNPOD_API_KEY     # RunPod API key
```

### Additional Requirements for Model Management
Since the handler doesn't include model downloading functionality, you'll need RunPod S3 credentials to manage models on the network volume:

```bash
# For RunPod S3 operations (configure with aws configure)
AWS_ACCESS_KEY_ID     # RunPod S3 access key
AWS_SECRET_ACCESS_KEY # RunPod S3 secret key
AWS_DEFAULT_REGION=us-ks-2  # Your RunPod datacenter region
```

**RunPod S3 Configuration:**
- **Endpoint**: `https://s3api-us-ks-2.runpod.io`
- **Bucket**: Your network volume ID (e.g., `mjjt5bmlew`)
- **Region**: Matches your datacenter selection (`us-ks-2`)

**Note**: Models must be uploaded/downloaded manually using `aws cli` with RunPod's S3-compatible endpoints.

### Deployment Options
The workflow supports multiple deployment configurations:

| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `environment` | `production` | production, staging, development | Deployment environment |
| `gpu_type` | `NVIDIA RTX A5000` | A5000, RTX 4090, A40, RTX A4000, RTX 3090 | GPU type to use |
| `datacenter` | `US-KS-2` | US-KS-2, US-GA-1, CA-MTL-3, EU-RO-1, etc. | RunPod datacenter |
| `execution_timeout` | `600` | 600s to 86400s | Maximum execution time |

## Workflow Details

### Step 1: Docker Image Build
- Builds multi-platform Docker image (`linux/amd64`)
- Tags with both `latest` and commit SHA
- Pushes to Google Artifact Registry
- Configures private registry authentication

### Step 2: Network Volume Management
- Searches for existing volume by name: `model-storage-{environment}`
- Creates new 100GB volume if none exists
- Reuses existing volume to preserve data
- Configurable datacenter placement

### Step 3: Template Management
- Creates reusable template: `nvidia-smi-{environment}`
- **Updates existing template** instead of creating duplicates
- Injects environment variables (including secrets)
- Configures storage: 20GB container + 100GB local volume

### Step 4: Endpoint Management
- Creates/updates serverless endpoint: `nvidia-smi-{environment}`
- Attaches network volume for persistent storage
- Configures auto-scaling: 0-2 workers with queue-based scaling
- Sets execution timeout and idle timeout

### Step 5: Testing & Verification
- Waits 30 seconds for endpoint initialization
- Runs automated test with sample request
- Validates response structure
- Reports test results in deployment summary

## API Usage

### GPU Information (Default)
```bash
curl -X POST "https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

### File Listing
```bash
# List network volume (models)
curl -X POST "https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"action": "list_files", "path": "/runpod-volume"}}'

# List any directory (workspace, root, etc.)
curl -X POST "https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"action": "list_files", "path": "/workspace"}}'
```

## Storage Management

### Network Volume Benefits
- **Persistent**: Survives endpoint restarts and updates
- **Shared**: Can be attached to multiple endpoints
- **Cost-effective**: Reused across deployments
- **Large capacity**: 100GB for model storage

### File Organization
```
/runpod-volume/           # Persistent storage (survives deployments)
├── models/              # ML models - dwpose, musetalk, face-parse-bisent, whisper
├── datasets/            # Training data
└── .cache/              # Dependencies

/workspace/              # Temporary storage (survives restarts only)
├── temp/                # Processing files
└── outputs/             # Generated content
```

**Note**: `/workspace` is the default path for `list_files` but any directory can be listed.

### Model Management with RunPod S3

Since model downloading was removed from the handler, use RunPod's S3-compatible API directly:

```bash
# Upload models to RunPod S3 (from local machine)
aws s3 cp --recursive models/ s3://mjjt5bmlew/models/ \
  --region us-ks-2 \
  --endpoint-url https://s3api-us-ks-2.runpod.io

# List models in RunPod S3 bucket
aws s3 ls --recursive s3://mjjt5bmlew/models/ \
  --region us-ks-2 \
  --endpoint-url https://s3api-us-ks-2.runpod.io \
  --cli-read-timeout 0 \
  --cli-connect-timeout 60

# Download models to network volume (run inside RunPod container)
aws s3 sync s3://mjjt5bmlew/models/ /runpod-volume/models/ \
  --region us-ks-2 \
  --endpoint-url https://s3api-us-ks-2.runpod.io

# Remove models from S3 bucket
aws s3 rm --recursive s3://mjjt5bmlew/models/old-model/ \
  --region us-ks-2 \
  --endpoint-url https://s3api-us-ks-2.runpod.io
```

**Key Points:**
- **Endpoint URL**: `https://s3api-us-ks-2.runpod.io` (matches your datacenter)
- **Region**: `us-ks-2` (matches your RunPod datacenter selection)
- **Bucket ID**: `mjjt5bmlew` (your network volume ID)
- **Timeouts**: Extended for large model files

## Deployment Triggers

### Automatic Deployment
```bash
git push origin main  # Triggers deployment to production
```

### Manual Deployment
1. Go to **Actions** tab in GitHub
2. Select **Deploy NVIDIA-SMI to RunPod Serverless**
3. Click **Run workflow**
4. Choose environment, GPU type, and other options
5. Click **Run workflow**

## Monitoring & Management

### GitHub Actions Summary
After each deployment, you'll get a detailed summary with:
- ✅ Deployment status and configuration
- 🔧 Endpoint ID and template information
- 💾 Storage configuration details
- 🧪 Test commands for immediate verification
- 📊 Links to RunPod dashboard

### RunPod Console
- **Endpoint Dashboard**: `https://www.runpod.io/console/serverless/{ENDPOINT_ID}`
- **All Endpoints**: `https://www.runpod.io/console/serverless`
- **Network Volumes**: `https://www.runpod.io/console/user/storage`

## Advanced Configuration

### Custom Docker Image
Modify the following in the workflow:
```yaml
env:
  GAR_LOCATION: us-central1
  GAR_REPOSITORY: your-registry-name
  PROJECT_ID: your-gcp-project
  IMAGE_NAME: your-image-name
```

### Storage Sizes
Adjust storage allocation in the workflow:
```yaml
VOLUME_SIZE=100          # Network volume (GB)
LOCAL_VOLUME_SIZE=100    # Local volume (GB)
CONTAINER_DISK_SIZE=20   # Container disk (GB)
```

### Template Environment Variables
Environment variables are injected into the template:
```yaml
env:
  CUDA_VISIBLE_DEVICES: "0"
  PYTHONUNBUFFERED: "1"
  GCP_CREDENTIALS: # From GitHub secrets
  RUNPOD_API_KEY: # From GitHub secrets
```

## Troubleshooting

### Common Issues

**1. Template Update Failures**
- Check if template name conflicts exist
- Verify container registry authentication
- Ensure image is accessible from RunPod

**2. Network Volume Attachment**
- Volume must be in same datacenter as endpoint
- Check volume quotas in RunPod console
- Verify volume exists and is active

**3. Secret Access Issues**
- Ensure GitHub secrets are properly configured
- Check secret names match exactly: `GCP_CREDENTIALS`, `RUNPOD_API_KEY`
- Verify JSON format for GCP credentials

**4. Model Management Issues**
- Models are not automatically downloaded - use S3 tools directly
- Ensure S3 credentials are configured for model uploads/downloads
- Network volume persists across deployments - check `/runpod-volume/models/`

**5. Endpoint Scaling Issues**
- Check worker quotas in RunPod account
- Adjust `workersMax` if hitting limits
- Monitor scaling metrics in console

### Deployment Logs
Check GitHub Actions logs for detailed information:
1. Go to **Actions** tab
2. Select latest workflow run
3. Expand failed steps to see error details
4. Look for specific error messages in logs

## Cost Optimization

### Scaling Configuration
- **Workers Min**: 0 (scales to zero when idle)
- **Workers Max**: 2 (limits concurrent instances)
- **Idle Timeout**: 5 seconds (quick scale-down)
- **Scaler Type**: Queue-based (efficient for serverless)

### Storage Efficiency
- Use network volume for persistent data only
- Store temporary files in local volume or container disk
- Clean up unused models and datasets regularly

### Resource Selection
- Choose appropriate GPU type for workload
- Select datacenter close to data sources
- Adjust execution timeout based on actual needs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test deployment in development environment
5. Submit a pull request