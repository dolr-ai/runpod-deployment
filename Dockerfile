FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application
COPY main.py .

# Expose port (optional, for debugging)
EXPOSE 8000

# Start the RunPod serverless handler
CMD ["python", "-u", "main.py"]