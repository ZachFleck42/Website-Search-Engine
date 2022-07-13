FROM python:3.10
    
COPY requirements.txt .
RUN pip3 install -r requirements.txt

WORKDIR /app
COPY ./app .