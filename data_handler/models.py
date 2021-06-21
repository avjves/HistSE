"""
This class houses all the necessary functionality to handle the requested data.
Acts as a sort of a middle man, where the API endpoints ask for the data given the request parameters.
Rather than asking for the necessary data from indexed search engine (Solr), it formats the parameters
and asks a Interactor to fetch the data.
"""
import json
import html
from operator import itemgetter
from geopy import geocoders

from django.conf import settings

from solr_interactor.models import SolrInteractor
from HistSE.data_config import available_hit_facets, available_cluster_facets, skipped_hit_fields, skipped_metadata_fields
from HistSE.data_config import available_hit_sort_options, available_cluster_sort_options, available_rows_per_page_options
from HistSE.data_config import hit_field_mapping, cluster_field_mapping
from HistSE import data_config
### TODO dont import the field configs explicitly

field_mapping = {}
field_mapping.update(hit_field_mapping)
field_mapping.update(cluster_field_mapping)

class DataHandler:

    def __init__(self, search_type, result_type, extra_args={}):
        self.search_type = search_type
        self.result_type = result_type
        self.extra_args = extra_args
        self.hit_interactor = SolrInteractor(core='swe_v10', use_cache=False)
        self.cluster_interactor = SolrInteractor(core='swe_v10_clusters', use_cache=False)

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

    def fetch_all_data(self, request, fields, data_type, field_override=None):
        """
        Fetches _all_ the data with the given parameters.
        Does not generate facets or URLs.
        """
        parameters = self._extract_request_parameters(request)
        parameters[data_type]['facet'] = 'false'
        parameters[data_type]['hl'] = 'false'
        parameters[data_type]['start'] = 0
        parameters[data_type]['rows'] = 1000
        parameters[data_type]['fl'] = ",".join(fields)
        total_results = 0
        found_results = 0
        all_data = {}
        while True:
            data = self._fetch_data(parameters)[data_type]
            parameters[data_type]['start'] = parameters[data_type]['start'] + parameters[data_type]['rows'] # Next iteration asks for different data
            for result in data:
                found_results += 1

                if field_override:
                    fields = hit_field_mapping.keys() if field_override == 'hits' else cluster_field_mapping.keys()
                else:
                    fields = hit_field_mapping.keys() if data_type == 'hits' else cluster_field_mapping.keys()

                for field in fields:
                    all_data[field] = all_data.get(field, [])
                    all_data[field].append(result.get(field, None))

            if not found_results:
                break
            if found_results > 50000: break
        return all_data

    def _extract_request_parameters(self, request):
        """
        Extracts the HTTP GET request parameters from the request object and returns them as a dictionary.
        Also sets any default parameters that should be passed to Solr.
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
                'facet.limit': -1,
        }
        if  self.search_type == 'hits':
            params = dict(default_params)
            params['sort'] = params['sort'] if params['sort'] else 'date asc'
            return {'hits': params}
        elif self.search_type ==  'clusters':
            cluster_params = default_params
            cluster_params['hl.fl'] = 'first_text'
            cluster_params['facet.field'] = [facet['field'] for facet in available_cluster_facets]
            cluster_params['sort'] = cluster_params['sort'] if cluster_params['sort'] else 'starting_date asc'
            return {'hits': cluster_params}
        elif self.search_type ==  'cluster':
            default_params['q'] = '*:*' if not default_params['q'] else default_params['q']
            default_params['sort'] = default_params['sort'] if default_params['sort'] else 'date asc'
            cluster_params = {}
            cluster_params['q'] = '*:*'
            cluster_params['fq'] = [fq for fq in default_params['fq'] if fq.split(":")[0] == 'cluster_id']
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
                selected_facets[key] = selected_facets.get(key, [])
                selected_facets[key].append(value.strip('"'))
        for facet in available_facets:
            facet_type = facet.get('facet_type', 'entry_per_value')
            if facet_type == 'entry_per_value':
                facet_option = self._format_facets_entry_per_value(data, parameters, facet, selected_facets)
                facets.append(facet_option)
            elif facet_type == 'range_selector':
                facet_option = self._format_facets_range_limit(data, parameters, facet, selected_facets)
                facets.append(facet_option)
        return facets

    def _format_facets_entry_per_value(self, data, parameters, facet, selected_facets):
        """
        In place additions
        """
        facet_options = self._format_facets_default(data, parameters, facet)
        facet_selected = False
        negative_facet_selected = False
        if facet['field'] in selected_facets:
            facet_options = [facet_option for facet_option in facet_options if facet_option['name'] in selected_facets[facet['field']]]
            facet_options[0]['selected'] = True
            facet_selected = True
        if '-' + facet['field'] in selected_facets:
            negative_facet_options = [{'name': name, 'gui_name': name, 'value': 0, 'selected': False, 'unselected': True} for name in selected_facets['-' + facet['field']]]
            facet_options += negative_facet_options
            negative_facet_selected = True
        facet_options.sort(key=itemgetter('value'), reverse=True)
        return {'field': facet['field'], 'name': facet['name'], 'options': facet_options, 'has_selection': facet_selected, 'has_negative_selection': negative_facet_selected, 'facet_type': 'entry_per_value', 'visible': facet['visible']}


    def _format_facets_default(self, data, parameters, facet):
        """
        Generates the default facet value options so that stuff like chart works even if they are not used to populate
        the facet window.
        """
        data_facets = data.facets['facet_fields'][facet['field']]
        option_names = facet.get('option_names', {})
        facet_options = [{'name': data_facets[i], 'gui_name': option_names.get(data_facets[i], data_facets[i]), 'value': data_facets[i+1], 'selected': False} for i in range(0,len(data_facets), 2) if data_facets[i+1] > 0]
        return facet_options


    def _format_facets_range_limit(self, data, parameters, facet, selected_facets):
        """
        Range limited facets
        Attemps to create some values that can be charted and shown to user.
        """
        entry_facet = {'field': facet['field'], 'name': facet['name'], 'facet_type': 'range_selector', 'has_selection': False, 'options': self._format_facets_default(data, parameters, facet), 'visible': facet['visible']}
        data_facets = data.facets['facet_fields'][facet['field']]
        facet_options = [{'name': data_facets[i], 'value': data_facets[i+1], 'selected': False} for i in range(0,len(data_facets), 2) if data_facets[i+1] > 0]
        facet_values = []
        for i in range(0, len(data_facets), 2):
            if data_facets[i+1] < 1: continue
            facet_values.append([int(data_facets[i]), int(data_facets[i+1])])
        facet_values.sort(key=itemgetter(0))
        if not facet_values:
            return entry_facet
        min_value = facet_values[0][0]
        max_value = facet_values[-1][0]
        facet_labels = [v[0] for v in facet_values]
        facet_values = [v[1] for v in facet_values]
        charter = Charter()
        data_labels, data_values = charter.chart_bucket_range(facet_labels, facet_values, bucket_size=facet['increment'])
        entry_facet['min_value'] = min_value
        entry_facet['max_value'] = max_value
        entry_facet['data_labels'] = data_labels
        entry_facet['data_values'] = data_values
        if facet['field'] in selected_facets:
            entry_facet['current_selection'] = "FROM " + selected_facets[facet['field']][0].strip("[").strip("]")
            entry_facet['has_selection'] = True
        return entry_facet

    def _format_data(self, data, parameters, request):
        """
        Returns a formatted data dictionary.
        Adds hit AND metadata specific data fields.
        Metadata only added if metadata key is found inside parameters.
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
            values = [[field_mapping[field], field, self._enrich_hit_result(result[field], field, parameters)] for field in fields if field in field_mapping]
            results.append(values)
            ids.append(result['id'])
        parameters.update({
        })
        site_parameters = {k: v for k, v in parameters.items() if v != None and v != []}
        formatted_data = {
            'results': self._add_highlighting(results, ids, data),
            'facets': self._format_facets(data, parameters),
            'sort_options': self._format_sort_options(parameters),
            'current_sort_option': self._format_current_sort_option(parameters),
            'rows_per_page_options': self._format_rows_per_page_options(parameters),
            'current_rows_per_page_option': self._format_current_rows_per_page_option(parameters),
            'parameters': parameters,
            'site_parameters': site_parameters,
            'total_results': data.raw_response['response']['numFound'],
            'next_page_start': min(parameters['start'] + parameters['rows'], data.raw_response['response']['numFound']),
            'prev_page_start': max(0, parameters['start'] - parameters['rows']),
            'start_num_pagination': parameters['start'] + 1,
            'end_num_pagination': parameters['start'] + parameters['rows'],
            'search_type': self.search_type,
            'result_type': self.result_type,
        }
        for key, value in self.extra_args.items():
            formatted_data[key] = value

        return formatted_data

    def _enrich_hit_result(self, data, field, parameters):
        """
        Enriches certain results received from Solr.
        Different fields have their own enrich functions.
        """
        try:
            if field == 'url':
                return self._enrich_hit_result_url(data, parameters)
            else:
                return data
        except:  # In case something weird happens we just return the result without any enriching -  it's better than crashing!
            return data

    def _enrich_hit_result_url(self, data, parameters):
        """
        Enriches the received URL. 
        For now, adds the query term to Kansalliskirjasto URLs.
        """
        if data_config.enrich_kansalliskirjasto_URLs and 'kansalliskirjasto' in data:
            ## For now, assuming the user will have a text: query in the query field OR no : (No field specified = default search = text field)
            if ":" not in parameters['q']:
                # : not found in query, assuming everything in the query field is the desired highlight.
                url = data + '&term={}'.format(parameters['q'])
            elif "text:" in parameters['q']:
                # text: found in the query. Attempting two things: 1. see if the q is wrapped in quotes or 2. take first word
                query = parameters['q'].split("text:", 1)[1]  
                if query[0] == '"': # Wrapped in quotes? Probably
                    query = query.split('"')[1]
                else:
                    query = query.split(" ")[0]
                url = data + '&term={}'.format(query)
            else:
                url = data
            return url
        else:
            return data

    def _format_current_sort_option(self, parameters):
        """
        Returns the current sort option used.
        Returns it as a dictionary.
        """
        sort_options = self._format_sort_options(parameters)
        for option in sort_options:
            if option['field'] + ' ' + option['direction'] == parameters['sort'].replace("_asc", " asc").replace("_desc", " desc"):
                return option
        return {'name': ''} # Should hopefully never go here - would mean a sort option was not found.

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

    def _format_sort_options(self, parameters):
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

    def _format_rows_per_page_options(self, parameters):
        """
        Formats the currently available rows per page options for django templates.
        """
        return available_rows_per_page_options

    def _format_current_rows_per_page_option(self, parameters):
        """
        Returns the current rows per page option.
        """
        available_row_options = self._format_rows_per_page_options(parameters)
        for option in available_row_options:
            if option['value'] == parameters['rows']:
                return option
        return available_row_options[0] # Should hopefully never go here either



    def _format_metadata(self, data, parameters, request):
        """
        Receives the data from the interactor and formats it in a format that can be returned to the client.
        That is, data that can be rendered with the requested template.
        Equivalent to the _format_hit function, but all fields etc. are metadata specific.
        """
        results = []
        for result in data:
            fields = list(result.keys())
            fields.sort()
            values = [(cluster_field_mapping[field], field, result[field]) for field in fields if field in cluster_field_mapping and field not in skipped_metadata_fields]
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
        urls['result_type'] = self._generate_site_urls_change_result_type(current_url_parameters, data, request)
        urls['flowmap'] = self._generate_site_urls_flowmap(current_url_parameters, data)
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
            

    def _generate_site_urls_change_result_type(self, current_url_parameters, data, request):
        """
        Generates URLs to change between showing cluster texts or charts.
        """
        clusters_url = self._generate_site_url(current_url_parameters, result_type='search')
        charts_url = self._generate_site_url(current_url_parameters, result_type='charts/absolute/year')
        # charts_url = self._generate_site_url(current_url_parameters, result_type='charts')
        download_url = self._generate_site_url(current_url_parameters, result_type='download')
        map_origin_url = self._generate_site_url(current_url_parameters, result_type='origin/map')
        map_chain_url = self._generate_site_url(current_url_parameters, result_type='chain/map')
        urls = {'clusters': clusters_url, 'charts': charts_url, 'map_origin': map_origin_url, 'map_chain': map_chain_url, 'download': download_url}
        ### Chart options
        current_norm_type = 'absolute' if 'absolute' in request.path else 'normalized'
        current_scope_type = 'year' if 'year' in request.path else 'month'
        urls['charts_norm_absolute'] = self._generate_site_url(current_url_parameters, result_type='charts/{}/{}'.format('absolute', current_scope_type))
        urls['charts_norm_normalized'] = self._generate_site_url(current_url_parameters, result_type='charts/{}/{}'.format('normalized', current_scope_type))
        urls['charts_scope_year'] = self._generate_site_url(current_url_parameters, result_type='charts/{}/{}'.format(current_norm_type, 'year'))
        urls['charts_scope_month'] = self._generate_site_url(current_url_parameters, result_type='charts/{}/{}'.format(current_norm_type, 'month'))
        return urls



    def _generate_site_urls_cluster_links(self, current_url_parameters, data):
        """
        Generates links to all cluster_id fields to show that particular cluster.
        Generates a list where the index matches the result list data['results']
        """
        urls = []
        for result in data['results']:
            for field in result: #field = [UI string, field name, value]
                if field[1] == 'cluster_id': 
                    new_params = {}
                    new_params['q'] = ''
                    new_params['fq'] = ['{}:{}'.format("cluster_id", field[2])]
                    urls.append(self._generate_site_url(new_params, search_type='cluster'))
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
                facet_type = facet['facet_type']
                if facet_type == 'entry_per_value':
                    for option in facet['options']:
                        if option['selected']: # Found the selected option
                            facet_params = dict(current_url_parameters)
                            facet_params['fq'] = json.loads(facet_params['fq'][0])
                            for i in range(0, len(facet_params['fq'])):
                                if facet_params['fq'][i].split(":", 1)[0] == facet['field']:
                                    facet_params['fq'].pop(i)
                                    break
                            single_facet_urls.append({'selected': self._generate_site_url(facet_params)})
                        elif option['unselected']:
                            facet_params = dict(current_url_parameters)
                            facet_params['fq'] = json.loads(facet_params['fq'][0])
                            for i in range(0, len(facet_params['fq'])):
                                if facet_params['fq'][i].split(":", 1)[0] == '-' + facet['field']:
                                    facet_params['fq'].pop(i)
                                    break
                            single_facet_urls.append({'previous': self._generate_site_url(facet_params)})
                        else: # Not selected option = URL doesn't really matter as it isn't show anyways
                            # single_facet_urls.append(self._generate_site_url(current_url_parameters))
                            single_facet_urls.append({'selected': ''})
                elif facet_type == 'range_selector':
                    facet_params = dict(current_url_parameters)
                    facet_params['fq'] = json.loads(facet_params['fq'][0])
                    for i in range(0, len(facet_params['fq'])):
                        if facet_params['fq'][i].split(":", 1)[0] == facet['field']:
                            facet_params['fq'].pop(i)
                            break
                    single_facet_urls.append(self._generate_site_url(facet_params))
            else:
                for option in facet['options']:
                    facet_params = dict(current_url_parameters)
                    if 'fq' in facet_params:
                        facet_params['fq'] = json.loads(facet_params['fq'][0])
                    else:
                        facet_params['fq'] = []
                    negative_facet_params = json.loads(json.dumps(facet_params))
                    previous_facet_params = json.loads(json.dumps(facet_params))
                    facet_params['fq'].append('{}:{}'.format(facet['field'], option['name']))
                    negative_facet_params['fq'].append('-{}:{}'.format(facet['field'], option['name']))
                    if '-{}:{}'.format(facet['field'], option['name']) in previous_facet_params['fq']:
                        previous_facet_params['fq'].remove('-{}:{}'.format(facet['field'], option['name']))
                    single_facet_urls.append({'selected': self._generate_site_url(facet_params), 'unselected': self._generate_site_url(negative_facet_params), 'previous': self._generate_site_url(previous_facet_params)})
            facet_urls.append(single_facet_urls)
        return facet_urls
        

    def _generate_site_urls_pagination(self, current_url_parameters, data):
        """
        Generates the URLs for previous and next page links
        """
        prev_page_params = dict(current_url_parameters)
        next_page_params = dict(current_url_parameters)
        start = int(current_url_parameters.get('start', 0))
        rows_per_page = int(current_url_parameters.get('rows', 10))
        prev_page = max(start-rows_per_page, 0)
        prev_page_params['start'] = prev_page
        prev_page_url = self._generate_site_url(prev_page_params)
        next_page = start+rows_per_page
        next_page = min(next_page, data['total_results']-1)
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
            params['sort'] = "{}_{}".format(sort_option['field'], sort_option['direction'])
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

    def _generate_site_urls_flowmap(self, current_url_parameters, data):
        current_domain = settings.DOMAIN
        url = current_domain + self._generate_site_url(current_url_parameters, result_type='{}/map_data'.format(self.extra_args.get('flow_type', '')))
        # url = current_domain + self._generate_site_url(current_url_parameters, result_type='origin/map_data')
        loc_url = url.replace("/map", "/locations/map")
        flows_url = url.replace("/map", "/flows/map")
        access_token = 'pk.eyJ1IjoiYXZqdmVzIiwiYSI6ImNrbHR4YmllYTBoZG4yb213cGNnbzZicHYifQ.vSaa0xMyKGztHbahyM6h2A'
        flow_url = "https://flowmap.blue/from-url?flows={}&locations={}&mapbox.accessToken={}".format(flows_url, loc_url, access_token)
        return {'flow_map': flow_url}
        



    def _generate_site_url(self, parameters, search_type=None, result_type=None):
        """
        Given a dict of parameters, generates a URL
        """
        params = []
        for param, value in parameters.items():
            if not value: continue
            if type(value) == list:
                if param == 'fq':
                    try:
                        value = json.loads(value[0])
                    except ValueError:
                        pass
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

    def _enrich_site_urls_result_type(self, parameters, search_type, request):
        """
        Enriches urls used to change the result type.
        """
        if data_config.enrich_normalized_chart_values and search_type == 'charts':
            if bool(request.GET.get('normalization', '')):
                pass
        return parameters



