"""
This class houses all the necessary functionality to handle the requested data.
Acts as a sort of a middle man, where the API endpoints ask for the data given the request parameters.
Rather than asking for the necessary data from indexed search engine (Solr), it formats the parameters
and asks a Interactor to fetch the data.
"""
import json

from solr_interactor.models import SolrInteractor

available_hit_facets = [
        {'field': 'title', 'name': 'Title'},
        {'field': 'year', 'name': 'Year of apperance'},
        {'field': 'location', 'name': 'Location'},
        {'field': 'country', 'name': 'Country'},
]

available_cluster_facets = [
        {'field': 'starting_country', 'name': 'Starting country'},
        {'field': 'starting_location', 'name': 'Starting location'},
        {'field': 'starting_year', 'name': 'Starting year of apperance'},
        # {'field': 'title', 'name': 'Title'},
        ]


hit_field_mapping = {
        'cluster_id': 'Cluster ID',
        'doc_id': 'Document ID',
        'id': 'ID',
        'text': 'Text',
        'title': 'Title',
        'date': 'Date',
        'url': 'URL',
        'country': 'Country',
        'location': 'Location',
        'year': 'Year',
        'starting_text': 'Starting Text',
        'starting_country': 'Country',
}

cluster_field_mapping = {
        'cluster_id': 'Cluster ID',
        'doc_id': 'Document ID',
        'id': 'ID',
        'count': 'Count',
        'timespan': 'Timespan',
        'locations': 'Locations',
        'average_length': 'Average length',
        'starting_text': 'Starting Text',
        'starting_title': 'Title',
        'starting_date': 'Date',
        'starting_country': 'Country',
        'starting_location': 'Location',
        'starting_year': 'Starting year',
}

hit_field_mapping.update(cluster_field_mapping)

class DataHandler:

    def __init__(self, search_type):
        self.search_type = search_type
        self.hit_interactor = SolrInteractor(core='swe_v2')
        self.cluster_interactor = SolrInteractor(core='swe_v2_clusters')
        # self.available_facets = AvailableFacets()



    def fetch_request_data(self, request):
        """
        Given the request parameters inside the request, asks an Interactor for the necessary data and 
        formats it in the way the client asked.
        """
        parameters = self._extract_request_parameters(request)
        print("Extracted parameters", parameters)
        data = self._fetch_data(parameters)
        return self._format_data(data, parameters, request)



    def _extract_request_parameters(self, request):
        """
        Extracts the HTTP GET request parameters from the request object and returns them as a dictionary.
        """
        default_params = {
                'q': request.GET.get('q') if request.GET.get('q') else '',
                'start': int(request.GET.get('start', 0)),
                'rows': int(request.GET.get('rows', 10)),
                'fq': json.loads(request.GET.get('fq', "[]")),
                'facet': 'true',
                'facet.field': [facet['field'] for facet in available_hit_facets],
        }
        if  self.search_type == 'hits':
            return {'hits': default_params}
        elif self.search_type ==  'clusters':
            cluster_params = default_params
            cluster_params['facet.field'] = [facet['field'] for facet in available_cluster_facets]
            return {'hits': cluster_params}
        elif self.search_type ==  'cluster':
            params = {
                'hits': default_params,
                'metadata': {'q': '*:*', 'fq': default_params['fq']}
            }
            return params


    def _fetch_data(self, parameters):
        """
        Fetches the necessary data from solr cores.
        """
        if self.search_type == 'hits':
            data = self.hit_interactor.fetch_data(parameters['hits'])
            return {'hits': data}
        elif self.search_type == 'clusters':
            data = self.cluster_interactor.fetch_data(parameters['hits'])
            return {'hits': data}
        elif self.search_type == 'cluster':
            hit_data = self.hit_interactor.fetch_data(parameters['hits'])
            cluster_metadata = self.cluster_interactor.fetch_data(parameters['metadata'])
            return {'hits': hit_data, 'metadata': cluster_metadata}

    def _format_facets(self, data, parameters):
        """
        Formats the facet information so that the Django template system can easily read it.
        """
        available_facets = available_cluster_facets if self.search_type == 'clusters' else available_hit_facets
        facets = []
        facet_params = parameters['fq']
        selected_facets = {}
        if facet_params:
            for selected_facet_param in facet_params:
                key, value = selected_facet_param.split(":", 1)
                selected_facets[key] = value.strip('"')
        
        for facet in available_facets:
            data_facets = data.facets['facet_fields'][facet['field']]
            facet_options = [{'name': data_facets[i], 'value': data_facets[i+1], 'selected': False} for i in range(0,len(data_facets), 2) if data_facets[i+1] > 0]
            facet_selected = False
            if facet['field'] in selected_facets:
                facet_options = [facet_option for facet_option in facet_options if facet_option['name'] == selected_facets[facet['field']]]
                facet_options[0]['selected'] = True
                facet_selected = True
            facets.append({'field': facet['field'], 'name': facet['name'], 'options': facet_options, 'has_selection': facet_selected})
        return facets

    def _format_data(self, data, parameters, request):
        """

        """
        formatted_data = self._format_hit_data(data['hits'], parameters['hits'], request)
        if 'metadata' in parameters:
            formatted_data.update(self._format_metadata(data['metadata'], parameters['metadata'], request))
        return formatted_data

    def _format_hit_data(self, data, parameters, request):
        """
        Receives the data from the interactor and formats it in a format that can be returned to the client.
        That is, data that can be rendered with the requested template.
        """
        results = []
        data_results = data
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [(hit_field_mapping[field], field, result[field]) for field in fields if field in hit_field_mapping]
            results.append(values)
        parameters.update({
        })
        site_parameters = {k: v for k, v in parameters.items() if v != None and v != []}
        formatted_data = {
            'results': results,
            'facets': self._format_facets(data, parameters),
            'parameters': parameters,
            'site_parameters': site_parameters,
            'total_results': data.raw_response['response']['numFound'],
            'next_page_start': min(parameters['start'] + parameters['rows'], data.raw_response['response']['numFound']),
            'prev_page_start': max(0, parameters['start'] - parameters['rows']),
            'start_num_pagination': parameters['start'] + 1,
            'end_num_pagination': parameters['start'] + parameters['rows'],
            'search_type': self.search_type,
        }
        return formatted_data

    def _format_metadata(self, data, parameters, request):
        """

        """
        results = []
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [(cluster_field_mapping[field], field, result[field]) for field in fields if field in cluster_field_mapping]
            results.append(values)

        formatted_data = {
            'show_metadata': True,
            'cluster_metadata': results[0],
            'current_cluster': parameters['fq'][0].split(":", 1)[1].replace("cluster_", ""),
        }

        return formatted_data
