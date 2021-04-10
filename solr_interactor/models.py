import pysolr
import pickle
import json
import os

class SolrInteractor:

    def __init__(self, core, host="http://localhost", port=8983, use_cache=False):
        solr_address = "{}:{}/solr/{}/".format(host, port, core)
        self.use_cache = use_cache
        self.core = core
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
            data = self._search(parameters, self.use_cache)
        except pysolr.SolrError:

            return self._do_bogus_search(solr_parameters)
        return data

    def _fetch_cache(self, parameters):
        """
        Attempts to fetch the Solr results from a cache.
        Cache is defined by solr core name + hash of parameters.
        """
        cache_key = '{}-{}'.format(self.core, hash(json.dumps(parameters)))
        cache_path = 'solr_interactor/cache/{}.pkl'.format(cache_key)
        if os.path.exists(cache_path):
            return pickle.load(open(cache_path, 'rb'))
        else:
            return None

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
                    if value.startswith("["): # We don't add extra "s if it's a range selector.
                        new_facet_fields.append(facet_field)
                        continue
                    value = value.replace("'", '"')
                    facet_field = '{}:"{}"'.format(field, value) 
                    new_facet_fields.append(facet_field)
                parameter_value = " AND ".join(new_facet_fields)
            if parameter_key == 'sort':
                parameter_value = parameter_value.replace("_asc", " asc").replace("_desc", " desc")

            new_parameters[parameter_key] = parameter_value
        return new_parameters

    def _save_cache(self, results, parameters):
        """
        Saves the received results from solr into the cache.
        """
        cache_key = '{}-{}'.format(self.core, hash(json.dumps(parameters)))
        cache_path = 'solr_interactor/cache/{}.pkl'.format(cache_key)
        pickle.dump(results, open(cache_path, "wb"))

    def _search(self, parameters, use_cache):
        """
        Given the parameters, searches the Solr.
        Checks whether to use cache or not.
        If using cache but it still fails, runs a normal Solr search.
        """
        if use_cache:
            cache_results = self._fetch_cache(parameters)
            if not cache_results:
                solr_results = self._search(parameters, False)
                self._save_cache(solr_results, parameters)
                return solr_results
            else:
                return cache_results
        else:
            return self.solr.search(**parameters)

