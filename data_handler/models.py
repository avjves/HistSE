"""
This class houses all the necessary functionality to handle the requested data.
Acts as a sort of a middle man, where the API endpoints ask for the data given the request parameters.
Rather than asking for the necessary data from indexed search engine (Solr), it formats the parameters
and asks a Interactor to fetch the data.
"""
import json

from solr_interactor.models import SolrInteractor

available_facets = [
        {'field': 'title', 'name': 'Title'},
        {'field': 'year', 'name': 'Year of apperance'},
]

field_mapping = {
        'cluster_id': 'Cluster ID',
        'doc_id': 'Document ID',
        'id': 'ID',
        'text': 'Text',
        'title': 'Title',
        'year': 'Year of apperance',
}


class DataHandler:

    def __init__(self):
        self.interactor = SolrInteractor(core='swe_v2')
        # self.available_facets = AvailableFacets()


    def fetch_request_data(self, request):
        """
        Given the request parameters inside the request, asks an Interactor for the necessary data and 
        formats it in the way the client asked.
        """
        parameters = self._extract_request_parameters(request)
        print("Extracted parameters", parameters)
        data = self.interactor.fetch_data(parameters)
        return self._format_data(data, parameters)



    def _extract_request_parameters(self, request):
        """
        Extracts the HTTP GET request parameters from the request object and returns them as a dictionary.
        """
        params = {
            'q': request.GET.get('q', ''),
            'start': int(request.GET.get('start', 0)),
            'rows': int(request.GET.get('rows', 10)),
            'fq': json.loads(request.GET.get('fq', "[]")),
            'facet': 'true',
            'facet.field': [facet['field'] for facet in available_facets]
        }
        return params

    def _format_facets(self, data, parameters):
        """
        Formats the facet information so that the Django template system can easily read it.
        """
        facets = []
        facet_params = parameters['fq']
        selected_facets = {}
        if facet_params:
            for selected_facet_param in facet_params:
                key, value = selected_facet_param.split(":", 1)
                selected_facets[key] = value.strip('"')
        
        print(selected_facets)
        for facet in available_facets:
            data_facets = data.facets['facet_fields'][facet['field']]
            facet_options = [{'name': data_facets[i], 'value': data_facets[i+1], 'selected': False} for i in range(0,len(data_facets), 2) if data_facets[i+1] > 0]
            facet_selected = False
            if facet['field'] in selected_facets:
                facet_options = [facet_option for facet_option in facet_options if facet_option['name'] == selected_facets[facet['field']]]
                facet_options[0]['selected'] = True
                facet_selected = True
            facets.append({'field': facet['field'], 'name': facet['name'], 'options': facet_options, 'has_selection': facet_selected})
        print(facets)
        return facets



    def _format_data(self, data, parameters):
        """
        Receives the data from the interactor and formats it in a format that can be returned to the client.
        That is, data that can be rendered with the requested template.
        """
        results = []
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [(field_mapping[field], field, result[field]) for field in fields if field in field_mapping]
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
        }
        return formatted_data
