from . import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('crawl/', views.crawl, name='crawl'),
    path('search/', views.search, name='search'),
    path('manage-database/', views.manageDatabase, name='manage-database'),
    path('manage-database/<str:table>/', views.manageTable, name='manage-table'),
    path('manage-database/<str:table>/rename/', views.renameTable, name='rename-table'),
    path('manage-database/<str:table>/delete/', views.deleteTable, name='delete-table'),
    path('manage-database/<str:table>/pre-process/', views.processTable, name='process-table'),
    path('admin/', admin.site.urls),
]
