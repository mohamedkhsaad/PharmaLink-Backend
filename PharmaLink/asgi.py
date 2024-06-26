"""
ASGI config for PharmaLink project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import ASGI_urlpatterns
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PharmaLink.settings')

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    "websocket":URLRouter(ASGI_urlpatterns)
})
