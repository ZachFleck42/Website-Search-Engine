from django.shortcuts import render
from django.http import HttpResponse
from src import database_utils


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
    databaseTables = database_utils.getSearchableWebsites()
    if request.method == "POST":
        searchMethod = request.POST.get('searchMethod')
        searchTerm = request.POST.get('searchInput')
    else:
        searchMethod = "Waiting on user selection..."
        searchTerm = "Waiting on user input..."

    return render(request, 'search.html', {'searchTerm':searchTerm, 'searchMethods':SEARCH_CHOICES, 'searchMethod':searchMethod})