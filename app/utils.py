import psycopg2
import sys
from psycopg2 import sql
from urllib.parse import urlparse

databaseConnectionParamaters = {"host": "app", "database": "searchenginedb", "user": "postgres", "password": "postgres"}

def tableExists(tableName):
    '''
    Accepts a table name to check.
    If table exists in the databse, function returns True. Returns false otherwise.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    databaseCursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tableName.replace('\'', '\'\'')))
    if databaseCursor.fetchone()[0] == 1:
        return True

    return False


def getTableName(url):
    '''
    Accepts a URL as a string.
    Generates the name of an SQL table for a website based on its URL.
    Returns the name of the table as a string.
    '''
    pageHost = (urlparse(url).hostname).lower()
    if pageHost[0:4] == "www.":
        tableName = pageHost[4:].split('.', 1)[0]
    else:
        tableName = pageHost.split('.', 1)[0]

    return tableName


def checkValidUsage():
    '''
    Returns 1 if program called properly.
    Prints error message and returns 0 if program called improperly.
    '''
    if (len(sys.argv) != 2):
        print("FATAL ERROR: Improper number of arguments.")
        print("Please call program as: 'python app.py URL")
        return 0
        
    return 1
    
    
def createTable(tableName):
    '''
    Accepts the name of a table to be created.
    Creates the table according to 
    '''
    # Create a table for the website in the database
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    databaseCursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_text VARCHAR);")
        .format(sql.Identifier(tableName)))
    databaseConnection.commit()
    databaseConnection.close()
    
    
def dropTable(tableName):
    '''
    Accepts the name of a table to be dropped.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    databaseCursor.execute(sql.SQL("DROP TABLE {};")
        .format(sql.Identifier(tableName)))
    databaseConnection.commit()
    databaseConnection.close()