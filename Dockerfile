ARG  CODE_VERSION=latest
FROM python:3.12.3-bookworm

WORKDIR /cl-dashboard-internal


RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/curiouslearning/cl-dashboard-internal.git .

RUN pip3 install -r requirements.txt

EXPOSE 8080

CMD ["streamlit", "run", "Acquisition_Funnel.py", "--server.port=8080"]