# Use latest stable Python base image
ARG CODE_VERSION=latest
FROM python:3.12.3-bookworm

# Set working directory inside container
WORKDIR /cl-dashboard-internal

# Set build mode: 'remote' (Cloud Run) or 'local' (GCE VM)
ARG BUILD_MODE=remote
ENV BUILD_MODE=${BUILD_MODE}

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Conditionally clone the repo for remote/Cloud Run builds
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git . ; \
    fi

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the Streamlit port (default to 8501)
EXPOSE 8501
ENV PORT=8501

# Run app with dynamic port + external access
CMD ["sh", "-c", "python add_ga.py && streamlit run main.py --server.port=$PORT --server.address=0.0.0.0"]
