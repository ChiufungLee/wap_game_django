"""
URL configuration for wap_game project.

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
from django.urls import path
from game import views as views
from game import admin_views as admin_views
from game.utils import session as session_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', admin_views.register, name = "register"),
    path('login/', admin_views.login, name = "login"),
    path('api/session/check/', session_views.session_health_check, name='session_check'),
    path('index/', views.index, name = "index"),
    path('logout/', admin_views.logout, name = "logout"),
    path('wapadmin/', admin_views.admin_views, name='admin_view'),
    path('game_error/', admin_views.game_error, name='game_error'),
    path('wap_error/', views.handle_error, name='wap_error'),
    path('game/', views.game_page, name='game_page'),

    path('wap/', views.wap, name='wap'),
    path('chat/', views.chat, name='chat'),
    path('get_messages/', views.get_messages, name='get_messages'),
    path('send_message/', views.send_message, name='send_message'),

]
