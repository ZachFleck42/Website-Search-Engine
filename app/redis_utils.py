from redis import Redis

redisConnection = Redis(host='redis', port=6379)

toVisitKey = 'crawling:to_visit'
visitedKey = 'crawling:visited'
processingKey = 'crawling:queued'

# Queue of URLs to visit
def addToQueue(value):
    if redisConnection.execute_command('LPOS', toVisitKey, value) is None:
        redisConnection.rpush(toVisitKey, value)

def popFromQueue(timeout=0):
    return redisConnection.blpop(toVisitKey, timeout)


# Already visited URLs
def addToVisited(value):
    redisConnection.sadd(visitedKey, value)

def hasBeenVisited(value):
    return redisConnection.sismember(visitedKey, value)
    
def getVisitedCount():
    return redisConnection.scard(visitedKey)


# Currently being processed by Celery
def markAsProcessing(value):
    redisConnection.sadd(processingKey, value)

def isProcessing(value):
    return redisConnection.sismember(processingKey, value)

def moveToVisited(value):
    redisConnection.smove(processingKey, visitedKey, value)
    

# Misc
def clearCache():
    redisConnection.flushall()