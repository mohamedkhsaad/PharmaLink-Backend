from django.urls import path
from chat.consumers import ChatConsumer
ASGI_urlpatterns=[
    path("websocket",ChatConsumer.as_asgi())
]


