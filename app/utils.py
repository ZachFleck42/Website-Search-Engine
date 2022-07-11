import sys
from urllib.parse import urlparse

def tableExists(databaseConnection, tableName):
    '''
    Accepts a database connection and a table name to check.
    If table exists in the databse, function returns True. Returns false otherwise.
    '''
    cursor = databaseConnection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tableName.replace('\'', '\'\'')))
    if cursor.fetchone()[0] == 1:
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
    if (len(sys.argv) != 3):
        print("FATAL ERROR: Improper number of arguments.")
        print("Please call program as: 'python app.py URL MAX_DEPTH")
        return 0
        
    return 1