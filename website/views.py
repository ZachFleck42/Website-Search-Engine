from django.shortcuts import render
from src.crawler import crawlWebsite
from src.database_utils import fetchAllData, getAllTables, getRowCount
from src.search_utils import runSearch


def home(request):
    return render(request, 'home.html')


def crawl(request):
    renderArguments = {}
    renderArguments['activeTab'] = "/crawl"
    
    if request.method == "POST":
        
        # Check if the 'website to crawl' field was filled in properly
        websiteURL = request.POST.get('input_url')
        if not websiteURL:
            renderArguments['noURL'] = 1
            return render(request, 'crawl.html', renderArguments)
        renderArguments['userInput'] = websiteURL
        
        # If valid input, (attempt to) crawl the website
        webpageVisitCount, crawlTime = crawlWebsite(websiteURL)
        renderArguments['webpageVisitCount'] = webpageVisitCount
        renderArguments['crawlTime'] = round(crawlTime, 2)

        # If the crawler was unable to connect to the provided URL...
        if not webpageVisitCount:
            renderArguments['badURL'] = 1
        
    return render(request, 'crawl.html', renderArguments)
    
    
def search(request):
    # Initiate renderArguments
    renderArguments = {}
    renderArguments['activeTab'] = "/search"
    
    # Get available websites to search from the database
    renderArguments['searchableWebsites'] = []
    for table in getAllTables():
        renderArguments['searchableWebsites'].append(table[0].replace('_', '.'))
        
    # Define search method and amount of results options
    renderArguments['searchMethods'] = (
        ('Python str.count()','COUNT'),
        ('Boyer-Moore', 'BM'),
        ('Knuth-Morris-Pratt','KMP'),
        ('Robin-Karp','RK'),
        ('Aho-Corasick','AC'))
    renderArguments['amountOfResultsOptions'] = (10, 50, 100, 1000)
    
    if request.method == "POST":
        # Check if the 'website to search' field was filled in
        renderArguments['searchWebsite'] = request.POST.get('input_website')
        if not renderArguments['searchWebsite']:
            renderArguments['noWebsite'] = 1
            return render(request, 'search.html', renderArguments)
        renderArguments['searchTable'] = renderArguments['searchWebsite'].replace('.', '_')
        
        # Check if the 'search term' field was filled in properly
        renderArguments['searchTerm'] = request.POST.get('input_search')
        if renderArguments['searchTerm'] == '':
            renderArguments['noSearchTerm'] = 1
            return render(request, 'search.html', renderArguments)
        
        # Check if the 'search method' field was filled in. Default to str.count() method if not
        renderArguments['searchMethod'] = request.POST.get('input_method')
        if not renderArguments['searchMethod']:
            renderArguments['searchMethod'] = "COUNT" 
        renderArguments['searchMethodName'] = ([method for method in renderArguments['searchMethods'] if method[1] == renderArguments['searchMethod']])[0][0]  # Don't even worry about it
        
        # Check if the 'amount of results to display' field was filled in. Deafult to 10 if not
        renderArguments['amountOfResults'] = request.POST.get('input_amount')
        if not renderArguments['amountOfResults']:
            renderArguments['amountOfResults'] = 10
        renderArguments['amountOfResults'] = int(renderArguments['amountOfResults'])
        
        # If all fields filled in properly, run a search with the provided arguments
        searchResults, searchTime = runSearch(renderArguments['searchTable'], renderArguments['searchTerm'], renderArguments['searchMethod'], renderArguments['amountOfResults'])
        
        # Store the results of the search in arguments to be passed to the results page
        renderArguments['searchResults'] = searchResults
        renderArguments['searchTime'] = round((searchTime * 1000), 2)
        renderArguments['foundPages'] = len(searchResults)
        renderArguments['totalPages'] = getRowCount(renderArguments['searchTable'])
        
    return render(request, 'search.html', renderArguments)


def manageDatabase(request):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"

    websiteNames = []
    tableData = getAllTables()
    for table in tableData:
        websiteNames.append((table[0]).replace('_', '.'))
    renderArguments['tableData'] = zip(tableData, websiteNames)
    
    return render(request, 'manage-database.html', renderArguments)
    

def manageTable(request, table):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['table'] = table
    renderArguments['website'] = table.replace('_', '.')
    
    websiteData = fetchAllData(table)
    websiteData.sort(key=lambda x: x[1])
    renderArguments['pages'] = websiteData
    return render(request, 'manage-table.html', renderArguments)