import csv

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from data_handler.models import DataHandler, DataExporter, Charter, Mapper



def index(request):
    return render(request, 'frontend/index.html', context={'current_site': 'index'})

def updates(request):
    return render(request, 'frontend/updates.html', context={'current_site': 'updates'})

def aboutus(request):
    return render(request, 'frontend/aboutus.html', context={'current_site': 'about_us'})


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
    labels, values, name = charter.chart(data, request)
    data.update({'chart_labels': list(labels), 'chart_values': list(values), 'chart_name': name})
    return render(request, 'frontend/chart.html', context=data)

def chart_better(request, search_type, normalization_type, date_scope):
    data_handler = DataHandler(search_type, 'charts', extra_args={'normalization_type': normalization_type, 'date_scope': date_scope})
    data = data_handler.fetch_request_data(request)
    new_facets = []
    for facet in data['facets']:
        if date_scope == 'year' and facet['field'] == 'year':
            new_facets.append(facet)
        elif date_scope == 'month' and facet['field'] == 'month':
            new_facets.append(facet)
    charter = Charter()
    labels, values, name = charter.chart(new_facets, normalization_type, date_scope, request)
    data.update({'chart_labels': list(labels), 'chart_values': list(values), 'chart_name': name})
    return render(request, 'frontend/chart.html', context=data)



def map(request, search_type, flow_type):
    data_handler = DataHandler(search_type, 'map', extra_args={'flow_type': flow_type})
    data = data_handler.fetch_request_data(request)
    return render(request, 'frontend/map.html', context=data)

def map_data(request, search_type, flow_type, data_type):
    data_handler = DataHandler(search_type, 'map')
    if search_type != 'cluster':
        return HttpResponse(status=501)
    data = data_handler.fetch_all_data(request, fields=['date', 'location', 'country', 'coordinates'], data_type='hits')
    mapper = Mapper(flow_type, data_type)
    csv_data = mapper.format_map_data(data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(data_type)
    writer = csv.writer(response)
    writer.writerows(csv_data)
    return response


def download(request, search_type):
    """
    Sends the current request to user as a downloadable CSV.
    """
    data_handler = DataHandler(search_type, 'download')
    data_exporter = DataExporter(data_handler=data_handler)
    lines = data_exporter.export_current_search(request, search_type)
    response = HttpResponse(content_type='text/tsv')
    response['Content-Disposition'] = 'attachment; filename="{}.tsv"'.format('download')
    writer = csv.writer(response, delimiter='\t')
    writer.writerows(lines)
    return response



