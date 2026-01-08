import pathlib
from argparse import ArgumentParser
import json

from helpers.elastic.logger import ElasticLogger
import helpers.aws.roles_anywhere_authenticate as ra
import helpers.sdp.save_request as sr
from modules.sdp.ticket_handler import TicketHandler
from modules.sdp.request import Request
from actions.action_loader import ActionLoader
from actions.esx_host_monitoring import ESXHostMonitoringAction
from actions.remove_monitoring import RemoveMonitoringAction
from actions.server_monitoring import ServerMonitoringAction
from actions.url_monitoring import URLMonitoringAction
from actions.datastore_monitoring import DatastoreMonitoringAction
from actions.remove_esx_monitoring import RemoveESXMonitoringAction


ACTION_CHOICES = [
    'monitoring', 
    'alerting', 
    'delete', 
    'alerting_only', 
    'url_alerting', 
    'esx_monitoring', 
    'datastore_monitoring', 
    'ping_monitoring', 
    'url_monitoring', 
    'port_monitoring', 
    'esx_delete'
]
REQUESTS_FILE_PATH = str(pathlib.Path(__file__).parent.resolve())

def setup_actions(action_loader):
    action_loader.register_action('monitoring', ServerMonitoringAction)
    action_loader.register_action('alerting', ServerMonitoringAction)
    action_loader.register_action('alerting_only', ServerMonitoringAction)
    action_loader.register_action('delete', RemoveMonitoringAction)
    action_loader.register_action('url_alerting', URLMonitoringAction)
    action_loader.register_action('ping_monitoring', URLMonitoringAction)
    action_loader.register_action('url_monitoring', URLMonitoringAction)
    action_loader.register_action('port_monitoring', URLMonitoringAction)
    action_loader.register_action('esx_monitoring', ESXHostMonitoringAction)
    action_loader.register_action('datastore_monitoring', DatastoreMonitoringAction)
    action_loader.register_action('esx_delete', RemoveESXMonitoringAction)

action_loader = ActionLoader()
setup_actions(action_loader)


def main(request, elk_key, **kwargs):
    elk_logger = kwargs.get('elk_logger', None)
    # action = kwargs.get('action', None)

    if not request.action or request.action not in ACTION_CHOICES:
        elk_logger.save_log(elk_logger.format_log(log_level='ERROR', message=f"Action for the request was not properly. Value: {action}",ticket_id=ticket_id))
    
    
    action_handler = action_loader.get_action_handler(request.action, elk_key, request, **kwargs)
    # print('action_handler: ', action_handler)
    action_handler.execute_action()


def load_monitoring_tickets(elk_logger, elk_key, sdp_key):
    created_after = 30
    created_before = 0

    ticket_handler = TicketHandler(search_start_time=created_after, search_end_time=created_before, elk_logger=elk_logger, sdp_key=sdp_key)
    requests_to_action, wrong_requests = ticket_handler.run_extract()
    # Processed request functionality
    new_requests = []
    requests_file = REQUESTS_FILE_PATH + '/handled_request.txt'
    # print(requests_file)
    old_processed_requests = sr.load_processed_requests(requests_file)
    # Processed request functionality

    if not requests_to_action:
        return
    
    for request_id in wrong_requests.keys():
        new_requests.append(request_id)
        # Processed request functionality
        if sr.check_request(request_id, old_processed_requests):
            # print('*'*40)
            # print('skipping request: ', request_id)
            # print('*'*40)
            continue
        # Processed request functionality
        elk_logger.save_log(elk_logger.format_log(function_name='load_monitoring_tickets',file_name='ticket_handler',message=f"Request is missing information and cannot be handled by the automation process: {wrong_requests[request_id]}",ticket_id=request_id))

    for request in requests_to_action:

        new_requests.append(request.ticket_id)
        # Processed request functionality
        if sr.check_request(request.ticket_id, old_processed_requests):
            # print('*'*40)
            # print('skipping request: ', request)
            # print('*'*40)
            continue
        # Processed request functionality
        
        if not request.validate_request():
            # print('Not valid request: ', request)
            elk_logger.save_log(elk_logger.format_log(function_name='load_monitoring_tickets',message=f"Request is missing information and cannot be handled by the automation process: {request}",ticket_id=request.ticket_id))
            continue
        
        # print('request: ', request)
        # print('*'*40)

        main(request, elk_key, elk_logger=elk_logger, ticket_handler=ticket_handler)
        elk_logger.save_log(elk_logger.format_log(function_name='load_monitoring_tickets',message=f"Monitoring Automation finished for ticket with id - {request.ticket_id}. Please verify.",log_level='INFO',ticket_id=request.ticket_id))

    # Processed request functionality
    latest_requests = sr.remove_missing_requests(new_requests, old_processed_requests)
    sr.save_processed_requests(latest_requests, requests_file)
    # Processed request functionality
    # print('New requests: ', new_requests)
    # print('Latest requests: ', latest_requests)



if __name__=='__main__':
    parser = ArgumentParser(description='Automate the process of setting up monitoring and alerting for new hosts!')
    parser.add_argument('--params_mode', default='SDP')
    parser.add_argument('--action', choices=ACTION_CHOICES, default='alerting')
    parser.add_argument('--elastic_key', default=True)
    parser.add_argument('--elk_logger_key', required=True)
    parser.add_argument('--sdp_key', required=True)
    parser.add_argument('--aws_roles', choices=['true', None], default=None)
    parser.add_argument('--step', default='1')
    args = parser.parse_args()
    params_mode = args.params_mode
    action = args.action
    elk_key = args.elastic_key
    elk_logger_key = args.elk_logger_key
    sdp_key = args.sdp_key
    aws_roles = args.aws_roles
    step = args.step

    elk_logger = ElasticLogger(api_key=elk_logger_key)
    
    if aws_roles:
        ra.decode_configuration()
        ra.export_new_config()

    if 'SDP' not in params_mode:
        params = None
        with open('monitoring_params.json', 'r') as f:
            params = json.load(f)

        # print('Params is: ', params)
        hosts = params.get('hosts', None)
        alerts = params.get('alarms', None)
        env = params.get('env', None)
        ticket_id = params.get('ticket_id', None)
        ticket_handler = TicketHandler(elk_logger=elk_logger, sdp_key=sdp_key)
        request = Request(hosts=hosts,alerts=alerts,env=env,action=action,ticket_id=ticket_id)

        main(request, elk_key, elk_logger=elk_logger, ticket_handler=ticket_handler, step=step)
        if ticket_id:
            elk_logger.save_log(elk_logger.format_log(message=f"Monitoring Automation(Manual Run) finished for ticket with id - {ticket_id}. Please verify.",log_level='INFO',ticket_id=ticket_id))
    else:
        load_monitoring_tickets(elk_logger, elk_key, sdp_key)
    
    if aws_roles:
        ra.remove_decoded_file()