class DataExporter:

    def __init__(self, data_handler):
        self.data_handler = data_handler

    def export_current_search(self, request, search_type):
        """
        Exports the current data as a TSV.
        Returns a list of lists = list of TSV lines.
        """
        if search_type == 'cluster':
            hit_data = self.data_handler.fetch_all_data(request, fields=['*'], data_type='hits')
            metadata_data = self.data_handler.fetch_all_data(request, fields=['*'], data_type='metadata')
        elif search_type == 'hits':
            hit_data = self.data_handler.fetch_all_data(request, fields=['*'], data_type='hits')
            metadata_data = {}
        else:
            hit_data = {}
            metadata_data = self.data_handler.fetch_all_data(request, fields=['*'], data_type='hits', field_override='clusters')
        
        hit_lines = self._extract_lines(hit_data)
        metadata_lines = self._extract_lines(metadata_data)
        lines = [['current URL', settings.DOMAIN + request.get_full_path().replace("/download?", "/search?")]]
        lines += [['Metadata / clusters'], []]
        lines += metadata_lines
        lines += [[], [], [], ['Hits'], []]
        lines += hit_lines
        return lines

    def _extract_lines(self, data):
        """
        Given a data dictionary, where each key represents a field name and the value is a list that contains as many values as there is to be TSV lines.
        Exports the data to a list of lists.
        """
        lines = []
        if data:
            fields = list(data.keys())
            lines.append(fields)
            for i in range(0, len(data[fields[0]])):
                line = []
                for field in fields:
                    if not data[field][i]:
                        line.append("")
                    else:
                        line.append(" ".join(str(data[field][i]).split()))
                lines.append(line)
        return lines




