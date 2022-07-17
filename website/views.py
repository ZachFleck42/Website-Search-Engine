from django.shortcuts import render
from src.crawler import crawlWebsite
from src.database_utils import getTableName, getSearchableWebsites, getRowCount
from src.search_utils import runSearch


def crawl(request):
    renderArguments = {}
    
    if request.method == "POST":
        websiteURL = request.POST.get('input_url')
        tableName = getTableName(websiteURL)
        webpageVisitCount, crawlTime = crawlWebsite(websiteURL, tableName)
        
        renderArguments['crawledURL'] = websiteURL
        renderArguments['webpageVisitCount'] = webpageVisitCount
        renderArguments['crawlTime'] = round(crawlTime, 2)
        
    return render(request, 'crawl.html', renderArguments)
    
    
def search(request):
    searchMethods = (
        ('Python str.count()','COUNT'),
        ('Boyer-Moore', 'BM'),
        ('Knuth-Morris-Pratt','KMP'),
        ('Robin-Karp','RK'),
        ('Aho-Corasick','AC'),
    )
    
    renderArguments = {}
    renderArguments['searchMethods'] = list(searchMethods)
    renderArguments['searchableWebsites'] = getSearchableWebsites()
    renderArguments['amountOfResultsOptions'] = (10, 50, 100, 1000)
    
    if request.method == "POST":
        renderArguments['searchWebsite'] = request.POST.get('input_website')
        renderArguments['searchMethod'] = request.POST.get('input_method')
        renderArguments['searchMethodName'] = ([method for method in searchMethods if method[1] == renderArguments['searchMethod']])[0][0]  # Don't even worry about it
        renderArguments['searchTerm'] = request.POST.get('input_search')
        renderArguments['amountOfResults'] = int(request.POST.get('input_amount'))

        searchResults, searchTime = runSearch(renderArguments['searchWebsite'], renderArguments['searchTerm'], renderArguments['searchMethod'], renderArguments['amountOfResults'])
        
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