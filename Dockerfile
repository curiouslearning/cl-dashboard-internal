FROM python:3.12-slim-bookworm

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    curl \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG BUILD_MODE=remote
ENV BUILD_MODE=${BUILD_MODE}
ENV PORT=8501

# Use neutral temp folder for staging
WORKDIR /tmp/build-context

# Remote clone from GitHub
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git /cl-dashboard-internal ; \
    fi

# Optional: local copy
COPY . /tmp/local-copy
RUN if [ "$BUILD_MODE" = "local" ]; then \
      cp -r /tmp/local-copy /cl-dashboard-internal ; \
    fi

# Cleanup temp build folders
RUN rm -rf /tmp/local-copy /tmp/build-context /tmp/remote-copy || true

# Move into app and install requirements
WORKDIR /cl-dashboard-internal
RUN pip install --no-cache-dir -r requirements.txt

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
