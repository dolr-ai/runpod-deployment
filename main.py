import torch
import torch.nn as nn
import runpod
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

class SimpleTextClassifier(nn.Module):
    def __init__(self, vocab_size=1000, embed_dim=64, hidden_dim=128, num_classes=2):
        super(SimpleTextClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, _) = self.lstm(embedded)
        output = self.fc(self.dropout(hidden[-1]))
        return torch.softmax(output, dim=1)

def test_gpu_availability():
    """Test if GPU is available and accessible"""
    gpu_info = {
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device_count": 0,
        "devices": []
    }
    
    if torch.cuda.is_available():
        gpu_info["cuda_version"] = torch.version.cuda
        gpu_info["device_count"] = torch.cuda.device_count()
        
        for i in range(torch.cuda.device_count()):
            device_info = {
                "id": i,
                "name": torch.cuda.get_device_name(i),
                "memory_gb": torch.cuda.get_device_properties(i).total_memory / 1e9
            }
            gpu_info["devices"].append(device_info)
    
    return gpu_info

def run_simple_inference(text_tokens, model, device):
    """Run a simple inference to test GPU functionality"""
    model = model.to(device)
    model.eval()
    
    # Convert input to tensor and move to device
    input_tensor = torch.tensor(text_tokens).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(input_tensor)
        prediction = torch.argmax(output, dim=1)
    
    return {
        "prediction": prediction.cpu().item(),
        "confidence": torch.max(output).cpu().item(),
        "device_used": str(input_tensor.device)
    }

def handler(event):
    """
    RunPod handler function for serverless deployment
    """
    print("Worker started - Testing GPU functionality")
    
    # Get GPU information
    gpu_info = test_gpu_availability()
    print(f"GPU Info: {json.dumps(gpu_info, indent=2)}")
    
    # Determine device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    try:
        # Get input data
        input_data = event.get('input', {})
        
        # Create and test model
        model = SimpleTextClassifier()
        
        # Use provided tokens or default test tokens
        text_tokens = input_data.get('tokens', [1, 45, 123, 67, 234, 89, 12, 345])
        
        # Run inference
        result = run_simple_inference(text_tokens, model, device)
        
        # Test GPU memory if available
        gpu_memory_info = {}
        if torch.cuda.is_available():
            gpu_memory_info = {
                "allocated_mb": torch.cuda.memory_allocated() / 1e6,
                "reserved_mb": torch.cuda.memory_reserved() / 1e6,
                "max_allocated_mb": torch.cuda.max_memory_allocated() / 1e6
            }
        
        return {
            "status": "success",
            "gpu_info": gpu_info,
            "inference_result": result,
            "gpu_memory": gpu_memory_info,
            "input_tokens": text_tokens,
            "message": "GPU test completed successfully!"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "gpu_info": gpu_info
        }

# FastAPI app for local testing
app = FastAPI(title="RunPod GPU Test API", version="1.0.0")

class InferenceRequest(BaseModel):
    tokens: Optional[List[int]] = [1, 45, 123, 67, 234, 89, 12, 345]

@app.post("/predict")
async def predict(request: InferenceRequest):
    """FastAPI endpoint for local testing"""
    event = {"input": {"tokens": request.tokens}}
    return handler(event)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gpu_info = test_gpu_availability()
    return {
        "status": "healthy",
        "gpu_available": gpu_info["cuda_available"],
        "device_count": gpu_info["device_count"]
    }

@app.get("/ping")
async def ping():
    """Required endpoint for RunPod Load Balancing health checks"""
    # Return 200 for healthy, 204 for initializing
    return {"status": "healthy"}

if __name__ == "__main__":
    # For RunPod Load Balancing endpoints, we run FastAPI directly
    # Use PORT environment variable (RunPod standard)
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)