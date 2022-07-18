import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

databaseConnectionParamaters = {"host": "postgres", "database": "searchEngineDb", "user": "postgres", "password": "postgres"}


def getTableName(url):
    '''
    Returns the name of an SQL table for a website based on its URL.
    Name takes the form: "urlhostname_domain"
    '''
    return(((urlparse(url).hostname).replace('www.', '')).replace('.', '_'))
    

def tableExists(tableName):
    '''
    Checks to see if a table with name {tableName} already exists in database.
    Returns True if found, False if not.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name = %s)", (tableName, ))
    result = databaseCursor.fetchone()[0]
    
    databaseConnection.close()
    return result


def createTable(tableName):
    '''
    Creates a table with name {tableName} in the database
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    query = sql.SQL("CREATE TABLE {table} (page_url VARCHAR, page_title VARCHAR, page_desc VARCHAR, page_text VARCHAR);").format(
        table = sql.Identifier(tableName))
    databaseCursor.execute(query)
        
    databaseConnection.commit()
    databaseConnection.close()
    
    
def dropTable(tableName):
    '''
    Drops a table with name {tableName} from the database
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    query = sql.SQL("DROP TABLE {table};").format(
        table = sql.Identifier(tableName))
    databaseCursor.execute(query)
        
    databaseConnection.commit()
    databaseConnection.close()
    
    
def renameTable(tableName, newName):
    '''
    Renames table {tableName} to {newName} in the database.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()

    query = sql.SQL("ALTER TABLE {old} RENAME TO {new}").format(
        old = sql.Identifier(tableName),
        new = sql.Identifier(newName))
    databaseCursor.execute(query)
    
    databaseConnection.commit()
    databaseConnection.close()

    
def appendData(url, pageData, tableName):
    '''
    Appends specified data to the database.
    '''
    pageTitle, pageDesc, pageText = pageData
    
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    query = sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s)").format(
        sql.Identifier(tableName),
        [url, pageTitle, pageDesc, pageText])
    databaseCursor.execute(query)
    
    databaseConnection.commit()
    databaseConnection.close()
    

def fetchAllData(tableName):
    '''
    Returns all rows of data found in table with name {tableName} in database.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    query = sql.SQL("SELECT * FROM {table}").format(
        table = sql.Identifier(tableName))
    databaseCursor.execute(query)
    
    data = databaseCursor.fetchall()
    databaseConnection.close()
    return data


def getAllTables():
    '''
    Gets a list of lists of all tables in the database and their rowcounts.
    List is sorted alphabetically by table name.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    databaseTables = databaseCursor.fetchall()
    databaseConnection.close()
    
    tableData = []
    for table in databaseTables:
        tableName = table[0]
        rowCount = getRowCount(tableName)
        tableData.append([tableName, rowCount])
        
    return sorted(tableData)
    
    
def getRowCount(tableName):
    '''
    Returns the number of rows in table {tableName}.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    query = sql.SQL("SELECT COUNT(*) from {table}").format(
        table = sql.Identifier(tableName))
    databaseCursor.execute(query)
    
    rowCount = databaseCursor.fetchall()
    databaseConnection.close()
    return rowCount[0][0]
    

def deleteRow(tableName, pageURL):
    '''
    Deletes the row in {tableName} where column page_url = {pageURL}.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()

    query = sql.SQL("DELETE FROM {table} where {col} = %s").format(
        table = sql.Identifier(tableName),
        col = sql.Identifier('page_url'))
    databaseCursor.execute(query, (pageURL,))
    
    databaseConnection.commit()
    databaseConnection.close()