"""
This class houses all the necessary functionality to handle the requested data.
Acts as a sort of a middle man, where the API endpoints ask for the data given the request parameters.
Rather than asking for the necessary data from indexed search engine (Solr), it formats the parameters
and asks a Interactor to fetch the data.
"""
import json
from operator import itemgetter

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
        {'field': 'crossed', 'name': 'Span across multiple countries'},
        # {'field': 'title', 'name': 'Title'},
        ]

available_hit_sort_options = [
        {'field': 'title', 'name': 'Sort by title, ascending', 'direction': 'asc'},
        {'field': 'title', 'name': 'Sort by title, descending', 'direction': 'desc'},
        {'field': 'date', 'name': 'Sort by date, ascending', 'direction': 'asc'},
        {'field': 'date', 'name': 'Sort by date, descending', 'direction': 'desc'},
        {'field': 'country', 'name': 'Sort by country, ascending', 'direction': 'asc'},
        {'field': 'country', 'name': 'Sort by country, descending', 'direction': 'desc'},
        {'field': 'location', 'name': 'Sort by location, ascending', 'direction': 'asc'},
        {'field': 'location', 'name': 'Sort by location, descending', 'direction': 'desc'},
        {'field': 'year', 'name': 'Sort by year, ascending', 'direction': 'asc'},
        {'field': 'year', 'name': 'Sort by year, descending', 'direction': 'desc'},
]

available_cluster_sort_options = [
        {'field': 'starting_title', 'name': 'Sort by title, ascending', 'direction': 'asc'},
        {'field': 'starting_title', 'name': 'Sort by title, descending', 'direction': 'desc'},
]

available_rows_per_page_options = [
        {'name': '5 per page', 'value': 5},
        {'name': '10 per page', 'value': 10},
        {'name': '20 per page', 'value': 20},
        {'name': '50 per page', 'value': 50},
]

hit_field_mapping = {
        'cluster_id': 'Cluster ID',
        'doc_id': 'Document ID',
        # 'id': 'ID',
        'text': 'Text',
        'title': 'Title',
        'date': 'Date',
        'url': 'URL',
        'country': 'Country',
        'location': 'Location',
        'year': 'Year',
}

cluster_field_mapping = {
        'cluster_id': 'Cluster ID',
        'doc_id': 'Document ID',
        # 'id': 'ID',
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
        'crossed': 'Span across mulitiple countries',
        'out_city': 'From city',
        'out_country': 'From country',
        'in_city': 'To city',
        'in_country': 'To country',
        'first_text': 'Text from the first hit',
}

hit_field_mapping.update(cluster_field_mapping)