class Charter:

    def __init__(self):
        pass

    def chart(self, facets, normalization_type, date_scope, request):
        """
        Generates a chart from the given query.
        """
        values = []
        labels, values, name = [], [], ''
        for facet in facets: 
            if facet['field'] == 'year':
                for option in facet['options']:
                    year = int(option['name'])
                    value = int(option['value'])
                    year, value = self._enrich_label_data(year, value, normalization_type, date_scope, request)
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
                    year, value = self._enrich_label_data(year, value, normalization_type, date_scope, request)
                    values.append([year, value])
                if values:
                    values.sort(key=itemgetter(0))
                    labels, values = list(zip(*values))
                    name = '# of clusters starting per year'
                break
            if facet['field'] == 'month':
                for option in facet['options']:
                    month = option['name']
                    value = int(option['value'])
                    month, value = self._enrich_label_data(month, value, normalization_type, date_scope, request)
                    month = "_".join(month.split("_")[::-1])
                    values.append([month, value])
                if values:
                    values.sort(key=itemgetter(0))
                    labels, values = list(zip(*values))
                    name = '# of hits per month'
                break
            if facet['field'] == 'starting_month':
                for option in facet['options']:
                    month = int(option['name'])
                    value = int(option['value'])
                    month, value = self._enrich_label_data(month, value, normalization_type, date_scope, request)
                    month = "_".join(month.split("_")[::-1])
                    values.append([month, value])
                if values:
                    values.sort(key=itemgetter(0))
                    labels, values = list(zip(*values))
                    name = '# of clusters starting per month'
                break
        return labels, values, name

    def chart_bucket_range(self, labels, data, bucket_size):
        """
        Generates data for a chart with bucketed data / labels. 
        Buckets are formed from the labels.
        Assumes labels and data are both sorted timewise AND that their indexes match.
        """
        min_key = labels[0]
        max_key = labels[-1]
        if min_key == max_key: # No need to bucket stuff when we only have one year in data.
            return ["{} - {}".format(min_key, max_key)], [sum(data)]
        bucket_indexes = [(i, i+bucket_size) for i in range(min_key, max_key, bucket_size)]
        buckets = [[] for _ in bucket_indexes]
        cur_bi = 0
        for i in range(0, len(labels)):
            while True:
                if labels[i] <= bucket_indexes[cur_bi][1]:
                    buckets[cur_bi].append([labels[i], data[i]])
                    break
                else:
                    cur_bi += 1
                    continue

        new_labels, new_data = [], []
        for bucket_i, bucket in enumerate(buckets):
            new_labels.append("{} - {}".format(bucket_indexes[bucket_i][0], bucket_indexes[bucket_i][1]))
            new_data.append(sum([v[1] for v in bucket]))
        return new_labels, new_data

    def _enrich_label_data(self, label, value, normalization_type, date_scope, request):
        if data_config.enrich_normalized_chart_values and normalization_type == 'normalized':
            from data_handler.data_enrichment.year_normalization import year_multipliers
            if date_scope == 'year':
                value = round(value/year_multipliers[label]*10000, 4)
            else:
                month, year = label.split("_")
                value = round(value/year_multipliers[int(year)]*10000, 4)
            return label, value

        return label, value



