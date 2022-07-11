import psycopg2
import sys
from psycopg2 import sql

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


def checkValidUsage():
    if (len(sys.argv) != 3):
        print("FATAL ERROR: Improper number of arguments.")
        print("Please call program as: 'python app.py <URL> <MAX_DEPTH>")
        return 0
        
    return 1