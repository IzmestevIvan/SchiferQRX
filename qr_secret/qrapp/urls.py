from django.urls import path
from .views import index, generate_qr, decode_qr_secret


urlpatterns = [
    path('', index, name='index'),
    path('api/generate/', generate_qr, name='generate_qr'),
    path('api/decode/', decode_qr_secret, name='decode_qr_secret'),
]