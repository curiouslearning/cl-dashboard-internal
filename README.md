# cl-data-dashboard
Streamlit Dashboard for Internal Analysis

**To run locally**

1. Install python 3.12.0 - https://www.python.org/downloads/release/python-3123/
2. git clone https://github.com/curiouslearning/cl-dashboard-internal.git
3. cd to ./cl-dashboard-internal
4. pip install -r requirements.txt
5. streamlit run main.py


docker build  --no-cache --platform linux/amd64  -t gcr.io/dataexploration-193817/cl-dashboard-internal:latest . 
docker push gcr.io/dataexploration-193817/cl-dashboard-internal:latest
