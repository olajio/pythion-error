from datetime import datetime
import re
import time
import requests
import json

from modules.sdp.request import Request


SDP_HOSTS_FIELD = 'udf_sline_75301'
SDP_HOST_TYPE = 'udf_pick_77105'
# SDP_APP_CODE_FIELD = 'udf_sline_75302' # This is the old text field
SDP_APP_CODE_SELECTOR_FIELD = 'udf_pick_75601' # This is the new selector field
SDP_ALERT_FIELD = 'udf_multiselect_75901'

HOST_LIST_DELIMETERS_REGEX = ' |, |; |,|;'

MONITORING_REQUESTS = [
    # 'Remove all Monitoring',
    'Infrastructure Monitoring - Add Monitor',
    'Infrastructure Monitoring - Add Monitor with Alert',
    # 'Add Monitoring to Client in DR',
    # 'Remove all monitoring',
    # 'Add Client Monitoring - Client On-boarding',
    # 'Remove all monitoring for client environment',
    'Infrastructure Monitoring - Remove Alert'
]

ALERT_REQUESTS = [
    # 'Add Client Monitoring - Client On-boarding',
    'Infrastructure Monitoring - Add Monitor with Alert'
]

REMOVE_REQUESTS = [
    # 'Remove all Monitoring',
    # 'Remove all monitoring',
    # 'Remove all monitoring for client environment',
    'Infrastructure Monitoring - Remove Alert'
]


