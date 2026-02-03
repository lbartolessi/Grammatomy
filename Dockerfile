FROM python:3.10-slim

# Install system dependencies required for visualization
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install project and API dependencies
# We install the package in editable mode or standard mode
RUN pip install -e .

# Pre-download models during build to speed up cold start in HF Spaces
# This respects the "Model Sovereignty" principle by baking them into the image
RUN python tools/manage_models.py

# Expose the default Streamlit port
EXPOSE 8501

# Start the Streamlit Demo
# server.address=0.0.0.0 is required for Docker
CMD ["streamlit", "run", "src/grammatomy/demo/app.py", "--server.address=0.0.0.0", "--server.port=8501"]