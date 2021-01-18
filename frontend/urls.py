from django.urls import path

from . import views


urlpatterns = [
        path('', views.index),
        path('<str:search_type>/search', views.search),
        path('<str:search_type>/charts', views.chart),
    ]
