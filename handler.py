"""
RunPod Serverless Handler for NVIDIA-SMI GPU Information
Following RunPod official documentation patterns
"""

import runpod
import subprocess
import json
import os
import tempfile
from google.cloud import storage
from pathlib import Path


def download_models_from_gcs():
    """
    Download all models from Google Cloud Storage bucket to /runpod-volume/models/
    """
    try:
        # Get GCP credentials and bucket from environment
        gcp_credentials = os.getenv("GCP_CREDENTIALS")
        bucket_name = os.getenv("GCS_BUCKET", "talking-head-models")
        
        if not gcp_credentials:
            return {
                "status": "error",
                "error": "GCP_CREDENTIALS environment variable not set"
            }
        
        # Create models directory on persistent storage
        models_dir = Path("/runpod-volume/models")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Write GCP credentials to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(gcp_credentials)
            credentials_path = f.name
        
        # Set GOOGLE_APPLICATION_CREDENTIALS environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # List all blobs in the bucket
        blobs = list(bucket.list_blobs())
        downloaded_files = []
        
        print(f"Found {len(blobs)} files in bucket {bucket_name}")
        
        # Download each file
        for blob in blobs:
            # Skip directories (blobs ending with /)
            if blob.name.endswith('/'):
                continue
                
            # Create local path preserving directory structure
            local_path = models_dir / blob.name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Downloading {blob.name} to {local_path}")
            
            # Download the blob to local file
            blob.download_to_filename(str(local_path))
            downloaded_files.append(str(local_path))
        
        # Clean up credentials file
        os.unlink(credentials_path)
        
        return {
            "status": "success",
            "message": f"Downloaded {len(downloaded_files)} files from {bucket_name}",
            "downloaded_files": downloaded_files,
            "models_directory": str(models_dir)
        }
        
    except Exception as e:
        # Clean up credentials file if it exists
        if 'credentials_path' in locals():
            try:
                os.unlink(credentials_path)
            except:
                pass
                
        return {
            "status": "error",
            "error": f"Failed to download models: {str(e)}"
        }


def handler(job):
    """
    RunPod serverless handler function
    
    Args:
        job (dict): Job data containing input and other metadata
        
    Returns:
        dict: Result containing GPU information or error
    """
    try:
        # Get input data (optional for nvidia-smi)
        job_input = job.get("input", {})
        
        # Check if this is a model download request
        if job_input.get("action") == "download_models":
            print("Processing model download request...")
            return download_models_from_gcs()
        
        # Run nvidia-smi command to get GPU information
        print("Running nvidia-smi...")
        
        # Basic nvidia-smi output
        smi_result = subprocess.check_output(
            ['nvidia-smi'], 
            text=True, 
            stderr=subprocess.STDOUT
        )
        
        # Get additional GPU details
        gpu_query_result = subprocess.check_output([
            'nvidia-smi', 
            '--query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits'
        ], text=True, stderr=subprocess.STDOUT)
        
        # Parse GPU details
        gpu_lines = gpu_query_result.strip().split('\n')
        gpu_details = []
        for i, line in enumerate(gpu_lines):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 7:
                gpu_details.append({
                    "gpu_id": i,
                    "name": parts[0],
                    "driver_version": parts[1],
                    "memory_total_mb": parts[2],
                    "memory_used_mb": parts[3], 
                    "memory_free_mb": parts[4],
                    "temperature_c": parts[5],
                    "power_draw_w": parts[6]
                })
        
        # Get CUDA information if available
        cuda_version = "Not available"
        try:
            cuda_result = subprocess.check_output(['nvcc', '--version'], text=True, stderr=subprocess.STDOUT)
            # Extract CUDA version from nvcc output
            for line in cuda_result.split('\n'):
                if 'release' in line.lower():
                    cuda_version = line.strip()
                    break
        except:
            cuda_version = "NVCC not available"
        
        return {
            "status": "success",
            "nvidia_smi_output": smi_result,
            "gpu_details": gpu_details,
            "cuda_info": cuda_version,
            "gpu_count": len(gpu_details),
            "environment": {
                "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES", "Not set"),
                "runpod_endpoint_id": os.getenv("RUNPOD_ENDPOINT_ID", "Not set"),
            },
            "input_received": job_input
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_type": "subprocess_error",
            "error": f"Command failed: {str(e)}",
            "output": e.output if hasattr(e, 'output') else "No output"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error_type": "general_error",
            "error": str(e),
            "input_received": job.get("input", {})
        }


if __name__ == "__main__":
    print("Starting RunPod Serverless Handler...")
    print("Handler ready to process nvidia-smi requests")
    runpod.serverless.start({"handler": handler})