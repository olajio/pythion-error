from elasticsearch import Elasticsearch


class ElasticClient():

    def __init__(self, elastic_host=None, api_key=None):
        self._elastic_host = elastic_host
        self._api_key = api_key
        self._set_es_connection()


    def _set_es_connection(self):
        es = Elasticsearch(self._elastic_host, api_key=self._api_key, verify_certs=False, ssl_show_warn=False)  
        self.es = es