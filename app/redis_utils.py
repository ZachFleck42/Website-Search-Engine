from redis import Redis

redisConnection = Redis(host='redis', port=6379)

toVisitKey = 'crawling:to_visit'
processingKey = 'crawling:queued'
visitedKey = 'crawling:visited'

# Queue of URLs to visit
def addToQueue(url):
    '''Add url to queue of URLs to be visited'''
    return redisConnection.sadd(toVisitKey, url)
    
def popFromQueue():
    '''Pop first-in URL from the queue of URLs to be visited'''
    return redisConnection.spop(toVisitKey)
    

# Currently being processed by Celery
def moveToProcessing(url):
    '''Mark the URL as having been sent to Celery for processing'''
    redisConnection.smove(toVisitKey, processingKey, url)
    
def isProcessing(url):
    '''Checks if URL has been sent to Celery for processing'''
    return redisConnection.sismember(processingKey, url)
    

# Already visited URLs
def moveToVisited(url):
    '''Moves URL from processing to visited'''
    redisConnection.smove(processingKey, visitedKey, url)
    
def hasBeenVisited(url):
    """Checks if URL has already been visited"""
    return redisConnection.sismember(visitedKey, url)
    
def getVisitedCount():
    '''Gets the number of URLs already visited by program'''
    return redisConnection.scard(visitedKey)


# Misc
def clearCache():
    '''Clears the Redis database for re-crawling a website'''
    redisConnection.flushall()