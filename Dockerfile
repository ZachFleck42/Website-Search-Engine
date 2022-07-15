FROM python:3.10
    
WORKDIR /search_engine
COPY . .
RUN pip3 install -r requirements.txt
# ENTRYPOINT ["tail", "-f", "/dev/null"]