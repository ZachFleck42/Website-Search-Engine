## Website-Search-Engine
My full stack implementation of a website crawler, search engine, and database management tool.

Application serves as a one-stop shop for crawling a website, scraping its data (in this case, human-readable text), and performing custom searches on the data. 
Optional pre-processing tools and multiple search algorithm options enable a user to customize and optimize their searches. 
And the dynamic frontend provides an easy-to-use interface for control of the application or to view/edit/delete data in the database.

<br>

## Application architecture:
Docker integrates and connects the application's three main services, making startup/development quick and painless:

1. A PostgresSQL database for persistent data storage.
2. Redis as a message-broker, queue manager, and general backend service.
3. Django as a web framework, both hosting and rendering a dynamic frontend that controls/interfaces with:

   * My own implementation of website crawler that uses:
  
     - Requests and BeautifulSoup to connect to and parse webpages.
     - Psycopg2 to execute SQL queries and create/modify/delete databases.
     - Celery for asynchronous task processing/execution.
    
   * A custom-made search engine that uses:
  
     - Four different search algorithms (Boyer-Moore, Knuth-Morris-Pratt, Aho-Corasick, Robin-Karp)
     - NLTK for text pre-processing utilities and techniques.
    
   * My implementation of a database management interface that allows a user to:
    
     - Quickly and easily view, manipulate, or delete tables within the database (or entries within each table).
    
Plus, a whole suite of custom utilities and functions increase the portability and readability of the program.

<br>

## Installation/Use:
1. Run ```docker-compose up``` in the directory and wait for containers to start.
2. Application is now running. Connect at http://localhost:8000
