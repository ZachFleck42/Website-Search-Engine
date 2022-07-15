from django.db import models

class searchForm(models.Model):
    # database = 
    # searchMethod = 
    # searchInput = models.CharField(max_length=100)
    # exactMatch = 
    pass

class crawlForm(models.Model):
    url = models.CharField(max_length=200)