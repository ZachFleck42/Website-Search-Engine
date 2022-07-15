from django.db import models

# Create your models here.
class webpage(models.Model):
    url = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    desc = models.TextField()
    text = models.TextField()