class Mapper:
    def __init__(self, flow_type, data_type):
        self.gn = geocoders.GeoNames('avjves')
        self.flow_type = flow_type
        self.data_type = data_type

    def format_map_data(self, data):
        if self.data_type == 'flows':
            return self._format_map_data_flows(data)
        elif self.data_type == 'locations':
            return self._format_map_data_locations(data)
        else:
            raise NotImplementedError


    def _format_map_data_flows(self, data):
        csv_data = [['origin', 'dest', 'count']]
        dates = data['date']
        locations = data['location']
        # dates, locations = [list(a) for a in zip(*sorted(zip(dates, locations)))]
        if self.flow_type == 'origin':
            counts = {}
            orig_date, orig_loc = dates.pop(0), locations.pop(0)
            if orig_loc == "OUT OF SCOPE": return csv_data
            for date, location in zip(dates, locations):
                if location == "OUT OF SCOPE": continue
                counts[location] = counts.get(location, 0) + 1
            for key, value in counts.items():
                csv_data.append([orig_loc, key, value])
            return csv_data
        elif self.flow_type == 'chain':
            counts = {}
            cur_date, cur_loc = dates.pop(0), locations.pop(0)
            while dates:
                new_date, new_loc = dates.pop(0), locations.pop(0)
                loc_key = "{}|{}".format(cur_loc, new_loc)
                counts[loc_key] = counts.get(loc_key, 0) + 1
                cur_date = new_date
                cur_loc = new_loc
            for key, value in counts.items():
                start, end = key.split("|")
                csv_data.append([start, end, value])
            return csv_data
        else:
            raise NotImplementedError
         

    def _format_map_data_locations(self, data):
        csv_data = [['id', 'name', 'lat', 'lon']]
        dates = data['date']
        locations = data['location']
        coordinates = data['coordinates']
        dates, locations, coordinates = [list(a) for a in zip(*sorted(zip(dates, locations, coordinates)))]
        if self.flow_type == 'origin':
            date = dates.pop(0)
            location = locations.pop(0)
            coordinate_pair = coordinates.pop(0)
            if location == 'OUT OUF SCOPE': return csv_data
            # lat, lng = self._get_location_coordinates(location)
            lng, lat = coordinate_pair
            csv_data.append([location, location, lat, lng])
            found_locations = set([location])
            for (date, location, coordinate_pair) in zip(dates, locations, coordinates):
                if location not in found_locations:
                    found_locations.add(location)
                    if location == 'OUT OF SCOPE': continue
                    # lat, lng = self._get_location_coordinates(location)
                    lng, lat = coordinate_pair
                    if not lat: continue
                    csv_data.append([location, location, lat, lng])
            return csv_data
        elif self.flow_type == 'chain':
            found_locations = set()
            for (date, location, coordinate_pair) in zip(dates, locations, coordinates):
                    if location not in found_locations:
                        found_locations.add(location)
                        lng, lat = coordinate_pair
                        csv_data.append([location, location, lat, lng])
            return csv_data
        else:
            raise NotImplementedError

    def _get_location_coordinates(self, location_name):
        print(location_name)
        loc = self.gn.geocode(location_name)
        if not loc: return None, None
        print(loc)
        return loc.latitude, loc.longitude
