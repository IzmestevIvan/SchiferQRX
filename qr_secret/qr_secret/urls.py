from django.contrib import admin
from django.urls import path, include


handler404 = 'qr_secret.views.custom_404'
handler500 = 'qr_secret.views.custom_500'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('qrapp.urls')),
    path('accounts/', include('users.urls')),
]