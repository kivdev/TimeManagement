"""RESTProjectWithoutDjoser URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from MainPage.mail import SendAgain,ConfirmMail
from MainPage.views import Upload, MainPage,Index
from MainPage.items import Items,ItemsAdd
from MainPage.categs import Category,CategoryAdd,CategoryRemove
from MainPage.paterns import PaternPlace,PaternAdd,Patern
from MainPage.stats import Stats
from Users.views import Login, Logout, Register, Me, Change


urlpatterns = [
    path('confirm/<key>', ConfirmMail.as_view()),
    path('api/auth/confirm/', SendAgain.as_view()),
    path('admin/', admin.site.urls),
    path('index/', Index.as_view()),
    path('api/auth/login/', Login.as_view()),
    path('api/auth/logout/', Logout.as_view()),
    path('api/auth/register/', Register.as_view()),
    path('api/auth/change/', Change.as_view()),
    path('api/auth/me/', Me.as_view()),

    path('api/items/', Items.as_view()),
    path('api/items/<str:sdate>-<str:edate>', Items.as_view()),
    path('api/items/add/', ItemsAdd.as_view()),
    path('api/items/edit/', ItemsAdd.as_view()),
    path('api/categs/', Category.as_view()),
    path('api/categs/add/', CategoryAdd.as_view()),
    path('api/categs/remove/', CategoryRemove.as_view()),
    path('api/categs/edit/', CategoryAdd.as_view()),
    path('api/paterns/', Patern.as_view()),
    path('api/paterns/add/', PaternAdd.as_view()),
    path('api/paterns/edit/', PaternAdd.as_view()),
    path('api/paterns/place/', PaternPlace.as_view()),
    #path('api/items/[<str:combo>]', Combiner.as_view()),
    # path('api/icons/', Icons.as_view()),
    path('api/stats/', Stats.as_view()),

    path('upload/', Upload.as_view()),
    path('', MainPage.as_view()),

]
