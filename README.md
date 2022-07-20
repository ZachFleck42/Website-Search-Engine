# Website-Search-Engine
My full stack implementation of a website crawler, search engine, and database management tool.

Technologies used include:
- Requests and BeautifulSoup to connect to and parse webpages.
- NLTK for text pre-processing utilities.
- PostgresSQL for persistent data storage.
- Psycopg2 to execute SQL queries and create/modify/delete databases.
- Celery for asynchronous processing, using Redis as a message broker and queue manager.
- Django as a web framework, both hosting and rendering a dynamic frontend.
- Docker to integrate the multiple services and enable more rapid iteration/development.

<br>

## Installation/Use:
1. Run ```docker-compose up``` in the directory and wait for containers to start.
2. Application is now running. Connect at http://localhost:8000
