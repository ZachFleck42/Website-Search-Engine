from redis import Redis

connection = Redis(db=1)

toVisitKey = 'crawling:to_visit'
visitedKey = 'crawling:visited'
processingKey = 'crawling:queued'
content_key = 'crawling:content'


# Queue of URLs to visit
def addToQueue(value):
    if connection.execute_command('LPOS', toVisitKey, value) is None:
        connection.rpush(toVisitKey, value)

def popFromQueue(timeout=0):
    return connection.blpop(toVisitKey, timeout)


# Already visited URLs
def addToVisited(value):
    connection.sadd(visitedKey, value)

def hasBeenVisited(value):
    return connection.sismember(visitedKey, value)
    
def getVisitedCount():
    return connection.scard(visitedKey)


# Currently being processed by Celery
def markAsProcessing(value):
    connection.sadd(processingKey, value)

def isProcessing(value):
    return connection.sismember(processingKey, value)

def moveToVisited(value):
    connection.smove(processingKey, visitedKey, value)