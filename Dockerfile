# Declare the argument globally for default values
ARG BUILD_MODE=remote

FROM python:3.12.3-bookworm

WORKDIR /cl-dashboard-internal

# 👇 Define it again inside the image so it's available to RUN
ARG BUILD_MODE
ENV BUILD_MODE=${BUILD_MODE}

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    python3-pip \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*


# ✅ Now this will actually respect the --build-arg value
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git . ; \
    fi

RUN pip3 install --no-cache-dir -r requirements.txt
