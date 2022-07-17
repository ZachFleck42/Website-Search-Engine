from django.shortcuts import render
from src.crawler import crawlWebsite
from src.database_utils import getTableName, getSearchableWebsites, getRowCount
from src.search_utils import runSearch


def crawl(request):
    renderArguments = {}
    if request.method == "POST":
        # Check if the 'website to crawl' field was filled in properly
        websiteURL = request.POST.get('input_url')
        if not websiteURL:
            renderArguments['blankForm'] = 1
            return render(request, 'crawl.html', renderArguments)
        renderArguments['crawledURL'] = websiteURL
        
        # If valid input, crawl the provided website for data and store in database
        tableName = getTableName(websiteURL)
        webpageVisitCount, crawlTime = crawlWebsite(websiteURL, tableName)
        renderArguments['webpageVisitCount'] = webpageVisitCount
        renderArguments['crawlTime'] = round(crawlTime, 2)
        
    return render(request, 'crawl.html', renderArguments)
    
    
def search(request):
    # Define search methods available to user
    searchMethods = (
        ('Python str.count()','COUNT'),
        ('Boyer-Moore', 'BM'),
        ('Knuth-Morris-Pratt','KMP'),
        ('Robin-Karp','RK'),
        ('Aho-Corasick','AC'),
    )
    
    # Initiate renderArguments with necessary variables to display any search page
    renderArguments = {}
    renderArguments['searchMethods'] = list(searchMethods)
    renderArguments['searchableWebsites'] = getSearchableWebsites()
    renderArguments['amountOfResultsOptions'] = (10, 50, 100, 1000)
    
    # If the user has attempted to make a search...
    if request.method == "POST":
        # Check if the 'website to search' field was filled in
        renderArguments['searchWebsite'] = request.POST.get('input_website')
        if not renderArguments['searchWebsite']:
            renderArguments['noWebsite'] = 1
            return render(request, 'search.html', renderArguments)
        
        # Check if the 'search method' field was filled in. Default to str.count() method if not
        renderArguments['searchMethod'] = request.POST.get('input_method')
        if not renderArguments['searchMethod']:
            renderArguments['searchMethod'] = "COUNT" 
        renderArguments['searchMethodName'] = ([method for method in searchMethods if method[1] == renderArguments['searchMethod']])[0][0]  # Don't even worry about it
        
        # Check if the 'amount of results to display' field was filled in. Deafult to 10 if not
        renderArguments['amountOfResults'] = request.POST.get('input_amount')
        if not renderArguments['amountOfResults']:
            renderArguments['amountOfResults'] = 10
        
        # Check if the 'search term' field was filled in properly
        renderArguments['searchTerm'] = request.POST.get('input_search')
        if renderArguments['searchTerm'] == '':
            renderArguments['noSearchTerm'] = 1
            return render(request, 'search.html', renderArguments)
        
        # If all fields filled in properly, run a search with the provided arguments
        searchResults, searchTime = runSearch(renderArguments['searchWebsite'], renderArguments['searchTerm'], renderArguments['searchMethod'], renderArguments['amountOfResults'])
        
        # Store the results of the search in arguments to be passed to the results page
        renderArguments['searchResults'] = searchResults
        renderArguments['searchTime'] = round((searchTime * 1000), 2)
        renderArguments['foundPages'] = len(searchResults)
        renderArguments['totalPages'] = getRowCount(renderArguments['searchWebsite'])
        
    return render(request, 'search.html', renderArguments)


def home(request):
    return render(request, 'home.html')
    

def manageDatabase(request):
    # TODO
    return render(request, 'manage-database.html')