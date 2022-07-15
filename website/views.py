from django.shortcuts import render
from src.crawler import crawlWebsite
from src.database_utils import getTableName, getSearchableWebsites
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
    renderArguments = {}
    renderArguments['searchableWebsites'] = getSearchableWebsites()
    renderArguments['searchMethods'] = (
        ('Python str.count()','COUNT'),
        ('Boyer-Moore', 'BM'),
        ('Knuth-Morris-Pratt','KMP'),
        ('Robin-Karp','RK'),
        ('Aho-Corasick','AC'),
    )
    
    if request.method == "POST":
        renderArguments['searchWebsite'] = request.POST.get('input_website')
        renderArguments['searchMethod'] = request.POST.get('input_method')
        renderArguments['searchTerm'] = request.POST.get('input_search')
        
        searchResults, searchTime = runSearch(renderArguments['searchWebsite'], renderArguments['searchTerm'], renderArguments['searchMethod'])
        renderArguments['searchResults'] = searchResults
        renderArguments['searchTime'] = round((searchTime * 1000), 2)
        
    return render(request, 'search.html', renderArguments)
