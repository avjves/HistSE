import pysolr

class SolrInteractor:

    def __init__(self, core, host="http://localhost", port=8983):
        solr_address = "{}:{}/solr/{}/".format(host, port, core)
        self.solr = pysolr.Solr(solr_address)


    def fetch_data(self, parameters):
        """
        Given the parameters, fetches the data from the Solr instance.
        """
        query = parameters['q']
        data = self.solr.search(**parameters)
        return data
