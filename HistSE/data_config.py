"""

Contains all data related configs.

"""

####
#
# SETTINGS
#
####

enrich_kansalliskirjasto_URLs = True
enrich_tidningar_URLs = True
enrich_normalized_chart_values = True
enrich_map_coordinates = True

####
#
# FIELD INFORMATION
#
####

available_hit_facets = [
        {'field': 'title', 'name': 'Title', 'visible': True},
        {'field': 'year', 'name': 'Year of apperance', 'facet_type': 'range_selector', 'increment': 10, 'visible': True},
        {'field': 'month', 'name': 'Month of apperance', 'increment': 10, 'visible': False},
        {'field': 'location', 'name': 'Location', 'visible': True},
        {'field': 'country', 'name': 'Country', 'visible': True},
]

skipped_hit_fields = {}

skipped_metadata_fields = {'first_text'}

available_cluster_facets = [
        # {'field': 'starting_title', 'name': 'Starting title'},
        {'field': 'starting_country', 'name': 'Starting country', 'visible': True},
        {'field': 'starting_location', 'name': 'Starting location', 'visible': True},
        {'field': 'starting_year', 'name': 'Starting year of apperance', 'facet_type': 'range_selector', 'increment': 10, 'visible': True},
        {'field': 'crossed', 'name': 'Span across multiple countries', 'option_names': {'true': 'Yes', 'false': 'No'}, 'visible': True},
        {'field': 'out_city', 'name': 'Port city', 'visible': True},
        {'field': 'out_country', 'name': 'Port country', 'visible': True},
        {'field': 'in_city', 'name': 'Incoming city', 'visible': True},
        {'field': 'in_country', 'name': 'Incoming country', 'visible': True},
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
        {'field': 'average_length', 'name': 'Sort by average length, ascending', 'direction': 'asc'},
        {'field': 'average_length', 'name': 'Sort by average length, descending', 'direction': 'desc'},
        {'field': 'starting_date', 'name': 'Sort by starting date, ascending', 'direction': 'asc'},
        {'field': 'starting_date', 'name': 'Sort by starting date, descending', 'direction': 'desc'},
        {'field': 'ending_date', 'name': 'Sort by ending date, ascending', 'direction': 'asc'},
        {'field': 'ending_date', 'name': 'Sort by ending date, descending', 'direction': 'desc'},
        {'field': 'starting_country', 'name': 'Sort by starting country, ascending', 'direction': 'asc'},
        {'field': 'starting_country', 'name': 'Sort by starting country, descending', 'direction': 'desc'},
        {'field': 'starting_location', 'name': 'Sort by starting location, ascending', 'direction': 'asc'},
        {'field': 'starting_location', 'name': 'Sort by starting location, descending', 'direction': 'desc'},
        {'field': 'locations', 'name': 'Sort by number of unique locations, ascending', 'direction': 'asc'},
        {'field': 'locations', 'name': 'Sort by number of unique locations, descending', 'direction': 'desc'},
        {'field': 'starting_year', 'name': 'Sort by starting year, ascending', 'direction': 'asc'},
        {'field': 'starting_year', 'name': 'Sort by starting year, descending', 'direction': 'desc'},
        {'field': 'count', 'name': 'Sort by count, descending', 'direction': 'desc'},
        {'field': 'count', 'name': 'Sort by count, ascending', 'direction': 'asc'},
        {'field': 'timespan', 'name': 'Sort by span, ascending', 'direction': 'asc'},
        {'field': 'timespan', 'name': 'Sort by span, descending', 'direction': 'desc'},
        {'field': 'gap', 'name': 'Sort by gap, ascending', 'direction': 'asc'},
        {'field': 'gap', 'name': 'Sort by gap, descending', 'direction': 'desc'},
        {'field': 'virality_score', 'name': 'Sort by virality score, ascending', 'direction': 'asc'},
        {'field': 'virality_score', 'name': 'Sort by virality score, descending', 'direction': 'desc'},
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
        # 'doc_id': 'Document ID',
        # 'id': 'ID',
        'count': 'Count',
        'timespan': 'Timespan in days',
        'gap': 'Biggest gap within the cluster (years)',
        'locations': 'Unique locations',
        'average_length': 'Average length',
        'starting_title': 'Title',
        'starting_date': 'Starting date',
        'ending_date': 'Ending date',
        'ending_country': 'Ending Country',
        'starting_country': 'Country',
        'starting_location': 'First printing location',
        'starting_year': 'Starting year',
        'all_locations': 'All unique locations',
        'all_countries': 'All unique countries',
        'crossed': 'Span across multiple countries',
        'out_city': 'Port city',
        'out_country': 'Port country',
        'in_city': 'Incoming city',
        'in_country': 'Incoming country',
        'virality_score': 'Virality score',
        'first_text': 'Text from the first hit',
}


