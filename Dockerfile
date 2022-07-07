FROM postgres:14.4

RUN apt-get -y update && apt-get install -y --fix-missing \
    libpq-dev \
    python3 \
    python3-pip
    
COPY requirements.txt .

RUN pip3 install -r requirements.txt