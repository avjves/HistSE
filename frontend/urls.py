from django.urls import path

from . import views


urlpatterns = [
        path('', views.index),
        path('<str:search_type>/search', views.search),
        path('<str:search_type>/charts', views.chart),
        path('<str:search_type>/download', views.download),
        path('<str:search_type>/<str:flow_type>/map', views.map),
        path('<str:search_type>/<str:flow_type>/<str:data_type>/map_data', views.map_data),
    ]
