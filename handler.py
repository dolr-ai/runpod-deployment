"""
RunPod Serverless Handler for NVIDIA-SMI GPU Information
Following RunPod official documentation patterns
"""

import runpod
import subprocess
import json
import os
from pathlib import Path


def list_workspace_files(path="/workspace"):
    """
    List files and directories in the specified path
    """
    try:
        path_obj = Path(path)
        
        if not path_obj.exists():
            return {
                "status": "error",
                "error": f"Path does not exist: {path}"
            }
        
        files = []
        directories = []
        
        # List all items in the directory
        for item in path_obj.iterdir():
            if item.is_file():
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "type": "file"
                })
            elif item.is_dir():
                directories.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory"
                })
        
        # Sort for consistent output
        files.sort(key=lambda x: x["name"])
        directories.sort(key=lambda x: x["name"])
        
        return {
            "status": "success",
            "path": str(path_obj.absolute()),
            "directories": directories,
            "files": files,
            "total_files": len(files),
            "total_directories": len(directories)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to list files: {str(e)}"
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
        print(f"DEBUG: Received job_input: {job_input}")
        print(f"DEBUG: Action value: '{job_input.get('action')}'")
        print(f"DEBUG: Action type: {type(job_input.get('action'))}")
        
        # Model downloading removed - handle via S3 manually
        if job_input.get("action") == "download_models":
            return {
                "status": "error",
                "error": "Model downloading removed. Use S3 API directly to manage models on the network volume."
            }
        
        # Check if this is a file listing request
        if job_input.get("action") == "list_files":
            print("Processing file listing request...")
            return list_workspace_files(job_input.get("path", "/workspace"))
        
        # If action is specified but not recognized, return error
        if "action" in job_input:
            return {
                "status": "error",
                "error": f"Unrecognized action: '{job_input.get('action')}'. Valid actions: 'download_models', 'list_files'",
                "input_received": job_input,
                "debug_info": {
                    "action_value": job_input.get("action"),
                    "action_type": str(type(job_input.get("action"))),
                    "all_input_keys": list(job_input.keys())
                }
            }
        
        # Run nvidia-smi command to get GPU information (only when no action specified)
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