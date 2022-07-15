FROM python:3.10
    
WORKDIR /search-engine
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["tail", "-f", "/dev/null"]