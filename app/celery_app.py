from celery import Celery

app = Celery('Search_Engine',
             backend='rpc://',
             broker='amqp://rabbitmq',
             include='crawler')
