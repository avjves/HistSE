"""
This class houses all the necessary functionality to handle the requested data.
Acts as a sort of a middle man, where the API endpoints ask for the data given the request parameters.
Rather than asking for the necessary data from indexed search engine (Solr), it formats the parameters
and asks a Interactor to fetch the data.
"""
from solr_interactor.models import SolrInteractor

class DataHandler:

    def __init__(self):
        self.interactor = SolrInteractor(core='swe_v2')


    def fetch_request_data(self, request):
        """
        Given the request parameters inside the request, asks an Interactor for the necessary data and 
        formats it in the way the client asked.
        """
        parameters = self._extract_request_parameters(request)
        data = self.interactor.fetch_data(parameters)
        return self._format_data(data, parameters)



    def _extract_request_parameters(self, request):
        """
        Extracts the HTTP GET request parameters from the request object and returns them as a dictionary.
        """
        params = {
            'q': request.GET.get('q', None),
            'start': int(request.GET.get('start', 0)),
            'rows': int(request.GET.get('rows', 10)),
        }
        return params


    def _format_data(self, data, parameters):
        """
        Receives the data from the interactor and formats it in a format that can be returned to the client.
        That is, data that can be rendered with the requested template.
        """
        results = []
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [(field, result[field]) for field in fields]
            results.append(values)
        parameters.update({
        })
        site_parameters = {k: v for k, v in parameters.items() if v is not None}
        formatted_data = {
            'results': results,
            'parameters': parameters,
            'site_parameters': site_parameters,
            'total_results': data.raw_response['response']['numFound'],
            'next_page_start': min(parameters['start'] + parameters['rows'], data.raw_response['response']['numFound']),
            'prev_page_start': max(0, parameters['start'] - parameters['rows']),
            'start_num_pagination': parameters['start'] + 1,
            'end_num_pagination': parameters['start'] + parameters['rows'],
        }
        return formatted_data
