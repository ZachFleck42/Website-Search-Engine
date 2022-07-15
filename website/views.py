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

def sayHello(request):
    return render(request, 'hello.html', {'name':'Zach'})
    
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
        renderArguments['searchResults'] = runSearch(renderArguments['searchWebsite'], renderArguments['searchTerm'], renderArguments['searchMethod'])

    return render(request, 'search.html', renderArguments)

    
def crawl(request):
    renderArguments = {}
    
    if request.method == "POST":
        websiteURL = request.POST.get('input_url')
        tableName = getTableName(websiteURL)
        webpageVisitCount, crawlTime = crawlWebsite(websiteURL, tableName)
        
        renderArguments['crawledURL'] = websiteURL
        renderArguments['webpageVisitCount'] = webpageVisitCount
        renderArguments['crawlTime'] = crawlTime

    return render(request, 'crawl.html', renderArguments)