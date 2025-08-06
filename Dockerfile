# ─────────────────────────────
# ⚡ Use Slim Python Base
# ─────────────────────────────
FROM python:3.12-slim-bookworm

# ─────────────────────────────
# 🧼 Set Environment Vars
# ─────────────────────────────
ARG BUILD_MODE=remote
ENV BUILD_MODE=${BUILD_MODE}
ENV PORT=8501

# ─────────────────────────────
# 🛠 Install Required OS Packages (only essentials)
# ─────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────
# 📦 Install Python Packages
# ─────────────────────────────
# Always set working dir to avoid weird pip behavior
WORKDIR /app

# Copy early if needed for layer caching
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────
# 📁 Clone or Copy Code
# ─────────────────────────────
# Remote clone
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git /app ; \
    fi

# Local copy
COPY . /tmp/local-copy
RUN if [ "$BUILD_MODE" = "local" ]; then \
      cp -r /tmp/local-copy/* /app ; \
    fi

# ─────────────────────────────
# ▶ Entrypoint
# ─────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
