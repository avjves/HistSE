import pysolr

class SolrInteractor:

    def __init__(self, core, host="http://localhost", port=8983):
        solr_address = "{}:{}/solr/{}/".format(host, port, core)
        self.solr = pysolr.Solr(solr_address)

    def _do_bogus_search(self, params):
        """
        Does a random search which *hopefully* doesn't match anything.
        Used to quickly make a SOLR response with no data in it.
        """
        print("bogus ran!")
        params['q'] = 'qweifjöewfjaewiofjewiföjaweofiöjwaeöfoiwryuopioasdfhjl234'
        return self.solr.search(**params)


    def fetch_data(self, parameters):
        """
        Given the parameters, fetches the data from the Solr instance.
        """
        solr_parameters = self._filter_parameters(parameters)
        print("Solr parameters", solr_parameters)
        try:
            data = self.solr.search(**solr_parameters)
        except pysolr.SolrError:
            return self._do_bogus_search(solr_parameters)
        return data

    def _filter_parameters(self, parameters):
        """
        Goes through the parameters and deletes any parameters that it can't handle.
        """
        new_parameters = {}
        for parameter_key, parameter_value in parameters.items():
            if parameter_value == None:
                continue
            if parameter_key == 'fq':
                new_facet_fields = []
                for facet_field in parameter_value:
                    field, value = facet_field.split(":", 1)
                    value = value.replace("'", '"')
                    facet_field = '{}:"{}"'.format(field, value) 
                    new_facet_fields.append(facet_field)
                parameter_value = new_facet_fields
            if parameter_key == 'sort':
                parameter_value = parameter_value.replace("_asc", " asc").replace("_desc", " desc")

            new_parameters[parameter_key] = parameter_value
        return new_parameters
