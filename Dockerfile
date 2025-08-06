# ─────────────────────────────
# ⚡ Base Image: Slim & Fast
# ─────────────────────────────
FROM python:3.12-slim-bookworm

# ─────────────────────────────
# 📦 Install OS Dependencies
# ─────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    curl \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────
# 🔁 Set Build Mode Variable
# ─────────────────────────────
ARG BUILD_MODE=remote
ENV BUILD_MODE=${BUILD_MODE}

# ─────────────────────────────
# ⏳ Work in Temporary Directory
# ─────────────────────────────
WORKDIR /tmp/build-context

# ─────────────────────────────
# 🧱 Clone or Copy App Code
# ─────────────────────────────
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git /cl-dashboard-internal ; \
    fi

COPY . /tmp/local-copy
RUN if [ "$BUILD_MODE" = "local" ]; then \
      cp -r /tmp/local-copy /cl-dashboard-internal ; \
    fi

# ─────────────────────────────
# 📦 Install Python Requirements
# ─────────────────────────────
WORKDIR /cl-dashboard-internal
COPY requirements.txt requirements.txt  # In case not already copied
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────
# 🎯 Set Entrypoint for Cloud Run
# ─────────────────────────────
ENV PORT=8501
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
