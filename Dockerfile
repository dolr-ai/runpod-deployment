FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application
COPY main.py .

# Expose port 80 (RunPod Load Balancing default)
EXPOSE 80

# Start the RunPod serverless handler
CMD ["python", "-u", "main.py"]