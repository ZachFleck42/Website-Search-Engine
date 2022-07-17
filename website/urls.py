from . import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('crawl/', views.crawl, name='crawl'),
    path('search/', views.search, name='search'),
    path('manage-database/', views.manageDatabase, name='manage-database'),
    path('admin/', admin.site.urls),
]
