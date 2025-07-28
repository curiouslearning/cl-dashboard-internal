ARG  CODE_VERSION=latest
ARG  BUILD_MODE=remote
FROM python:3.12.3-bookworm

WORKDIR /cl-dashboard-internal

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Conditionally clone the repo only if in 'remote' build mode
RUN if [ "$BUILD_MODE" = "remote" ]; then \
      git clone https://github.com/curiouslearning/cl-dashboard-internal.git . ; \
    fi

RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD ["sh", "-c", "python add_ga.py && streamlit run main.py --server.port=8080"]
