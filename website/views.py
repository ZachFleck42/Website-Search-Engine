from django.shortcuts import render
from django.http import HttpResponse
from src.crawler import crawlWebsite
from src.database_utils import getTableName, getSearchableWebsites
from src.search_utils import runSearch


SEARCH_CHOICES = (
    ('Python str.count()','COUNT'),
    ('Boyer-Moore', 'BM'),
    ('Knuth-Morris-Pratt','KMP'),
    ('Robin-Karp','RK'),
    ('Aho-Corasick','AC'),
)


# Create your views here.
def sayHello(request):
    return render(request, 'hello.html', {'name':'Zach'})
    
def search(request):
    databaseTables = getSearchableWebsites()
    
    if request.method == "POST":
        searchWebsite = request.POST.get('input_website')
        searchMethod = request.POST.get('input_method')
        searchTerm = request.POST.get('input_search')
        searchResults = runSearch(searchWebsite, searchTerm, searchMethod)
    else:
        searchWebsite = "Waiting on user selection..."
        searchMethod = "Waiting on user selection..."
        searchTerm = "Waiting on user input..."
        searchResults = "None"

    return render(request, 'search.html', {
        'searchableWebsites':databaseTables, 
        'searchMethods':SEARCH_CHOICES,
        'searchMethod':searchMethod, 
        'searchWebsite': searchWebsite, 
        'searchTerm':searchTerm, 
        'searchResults': searchResults})
    
def crawl(request):
    if request.method == "POST":
        crawledWebsite = request.POST.get('input_url')
        tableName = getTableName(crawledWebsite)
        webpageVisitCount, crawlTime = crawlWebsite(crawledWebsite, tableName)
    else:
        crawledWebsite = "Waiting on user input..."
        webpageVisitCount = "0"
        crawlTime = "0"
    
    return render(request, 'crawl.html', {
        'crawledWebsite':crawledWebsite, 
        'webpageVisitCount':webpageVisitCount,
        'crawlTime':crawlTime,
    })