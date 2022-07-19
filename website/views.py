from django.shortcuts import redirect, render
from src.crawler import crawlWebsite
import src.database_utils as database
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
            renderArguments['noURL'] = True
            return render(request, 'crawl.html', renderArguments)
        renderArguments['userInput'] = websiteURL

        # If valid input, (attempt to) crawl the website
        webpageVisitCount, crawlTime = crawlWebsite(websiteURL)
        renderArguments['webpageVisitCount'] = webpageVisitCount
        renderArguments['crawlTime'] = round(crawlTime, 2)

        # If the crawler was unable to connect to the provided URL...
        if not webpageVisitCount:
            renderArguments['badURL'] = True

    return render(request, 'crawl.html', renderArguments)


def search(request):
    # Initiate renderArguments
    renderArguments = {}
    renderArguments['activeTab'] = "/search"

    # Get available websites to search from the database
    websiteNames = []
    tableNames = []
    for table in database.getAllTables():
        tableNames.append(table[0])
        if table[0].endswith("_pp"):
            websiteNames.append((table[0][:-3]).replace('_', '.') + " (pre-processed)")
        else:
            websiteNames.append(table[0].replace('_', '.'))

    renderArguments['searchableWebsites'] = zip(websiteNames, tableNames)

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
        renderArguments['searchTable'] = request.POST.get('input_website')
        renderArguments['searchWebsite'] = websiteNames[tableNames.index(renderArguments['searchTable'])]
        if not renderArguments['searchTable']:
            renderArguments['noWebsite'] = True
            return render(request, 'search.html', renderArguments)

        # Check if the 'search term' field was filled in properly
        renderArguments['searchTerm'] = request.POST.get('input_search')
        if renderArguments['searchTerm'] == '':
            renderArguments['noSearchTerm'] = True
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
        searchResults, searchTime = runSearch(renderArguments['searchTable'], renderArguments['searchTerm'], renderArguments['searchMethod'])

        # Store the results of the search in arguments to be passed to the results page
        renderArguments['searchResults'] = searchResults[:renderArguments['amountOfResults']]
        renderArguments['searchTime'] = round((searchTime * 1000), 2)
        renderArguments['foundPages'] = len(searchResults)
        renderArguments['totalPages'] = database.getRowCount(renderArguments['searchTable'])

        # If less results found than the selected amount to display, adjust results output
        if renderArguments['foundPages'] < renderArguments['amountOfResults']:
            renderArguments['topResults'] = renderArguments['foundPages']
        else:
            renderArguments['topResults'] = renderArguments['amountOfResults']

    return render(request, 'search.html', renderArguments)


def manageDatabase(request):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['tableData'] = database.getAllTables()

    return render(request, 'manage-database.html', renderArguments)


def manageTable(request, table):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['table'] = table
    renderArguments['website'] = "https://" + table.replace('_', '.')

    websiteData = database.fetchAllData(table)
    websiteData.sort(key=lambda x: x[1])
    renderArguments['pages'] = websiteData

    if request.method == "POST":
        renderArguments['row'] = request.POST.get('row')
        database.deleteRow(table, renderArguments['row'])
        url = "/manage-database/" + table
        return redirect(url)

    return render(request, 'manage-table.html', renderArguments)


def renameTable(request, table):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['oldTable'] = table

    if request.method == "POST":
        renderArguments['newTable'] = request.POST.get('input_name')

        # Make sure user submit something
        if not renderArguments['newTable']:
            renderArguments['noTable'] = True
            return render(request, 'rename.html', renderArguments)

        # Check validity of provided table name
        if not database.validTableName(renderArguments['newTable']):
            renderArguments['badTable'] = 1
            return render(request, 'rename.html', renderArguments)

        # Rename the table and redirect back to the manage-database/ page
        database.changeTableName(renderArguments['oldTable'], renderArguments['newTable'])
        return redirect('/manage-database')

    return render(request, 'rename.html', renderArguments)


def deleteTable(request, table):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['table'] = table

    if request.method == "POST":
        database.dropTable(table)
        return redirect('/manage-database')

    return render(request, 'delete.html', renderArguments)

def processTable(request, table):
    renderArguments = {}
    renderArguments['activeTab'] = "/manage-database"
    renderArguments['table'] = table

    if request.method == "POST":
        checked = request.POST.get('input_newtable')
        newtable = table + "_pp"
        if checked:     # If the user checked the "make a new table" option, create a new table
            database.copyTable(table, newtable)
            database.preProcessTable(newtable)
        else:           # Otherwise, overwrite existing data
            database.preProcessTable(table)
            database.changeTableName(table, newtable)

        return redirect('/manage-database')

    return render(request, 'pre-process.html', renderArguments)