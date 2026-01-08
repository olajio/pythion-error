'''
This script is adding a custom client configuration to the sdp_amdb index in the CCS cluster. We 
have client monitoring setup for all of the caviar clients, but there are some additional ones
as well.

The client alert 

Example client monitoring config document:

{
    "alert_status": "enabled",
    "hostname": "<hostname>",
    "record": {
        "created_by": "monitoring_automation",
        "created_timestamp": "<current_utc_time>"
    },
    "client": "<client_name>",
    "app_code": "",
    "type": "client",
    "group": [<comma separated alert list>]
}
'''
from datetime import datetime
from argparse import ArgumentParser
import json
from elasticsearch import Elasticsearch


ELASTIC_HOST = 'https://de26459b90754aceb3234fe7969cb1ee.us-east-1.aws.found.io:9243' # CCS

class ElasticClient():

    def __init__(self, elastic_host=None, api_key=None):
        self._elastic_host = elastic_host
        self._api_key = api_key
        self._set_es_connection()


    def _set_es_connection(self):
        es = Elasticsearch(self._elastic_host, api_key=self._api_key, verify_certs=False, ssl_show_warn=False)  
        self.es = es


class ClientHandler:

    def __init__(self, es_client=None):
        self.es = es_client

    @property
    def es(self):
        return self._es
    
    @es.setter
    def es(self, value):
        if not value:
            raise Exception('Es client is not set...')
        
        self._es = value

    def save_client_configs(self, client_list, alert_list):
        '''
        Verify there are no configs for the list of clients in sdp_amdb before creating a new one.
        '''

        completed_list = []
        failed_list = []
        for client in client_list:
            doc = self.check_client_alerts(client)
            skip = True
            if not doc:
                doc = self._build_client_config_body(client=client, alert_list=alert_list)
                skip = False
            else:
                for alert in alert_list:
                    if alert not in doc['group']:
                        doc['group'].append(alert)
                        skip = False

            if skip:
                print(f'Skipping update for client {client} as it is up to date.')
                print('*'*100)
                continue
            
            print(f'For client {client} the document is this: {doc}')
            try:
                res = self.es.index(index='sdp_amdb', id=client, body=doc)
                print (f'Res for host: {client} is: ', res)
                if res['result'].lower() == 'updated' or res['result'].lower() == 'created':   
                    completed_list.append(client)
                else:
                    failed_list.append(client)
            except Exception as e:
                print(f"There was an error for host {client}:\n", str(e))
                failed_list.append(client)

            print('-'*100)

        return completed_list, failed_list

    def check_client_alerts(self, client):
        try:
            result = self.es.get(index='sdp_amdb', id=client)
            return result['_source']
        except Exception as e:
            print('Error:\n', str(e))
            return None
        
    def _build_client_config_body(self, client, alert_list=[]):
        return {
            "alert_status": "enabled",
            "hostname": client,
            "record": {
                "created_by": "monitoring_automation",
                "created_timestamp": datetime.utcnow().isoformat() + 'Z'
            },
            "client": client,
            "app_code": "",
            "type": "client",
            "group": alert_list
        }
    

if __name__=='__main__':

    parser = ArgumentParser(description='Automate the process of setting up alerting for clients!')
    parser.add_argument('--elastic_key', default=True) 
    args = parser.parse_args()
    elk_key = args.elastic_key

    with open('monitoring_params.json', 'r') as f:
        params = json.load(f)

    clients = params.get('hosts', None)
    alerts = params.get('alarms', None)

    es_client = ElasticClient(elastic_host=ELASTIC_HOST, api_key=elk_key)
    client_handler = ClientHandler(es_client.es)

    completed, failed = client_handler.save_client_configs(client_list=clients, alert_list=alerts)

    print(f'The process finished successfully for the following clients:\n {completed}')
    print('-'*100)
    print(f'The process failed for the following clients:\n {failed}')