class DataHandler:

    def __init__(self, search_type):
        self.search_type = search_type
        self.hit_interactor = SolrInteractor(core='swe_v2')
        self.cluster_interactor = SolrInteractor(core='swe_v2_clusters')

    def fetch_request_data(self, request):
        """
        Given the request parameters inside the request, asks an Interactor for the necessary data and 
        formats it in the way the client asked.
        """
        parameters = self._extract_request_parameters(request)
        data = self._fetch_data(parameters)
        formatted_data = self._format_data(data, parameters, request)
        urls = self._generate_site_urls(formatted_data, parameters, request)
        formatted_data.update({'urls': urls})
        return formatted_data

    def _extract_request_parameters(self, request):
        """
        Extracts the HTTP GET request parameters from the request object and returns them as a dictionary.
        """
        default_params = {
                'q': request.GET.get('q') if request.GET.get('q') else '',
                'start': int(request.GET.get('start', 0)),
                'rows': int(request.GET.get('rows', 10)),
                'fq': json.loads(request.GET.get('fq', "[]")),
                'sort': request.GET.get('sort', None),
                'hl': 'true',
                'hl.fl': 'text',
                'facet': 'true',
                'facet.field': [facet['field'] for facet in available_hit_facets],
        }
        if  self.search_type == 'hits':
            return {'hits': default_params}
        elif self.search_type ==  'clusters':
            cluster_params = default_params
            cluster_params['hl.fl'] = 'first_text'
            cluster_params['facet.field'] = [facet['field'] for facet in available_cluster_facets]
            return {'hits': cluster_params}
        elif self.search_type ==  'cluster':
            default_params['q'] = '*:*' if not default_params['q'] else default_params['q']
            cluster_params = {}
            cluster_params['q'] = '*:*'
            cluster_params['fq'] = [fq for fq in default_params['fq'] if fq.split(":")[0] == 'cluster_id']
            print(cluster_params)
            params = {
                'hits': default_params,
                'metadata': cluster_params,
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
        ids = []
        data_results = data
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [[hit_field_mapping[field], field, result[field]] for field in fields if field in hit_field_mapping]
            results.append(values)
            ids.append(result['id'])
        parameters.update({
        })
        site_parameters = {k: v for k, v in parameters.items() if v != None and v != []}
        # import pdb;pdb.set_trace()
        formatted_data = {
            'results': self._add_highlighting(results, ids, data),
            'facets': self._format_facets(data, parameters),
            'sort_options': self._format_sort_options(data, parameters),
            'rows_per_page_options': self._format_rows_per_page_options(data, parameters),
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

    def _add_highlighting(self, results, ids, data):
        """
        Replaces the necessary parts of results with the highlighted data.
        """
        if 'highlighting' in data.raw_response:
            highlighting_data = data.raw_response['highlighting']
            for result_i, result in enumerate(results):
                result_id = ids[result_i]
                highlights = highlighting_data[result_id]
                for key, value in highlights.items():
                    for highlighting in value:
                        non_highlighted = highlighting.replace("<em>", "").replace("</em>", "")
                        for res_i, res in enumerate(result):
                            if res[1] == key:
                                result[res_i][2] = result[res_i][2].replace(non_highlighted, highlighting)
        return results

    def _format_sort_options(self, data, parameters):
        """
        Formats the currently available sort options for django templates.
        Determines available sort options by the search_type.
        """
        options = []
        if self.search_type == 'clusters':
            sort_options = available_cluster_sort_options
        else:
            sort_options = available_hit_sort_options
        return sort_options

    def _format_rows_per_page_options(self, data, parameters):
        """
        Formats the currently available rows per page options for django templates.
        """
        return available_rows_per_page_options




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



    def _generate_site_urls(self, data, parameters, request):
        """
        Generates the URLS for facets, search etc.
        """
        current_url_parameters = request.GET
        urls = {}
        urls['facets'] = self._generate_site_urls_facets(current_url_parameters, data)
        urls['pagination'] = self._generate_site_urls_pagination(current_url_parameters, data)
        urls['cluster_links'] = self._generate_site_urls_cluster_links(current_url_parameters, data)
        urls['sort_options'] = self._generate_site_urls_sort_options(current_url_parameters, data)
        urls['rows_per_page_options'] = self._generate_site_urls_rows_per_page_options(current_url_parameters, data)
        urls['search_type'] = self._generate_site_urls_change_search_type(current_url_parameters, data)
        urls['result_type'] = self._generate_site_urls_change_result_type(current_url_parameters, data)
        return urls


    def _generate_site_urls_change_search_type(self, current_url_parameters, data):
        """
        Generates URLs to change the site between hits and clusters searches.
        """
        hits_params = dict(current_url_parameters)
        clusters_params = dict(current_url_parameters)
        if self.search_type == 'cluster':
            clusters_params['fq'] = []
            clusters_params['sort'] = ''
            hits_params['fq'] = []
            hits_params['sort'] = ''
        elif self.search_type == 'hits':
            clusters_params['fq'] = []
            clusters_params['sort'] = ''
        else:
            hits_params['fq'] = []
            hits_params['sort'] = ''
        hits_search_type = self._generate_site_url(hits_params, search_type='hits')
        clusters_search_type = self._generate_site_url(clusters_params, search_type='clusters')
        return {'hits': hits_search_type, 'clusters': clusters_search_type}
            

    def _generate_site_urls_change_result_type(self, current_url_parameters, data):
        """
        Generates URLs to change between showing cluster texts or charts.
        """
        clusters_url = self._generate_site_url(current_url_parameters, result_type='search')
        charts_url = self._generate_site_url(current_url_parameters, result_type='charts')
        return {'clusters': clusters_url, 'charts': charts_url}


    def _generate_site_urls_cluster_links(self, current_url_parameters, data):
        """
        Generates links to all cluster_id fields to show that particular cluster.
        Generates a list where the index matches the result list data['results']
        """
        urls = []
        for result in data['results']:
            for field in result: #field = [UI string, field name, value]
                if field[1] == 'cluster_id': 
                    url_params = dict(current_url_parameters)
                    url_params['q'] = ''
                    url_params['fq'] = ['{}:{}'.format("cluster_id", field[2])]
                    urls.append(self._generate_site_url(url_params, search_type='cluster'))
        return urls

    def _generate_site_urls_facets(self, current_url_parameters, data):
        """
        Generates the URLS for any facet links.
        Generates a list where the index matches the facet list data['facets']
        """
        current_url_parameters = dict(current_url_parameters)
        facet_urls = []
        if 'start' in current_url_parameters:
            del current_url_parameters['start']
        for facet in data['facets']:
            single_facet_urls=[]
            if facet['has_selection']:
                for option in facet['options']:
                    if option['selected']: # Found the selected option
                        facet_params = dict(current_url_parameters)
                        facet_params['fq'] = json.loads(facet_params['fq'][0])
                        for i in range(0, len(facet_params['fq'])):
                            if facet_params['fq'][i].split(":", 1)[0] == facet['field']:
                                facet_params['fq'].pop(i)
                                break
                        single_facet_urls.append(self._generate_site_url(facet_params))
                    else: # Not selected option = URL doesn't really matter as it isn't show anyways
                        single_facet_urls.append(self._generate_site_url(current_url_parameters))
            else:
                for option in facet['options']:
                    facet_params = dict(current_url_parameters)
                    if 'fq' in facet_params:
                        facet_params['fq'] = json.loads(facet_params['fq'][0])
                    else:
                        facet_params['fq'] = []
                    facet_params['fq'].append('{}:{}'.format(facet['field'], option['name']))
                    single_facet_urls.append(self._generate_site_url(facet_params))
            facet_urls.append(single_facet_urls)
        return facet_urls
        

    def _generate_site_urls_pagination(self, current_url_parameters, data):
        """
        Generates the URLs for previous and next page links
        """
        start = int(current_url_parameters.get('start', 0))
        rows_per_page = int(current_url_parameters.get('rows', 10))
        prev_page = max(start-rows_per_page, 0)
        prev_page_params = {}
        prev_page_params.update(current_url_parameters)
        prev_page_params['start'] = prev_page
        prev_page_url = self._generate_site_url(prev_page_params)
        next_page = start+rows_per_page
        next_page = min(next_page, data['total_results']-1)
        next_page_params = {}
        next_page_params.update(current_url_parameters)
        next_page_params['start'] = next_page
        next_page_url = self._generate_site_url(next_page_params)
        return {'previous_page': prev_page_url, 'next_page': next_page_url}

    def _generate_site_urls_sort_options(self, current_url_parameters, data):
        """
        Generates the URLs for sort options.
        Generates a list where the index matches the facet list data['sort_options']
        """
        urls = []
        for sort_option in data['sort_options']:
            params = dict(current_url_parameters)
            params['sort'] = "{} {}".format(sort_option['field'], sort_option['direction'])
            urls.append(self._generate_site_url(params))
        return urls

    def _generate_site_urls_rows_per_page_options(self, current_url_parameters, data):
        """
        Generates the URLs for deciding how many results are shown per page.
        """
        urls = []
        for option in data['rows_per_page_options']:
            params = dict(current_url_parameters)
            params['rows'] = option['value']
            urls.append(self._generate_site_url(params))
        return urls


    def _generate_site_url(self, parameters, search_type=None, result_type=None):
        """
        Given a dict of parameters, generates a URL
        """
        params = []
        for param, value in parameters.items():
            if not value: continue
            if type(value) == list:
                if param == 'fq':
                    value = json.dumps(value)
                else:
                    value = value[0]
            params.append([param, value])
        params.sort(key=itemgetter(0))
        params = ["=".join([str(param), str(value)]) for param, value in params]
        search_type = search_type if search_type else self.search_type #Use current search_type if not specified by function call
        result_type = result_type if result_type else 'search'
        if params:
            url = "/{}/{}?{}".format(search_type, result_type, "&".join(params))
        else:
            url = "/{}/{}".format(search_type, result_type)
        return url



class Charter:

    def __init__(self):
        pass

    def chart(self, data):
        """
        Generates a chart from the given query.
        """
        values = []
        labels, values, name = [], [], ''
        for facet in data['facets']:
            if facet['field'] == 'year':
                for option in facet['options']:
                    year = int(option['name'])
                    value = int(option['value'])
                    values.append([year, value])
                if values:
                    values.sort(key=itemgetter(0))
                    labels, values = list(zip(*values))
                    name = '# of hits per year'
                break
            if facet['field'] == 'starting_year':
                for option in facet['options']:
                    year = int(option['name'])
                    value = int(option['value'])
                    values.append([year, value])
                if values:
                    values.sort(key=itemgetter(0))
                    labels, values = list(zip(*values))
                    name = '# of clusters per year'
                break
        return labels, values, name
