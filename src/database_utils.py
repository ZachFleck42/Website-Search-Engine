import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

databaseConnectionParamaters = {"host": "postgres", "database": "searchEngineDb", "user": "postgres", "password": "postgres"}


def createTable(tableName):
    '''
    Creates a table with name {tableName} in the database
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute(sql.SQL("CREATE TABLE {} (page_url VARCHAR, page_title VARCHAR, page_desc VARCHAR, page_text VARCHAR);")
        .format(sql.Identifier(tableName)))
        
    databaseConnection.commit()
    databaseConnection.close()
    
    
def dropTable(tableName):
    '''
    Drops a table with name {tableName} from the database
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute(sql.SQL("DROP TABLE {};")
        .format(sql.Identifier(tableName)))
        
    databaseConnection.commit()
    databaseConnection.close()


def getTableName(url):
    '''
    Returns the name of an SQL table for a website based on its URL.
    Name attempts to take the form: "urlhostname_domain"
    '''
    pageHost = urlparse(url).hostname
    tableName = pageHost.replace('.', '_')
    
    return(tableName)
    

def tableExists(tableName):
    '''
    Checks to see if a table with name {tableName} already exists in database.
    Returns True if found, False if not.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{}'"
        .format(tableName.replace('\'', '\'\'')))
        
    if databaseCursor.fetchone()[0] == 1:
        databaseConnection.close()
        return True
    
    databaseConnection.close()
    return False

    
def appendData(url, pageData, tableName):
    '''
    Appends specified data to the database.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    cursor = databaseConnection.cursor()
    
    pageTitle, pageDesc, pageText = pageData
    cursor.execute(sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s);")
        .format(sql.Identifier(tableName)), [url, pageTitle, pageDesc, pageText])
    
    databaseConnection.commit()
    databaseConnection.close()
    return 1
    

def fetchAllData(tableName):
    '''
    Returns all rows of data found in table with name {tableName} in database.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute(sql.SQL("SELECT * FROM {};")
        .format(sql.Identifier(tableName)))
    
    data = databaseCursor.fetchall()
    databaseConnection.close()
    data.sort(key=lambda x: x[1])
    return data


def getSearchableWebsites():
    '''
    Gets a list of lists of all tables in the database and their rowcounts.
    List is sorted alphabetically by table name.
    '''
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    databaseTables = databaseCursor.fetchall()
    databaseConnection.close()
    
    searchableWebsites = []
    for table in databaseTables:
        tableName = table[0]
        rowCount = getRowCount(tableName)
        searchableWebsites.append((tableName, rowCount))
        
    return sorted(searchableWebsites)
    
    
def getRowCount(tableName):
    databaseConnection = psycopg2.connect(**databaseConnectionParamaters)
    databaseCursor = databaseConnection.cursor()
    
    databaseCursor.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(tableName)))
    
    rowCount = databaseCursor.fetchall()
    databaseConnection.close()
    return rowCount[0][0]
    

def renameTable(tableName, newName):
    pass


def getAllTables():
    pass


def deleteRow():
    pass