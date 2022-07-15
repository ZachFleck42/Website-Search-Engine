from redis import Redis

redisConnection = Redis(host='redis', port=6379)

toVisitKey = 'crawling:to_visit'
visitedKey = 'crawling:visited'

# Queue of URLs to visit
def addToQueue(url):
    '''Add url to queue of URLs to be visited'''
    return redisConnection.sadd(toVisitKey, url)
    
def popFromQueue():
    '''Pop first-in URL from the queue of URLs to be visited'''
    if item := redisConnection.spop(toVisitKey):
        return item.decode('utf-8')
        
def getQueueCount():
    '''Gets the number of URLs in the queue'''
    return redisConnection.scard(toVisitKey)
        

# Already visited URLs
def markVisited(url):
    '''Moves URL from queue to visited'''
    redisConnection.sadd(visitedKey, url)
    
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