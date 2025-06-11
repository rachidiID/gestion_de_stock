# stock_project/urls.py
"""
URL configuration for stock_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from inventory.views import custom_logout_view # <<< Importer votre nouvelle vue


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),
    # URLs pour l'authentification
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    # Utilisation de votre vue de déconnexion personnalisée
    path('logout/', custom_logout_view, name='logout'), # <<< MODIFICATION ICI
]