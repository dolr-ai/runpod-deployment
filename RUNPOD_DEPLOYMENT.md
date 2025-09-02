# RunPod Deployment Log

## Overview
This document tracks our journey to deploy a simple NVIDIA-SMI endpoint on RunPod Serverless, following official documentation step by step.

**Goal**: Create a working RunPod serverless endpoint that returns `nvidia-smi` output to verify GPU access.

---

## Attempt 1: Complex Setup with FastAPI + Load Balancing (FAILED)
**Date**: Sept 2, 2024  
**Approach**: Tried to create a hybrid FastAPI + RunPod serverless handler

### What We Tried:
- Created `main.py` with both FastAPI endpoints and RunPod handler
- Mixed Load Balancing and Queue-based patterns in same file
- Complex GitHub Actions workflow with GraphQL API calls
- Template creation with `saveTemplate` mutations

### Issues Encountered:
1. **GraphQL API Errors**: 
   - `Cannot query field "serverlessEndpoints" on type "Query"`
   - Should use `{ myself { endpoints { id name } } }`

2. **Template Creation Failures**:
   - Missing required fields: `dockerArgs`, `volumeInGb`
   - Template name uniqueness conflicts

3. **Worker Quota Issues**:
   - Hit 5-worker quota limit
   - `Max workers across all endpoints must not exceed your workers quota (5)`

4. **Endpoint Type Confusion**:
   - Created Load Balancing endpoint but code was Queue-based
   - Mixed `/ping`, `/health` (Load Balancing) with `/runsync` (Queue-based)

### What Didn't Work:
- ❌ Complex GitHub Actions with direct RunPod API calls
- ❌ Mixing FastAPI with RunPod serverless handler
- ❌ Load Balancing endpoints with Queue-based code
- ❌ Template management via GraphQL mutations
- ❌ Multiple endpoints created due to naming conflicts

### Lessons Learned:
1. RunPod has two distinct endpoint types: **Queue-based** vs **Load Balancing**
2. Don't mix FastAPI patterns with RunPod serverless handlers
3. GraphQL API has specific field names and required parameters
4. Template names must be unique across account
5. Worker quotas are shared across all endpoints

---

## Attempt 2: Official Documentation Approach (IN PROGRESS)
**Date**: Sept 2, 2024  
**Approach**: Following RunPod official documentation step by step

### References Used:
1. https://docs.runpod.io/serverless/workers/overview
2. https://docs.runpod.io/serverless/workers/custom-worker  
3. https://docs.runpod.io/serverless/workers/handler-functions
4. https://docs.runpod.io/serverless/workers/concurrent-handler
5. https://docs.runpod.io/serverless/workers/deploy
6. https://docs.runpod.io/serverless/workers/github-integration

### Current Setup:

#### 1. Simple Handler Function ✅
**File**: `handler.py`
```python
import runpod
import subprocess

def handler(job):
    try:
        result = subprocess.check_output(['nvidia-smi'], text=True)
        return {"gpu_info": result}
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
```

**Key Points from Documentation**:
- Handler takes `job` parameter
- Access input via `job["input"]` 
- Use `runpod.serverless.start()` to launch
- Handle errors gracefully
- Initialize heavy resources outside handler

