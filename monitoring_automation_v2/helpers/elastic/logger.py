from modules.elastic.elastic_client import ElasticClient
from datetime import datetime
import json


ELASTIC_HOST = 'https://d00bd6e2761143bd9a32501ad3b4397f.us-east-1.aws.found.io:9243' # PROD
API_KEY = ''
FILEBEAT_LOGS = 'filebeat-scripts'

class ElasticLogger(ElasticClient):
    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY):
        super().__init__(elastic_host=elastic_host, api_key=api_key)
        self.filebeat_logs = FILEBEAT_LOGS

    
    def save_log(self, json_log):
        self.es.index(index=FILEBEAT_LOGS, body=json_log)
    

    def format_log(self, **params):
        service = 'AutomationMonitoringLogs'
        service_name = params.get('service_name', 'automate_monitoring') # default works for automate_mon... script
        filename = params.get('filename', 'automate_monitoring.py') # default works for automate_mon... script
        filepath = params.get('filepath', 'automate_monitoring.py') # default works for automate_mon... script
        log_level = params.get('log_level', 'ERROR')
        process_thread = params.get('process_thread', 'MainThread') # default works for automate_mon... script
        process_name = params.get('process_name', 'MainProcess') # default works for automate_mon... script
        function_name = params.get('function_name', 'main')
        line_number = params.get('line_number', 0)
        message = params.get('message', '')
        ticket_id = params.get('ticket_id', None)

        time = datetime.utcnow().isoformat() + "Z"
        json_customized_log_object = {
            "@timestamp": time,
            "file": {
                "name": filename,
                "path": filepath,
            },
            "service": {
                "type": service,
                "name": service_name,
            },
            "log":{
                "level": log_level
            },
            "process": {
                "thread": {
                    "name": process_thread
                },
                "process": {
                    "name": process_name
                },
            },
            "labels": {
                "function_name": function_name,
                "line_number": line_number,
                "ticket_id": ticket_id
            },
            "message": message
        }
        return json.dumps(json_customized_log_object)