class TicketExtractor:

    def __init__(self, sdp_info=None):
        self.sdp = sdp_info


    def get_ticket_details(self):
        request_url = self.sdp['url'] + '?input_data=' + str(self.sdp['list_info'])
        requests_to_return = []
        try:
            sdp_response = requests.get(request_url, headers=self.sdp['headers'])
            # print('sdp_response status_code: ', sdp_response)
            # print('sdp_response body: ', sdp_response.json())
            if sdp_response.status_code == 200:
                for request in sdp_response.json()['requests']:
                    # print('*'* 40)
                    # print(request)
                    # print('*'* 40)
                    for request_type in MONITORING_REQUESTS:
                        if request_type.lower() in request['subject'].lower():
                            requests_to_return.append(request)
                return requests_to_return
            else:
                # print('sdp_response body: ', sdp_response.json())
                return None
        except Exception as e:
            # print('Request caused an exception: ', str(e))
            return None
        

    def extract_hosts_and_alerts(self, sdp_response=None):
        if not sdp_response:
            # print('The request to get details on the tickets failed!')
            return None, None

        req_hosts = None
        req_app_code = None
        requests_to_action = {}
        requests_to_skip = {}
        for request in sdp_response:
            if request.get('udf_fields', None):
                req_hosts = request['udf_fields'].get(SDP_HOSTS_FIELD, None)
                # req_app_code = request['udf_fields'].get(SDP_APP_CODE_FIELD, None) # Old text field
                req_app_code = request['udf_fields'].get(SDP_APP_CODE_SELECTOR_FIELD, None)
                req_host_type = request['udf_fields'].get(SDP_HOST_TYPE, None)
                req_subject = request['subject']
                # req_alerts = request['udf_fields'].get(SDP_ALERT_FIELD, None) # TODO Add req alerts extraction functionality here
                req_alerts = None
                action = 'monitoring'
                for request_type in ALERT_REQUESTS:
                    if request_type.lower() in req_subject.lower():
                        action = 'alerting'
                        req_alerts = self.get_request_alerts(request['id'])
                        # We are sleeping after each request for a bit in order not to put too much
                        # pressure on the Support Portal
                        time.sleep(2)
                for request_type in REMOVE_REQUESTS:
                    if request_type.lower() in req_subject.lower():
                        action = 'delete'
                        for host in req_hosts:
                            if 'esx' in host.lower():
                                action = 'esx_delete'
                                break

                if req_host_type and req_host_type.lower() == 'esx':
                    action = 'esx'
                
                if req_host_type and req_host_type.lower() == 'url':
                    action = 'url_monitoring'

                if req_host_type and req_host_type.lower() == 'ping':
                    action = 'ping_monitoring'

                if req_host_type and req_host_type.lower() == 'port':
                    action = 'port_monitoring'

                requests_to_action[request['id']] = {
                    'app_code': req_app_code, 
                    'hosts': req_hosts, 
                    'alerts': req_alerts,
                    'req_action': action
                }
            else:
                requests_to_skip[request['id']] = {'subject': request['subject']}

        return requests_to_action, requests_to_skip
    

    def get_request_alerts(self, request_id):
        # print('==========Get Request Alerts==========')
        url = f"{self.sdp['url']}/{request_id}"
        
        sdp_response = requests.get(url, headers=self.sdp['headers'])
        # print('request status code: ', sdp_response)
        # print('sdp_response: ', sdp_response.json())

        udf_fields = sdp_response.json()['request'].get('udf_fields', None)
        alerts = None
        if udf_fields:
            alert_string_list = udf_fields.get(SDP_ALERT_FIELD, [])

            alerts = []
            for alert in alert_string_list:
                amdb = alert.split('-')[0].strip()
                alerts.append(amdb)
    
        # print('Alerts: ', alerts)
        return alerts
    

    def format_host_arguments(self, requests_to_action):
        # print('********Format Host Arguments********')
        requests = []
        updated_requests = {}
        wrong_requests = {}
        if not requests_to_action:
            return None, None
        for key in requests_to_action.keys():
            # print('item: ', requests_to_action[key])
            hosts_str = requests_to_action[key]['hosts']
            req_action = requests_to_action[key].get('req_action', '')
            # print('HOSTS STR: ', hosts_str)
            if not hosts_str:
                wrong_requests[key] = requests_to_action[key]
                continue
            host_list = re.split(HOST_LIST_DELIMETERS_REGEX, hosts_str)
            # print('HOST LIST: ', host_list)
            host_env = self.get_host_env(host_list)
            if req_action == 'monitoring' or req_action == 'alerting':
                if not self.validate_hostname(host_list):
                    wrong_requests[key] = requests_to_action[key]
                    wrong_requests[key]['hosts'] = host_list
                    # print(f"Doesn't Comply with pattern '{requests_to_action[key]}'")
                    continue
                if not host_env:
                    wrong_requests[key] = requests_to_action[key]
                    wrong_requests[key]['host_env'] = host_env
                    continue
            requests_to_action[key]['host_env'] = host_env
            requests_to_action[key]['hosts'] = host_list

            updated_requests[key] = requests_to_action[key]
            hosts = updated_requests[key].get('hosts', None)
            app_code = updated_requests[key].get('app_code', None)
            alerts = updated_requests[key].get('alerts', None)
            env = updated_requests[key].get('host_env', None)
            action = updated_requests[key].get('req_action', None)
            if action == 'esx':
                if hosts and hosts[0].count('-') > 1:
                    action = 'datastore_monitoring'
                else:
                    action = 'esx_monitoring'
            
            request = Request(ticket_id=key, hosts=hosts, app_code=app_code, alerts=alerts, env=env, action=action)
            requests.append(request)

        return requests, wrong_requests

    ## Commenting out, due to insufficient testing
    def validate_hostname(self, host_list):
        name_pattern = r'^[A-Za-z]{2}\d{2}-[A-Za-z--9]*$'
        for host in host_list:
            if re.match(name_pattern,host):
                # print(f"Hostname is correct '{host}'")
                pass
            else:
                # print(f"Hostname {host} doesn't comply")
                return False
        return True
    

    def get_host_env(self, hosts):
        env = set()
        # print('env: ', env)
        # print('type(env): ', type(env))
        for host in hosts:
            try:
                datacenter = host.split('-')[0]
            except:
                datacenter = None
            # print('datacenter: ', datacenter)
            host_env = self.host_envs_by_datacenter(datacenter)
            if host_env:
                env.add(host_env)
            # print('env: ', env)
        
        # print('final env: ', env)
        # print('len(env): ', len(env))
        if len(env) > 1:
            # print('There are multiple environments in the server request')
            # return 'Multi ENV'
            pass
        elif len(env) == 0:
            # print('No environment could be extracted by the hosts...')
            return None

        # print('ENV: ', env)
        final_env = list(env)[0]
        # print('env for hosts is: ', final_env)
        return final_env


    def host_envs_by_datacenter(self, datacenter):
        envs = {
            "CS01": "HSC",
            "CS51": "HSC",
            "ES01": "HSE",
            "ES51": "HSE",
            "CW01": "HCW",
            "CW51": "HCW",
            "EW01": "HEW",
            "EW51": "HEW",
            "MS01": "HSM",
            "MS51": "HSM",
            "TS01": "HST",
            "TS51": "HST",
            "TW01": "HTW",
            "TW51": "HTW"
        }

        return envs.get(datacenter.upper(), None)
