from django.shortcuts import render
from data_handler.models import DataHandler


def index(request):
    return render(request, 'frontend/index.html')

def search(request):
    data_handler = DataHandler()
    data = data_handler.fetch_request_data(request)
    # return render(request, 'frontend/search.html')
    return render(request, 'frontend/search.html', context=data)
