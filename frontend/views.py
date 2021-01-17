from django.shortcuts import render
from data_handler.models import DataHandler


def index(request):
    return render(request, 'frontend/index.html', context={'current_site': 'index'})

def search(request, search_type):
    data_handler = DataHandler(search_type)
    data = data_handler.fetch_request_data(request)
    data.update({'current_site': 'search'})
    # return render(request, 'frontend/search.html')
    return render(request, 'frontend/search.html', context=data)