#### 2. Simplified Container ✅
**File**: `Dockerfile`
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY handler.py .
CMD ["python", "-u", "handler.py"]
```

**File**: `requirements.txt`
```
runpod>=1.6.2
```

#### 3. Build-Only GitHub Workflow ✅
**File**: `.github/workflows/build-image.yml`
- Only builds and pushes Docker image to Google Artifact Registry
- Provides deployment instructions in GitHub Actions summary
- **No automatic RunPod API calls** (following documentation recommendation)

#### 4. Manual Deployment Process (PENDING)
**Per RunPod Documentation**:
1. **Build image** via GitHub Actions ✅
2. **Connect GitHub to RunPod** (Console → Settings → Connections → GitHub)
3. **Create endpoint** via RunPod Console (not API)
4. **Select repository and branch** for auto-deployment
5. **Create GitHub release** to trigger updates

### What We're Doing Right:
- ✅ Following official documentation patterns
- ✅ Simple, focused handler function
- ✅ Minimal dependencies
- ✅ Using RunPod's preferred GitHub integration
- ✅ Avoiding complex GraphQL API management

### Progress Update:
1. ✅ **Push code to trigger image build** - COMPLETED
   - GitHub Actions ran successfully
   - ❌ GitHub Actions output had incorrect SHA hash
   - ✅ **Actual built image**: `us-central1-docker.pkg.dev/jay-dhanwant-experiments/talking-head-registry/runpod-nvidia-smi:bd65ba12e2b2`
   - ❌ **Incorrect hash in Actions**: `8ff246d6b3354238e8c562f595c8c01bb2ca735`
   
   **Issue**: RunPod couldn't pull image due to typo in SHA hash from GitHub Actions summary
   
2. ✅ **Manual endpoint creation** - COMPLETED (using correct image URL)
3. **Test nvidia-smi endpoint** - IN PROGRESS

### **New Discovery: Official CI/CD Support**
**Reference**: https://www.runpod.io/articles/guides/integrating-runpod-with-ci-cd-pipelines

RunPod **DOES support API-based CI/CD automation**! Our initial approach wasn't wrong, just poorly executed.

**Key Insights from Official Guide**:
- ✅ **API integration is recommended** for CI/CD pipelines
- ✅ **GitHub Actions workflows** are explicitly mentioned
- ✅ **Automated deployment** is the intended use case
- ✅ **REST API calls** can manage serverless endpoints

**Recommended CI/CD Flow**:
1. Build/push Docker image ✅
2. Send API request to RunPod to launch pod or update serverless endpoint ✅
3. Automated testing before deployment ✅
4. Handle authentication securely ✅

## Attempt 3: Full Automated CI/CD (IMPLEMENTED)
**Date**: Sept 2, 2024  
**Approach**: Complete automation using RunPod GraphQL API

### What We Built:
**File**: `.github/workflows/deploy-runpod.yml`

#### Workflow Steps:
1. **Build & Push Image** → Google Artifact Registry
2. **Create Template** → RunPod GraphQL `saveTemplate` mutation
3. **Create/Update Endpoint** → RunPod GraphQL `saveEndpoint` mutation  
4. **Test Endpoint** → Automated `runsync` API call
5. **Generate Summary** → GitHub Actions summary with test commands

#### Key Features:
- ✅ **Template Management**: Creates unique templates with timestamps
- ✅ **Endpoint Management**: Creates new or updates existing endpoints
- ✅ **Error Handling**: Validates API responses, fails on errors
- ✅ **Automated Testing**: Tests endpoint after deployment
- ✅ **Environment Support**: Production/staging/development environments
- ✅ **GPU Configuration**: Configurable GPU types via workflow inputs

#### Secrets Required:
- `GCP_CREDENTIALS` - Google Cloud service account JSON
- `RUNPOD_API_KEY` - RunPod API key

### Expected Workflow Result:
```
✅ Docker image built and pushed
✅ RunPod template created: nvidia-smi-prod-1693689600  
✅ RunPod endpoint created/updated: nvidia-smi-prod
✅ Endpoint tested successfully
📊 GitHub Actions summary with test commands and dashboard links
```

### Expected Test:
```bash
curl -X POST "https://api.runpod.ai/v2/ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{"input": {}}'
```

**Expected Response**:
```json
{
  "status": "COMPLETED",
  "output": {
    "gpu_info": "nvidia-smi output here..."
  }
}
```

---

## Key Learnings So Far:

### ✅ Do's:
1. **Follow official documentation** - don't invent your own patterns
2. **Keep handlers simple** - one function, clear purpose
3. **Use RunPod Console** for endpoint creation and management
4. **GitHub integration** is preferred over API automation
5. **Test locally first** with simple docker run
6. **Minimal dependencies** - only what you need

### ❌ Don'ts:
1. **Mix frameworks** - don't combine FastAPI with RunPod handlers
2. **Complex GraphQL API calls** - use Console instead
3. **Multiple deployment methods** - pick one approach
4. **Ignore worker quotas** - monitor your limits
5. **Create duplicate endpoints** - clean up old ones
6. **Over-engineer** - start simple, add complexity later

### 🔧 RunPod Specific Gotchas:
1. **Queue-based vs Load Balancing** are fundamentally different
2. **Template names must be unique** across your account
3. **Worker quotas are shared** across all endpoints  
4. **GitHub releases** trigger automatic updates (not pushes)
5. **Image build timeout** is 160 minutes max
6. **Container size limit** is 80GB

---

*This document will be updated as we progress through the deployment...*