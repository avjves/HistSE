from django.shortcuts import render
from data_handler.models import DataHandler, Charter


def index(request):
    return render(request, 'frontend/index.html', context={'current_site': 'index'})

def search(request, search_type):
    print("GET params:", request.GET)
    data_handler = DataHandler(search_type, 'search')
    data = data_handler.fetch_request_data(request)
    data.update({'current_site': 'search'})
    # return render(request, 'frontend/search.html')
    return render(request, 'frontend/search.html', context=data)


def chart(request, search_type):
    data_handler = DataHandler(search_type, 'charts')
    data = data_handler.fetch_request_data(request)
    charter = Charter()
    labels, values, name = charter.chart(data)
    data.update({'chart_labels': list(labels), 'chart_values': list(values), 'chart_name': name})
    return render(request, 'frontend/chart.html', context=data)
