import time
import requests
import json
from pathlib import Path
from argparse import ArgumentParser
from helpers.general.consul_handler import ConsulHandler
from helpers.general.notify_teams import notify_hosts_added, notify_hosts_removed, notify_urls_added
from helpers.general.sdp_operations import get_ticket_details
from helpers.sdp import ticket_operations as to
import helpers.general.json_log_format as jlf
from helpers.elastic.monitor_setup import MonitorHandler
from helpers.aws.elastic_agents_codebuild import ElasticAgentsCodebuild


jlf.service_name = Path(__file__).stem
jlf.service_type = 'MonitoringAutomation'
jlf.json_logging.init_non_web(custom_formatter=jlf.CustomJSONLog, enable_json=True)
logger = jlf.logging.getLogger(__name__)
logger.setLevel(jlf.logging.DEBUG)
logger.addHandler(jlf.logging.StreamHandler(jlf.sys.stdout))



def main():
    # Set up clients
    if not elk_key:
        elk_client = MonitorHandler()
    else:
        elk_client = MonitorHandler(api_key=elk_key)

    if action == 'delete':
        hosts_for_deletion = []
        for host in hosts:
            hosts_for_deletion.append(host.lower())
            hosts_for_deletion.append(host.upper())
        remove_monitoring(elk_client=elk_client, hosts_for_deletion=hosts_for_deletion, ticket_id=ticket_id)
    elif 'url' in action:
        setup_url_monitoring(elk_client=elk_client, ticket_id=ticket_id)
    else:
        setup_monitoring(elk_client=elk_client, ticket_id=ticket_id)



def remove_monitoring(elk_client, hosts_for_deletion, ticket_id):
    hosts_removed, hosts_failed = elk_client.remove_sdp_host(hosts_for_deletion)
    notify_hosts_removed(hosts_removed=hosts_removed, hosts_failed=hosts_failed, ticket_id=ticket_id)
    logger.debug(f"Monitoring and alerting successfully removed for hosts: {hosts_removed}")
    if len(hosts_failed) > 0:
        logger.error(f"Failed to remove monitoring/alerting for hosts: {hosts_failed}")
    logger.debug(f"Sent teams report for removing alerts on hosts!")


def setup_url_monitoring(elk_client, ticket_id):
    sdp_url_monitrs, sdp_url_error_monitors = elk_client.save_url_monitor_records(hosts, alerts)

    if len(sdp_url_error_monitors) > 0:
        logger.error(f"There were urls with errors when trying to setup monitoring in sdp_amdb -> {sdp_url_error_monitors}")
    
    logger.debug(f"Added monitoring successfully for these urls in sdp_amdb -> {sdp_url_monitrs}")

    hosts_report = {
        # 'elastic_found_hosts': found_hosts,
        # 'elastic_not_found': not_found_hosts,
        # 'consul_configs_hosts': consul_hosts_list,
        # 'consul_not_found': not_in_consul,
        'sdp_hosts': sdp_url_monitrs,
        'sdp_error_hosts': sdp_url_error_monitors
    }
    notify_urls_added(hosts_report=hosts_report, ticket_id=ticket_id)
    logger.debug(f"Sent a teams notification!")



def setup_monitoring(elk_client, ticket_id):
    consul = ConsulHandler()
    aws_client = ElasticAgentsCodebuild()
    logger.debug(f"Imported modules for AWS and Consul!")
    # Step 1 -> run codebuild and wait for finish
    if action != 'alerting_only':
        install_agents(aws_client=aws_client, hosts=hosts)
        logger.debug(f"Finished CodeBuild step! Continuing to verify hosts in elastic!")
    # Step 2 -> validate hosts in elastic
    found_hosts, not_found_hosts = elk_client.validate_hosts(hosts) # Elastic validation !!!!
    # print('2. Elastic found_hosts: ', found_hosts)
    logger.debug(f"Hosts in elastic: {found_hosts}")

    # Step 3 -> notify for failed hosts
    if len(not_found_hosts) > 0:
        # print('3. Elastic not_found_hosts: ', not_found_hosts)
        logger.error(f"Hosts not found in elastic: {not_found_hosts}")

    if action == 'monitoring':
        logger.debug(f"Script ran with the monitoring flag. Monitoring setup is finished -> ending script execution...")
        exit()

    # Step 4 -> pull consul config for verified hosts
    consul_hosts, not_in_consul = consul(found_hosts) # Consul config !!!!
    consul_hosts_list = [host for host in consul_hosts.keys()] # Consul config !!!!
    logger.debug(f"Consul configs found for hosts: {consul_hosts_list}")

    # Step 5 -> notify for missing consul configs for hosts
    # print('5. not in consul: ', not_in_consul)
    if len(not_in_consul) > 0:
        logger.error(f"Consul configs not found for hosts: {not_in_consul}")

    # Step 6 -> for valid hosts with consul configs set up alert record
    # print('6. consul host: ', consul_hosts)

    sdp_hosts, sdp_error_hosts = elk_client.save_sdp_amdb(hosts=found_hosts, alerts=alerts, consul_hosts=consul_hosts) # sdp_amdb records !!!!

    if not sdp_hosts and not sdp_error_hosts:
        logger.error(f"Creating records in sdp_amdb failed! Either no hosts were sent or there were no consul configs for the hosts...")
    logger.debug(f"Created record in sdp_amdb for hosts: {sdp_hosts}")
    if len(sdp_error_hosts) > 0:
        logger.error(f"Hosts with errors when saving in sdp_amdb: {sdp_error_hosts}")


    # Step 7 -> send report to ITSMA via teams
    hosts_report = {
        'elastic_found_hosts': found_hosts,
        'elastic_not_found': not_found_hosts,
        'consul_configs_hosts': consul_hosts_list,
        'consul_not_found': not_in_consul,
        'sdp_hosts': sdp_hosts,
        'sdp_error_hosts': sdp_error_hosts
    }
    # print('hosts_report: ', hosts_report)
    notify_hosts_added(hosts_report=hosts_report, ticket_id=ticket_id)
    logger.debug(f"Sent a teams notification!")


def install_agents(aws_client, hosts):
    servers_to_run = ''
    for host in hosts:
        servers_to_run += host.lower() + ',' + host.upper() + ','
        # print('Servers to run in progress: ', servers_to_run)
    servers_to_run = servers_to_run[:-1]
    
    codebuild_response = aws_client.start_codebuild(env=env, servers=servers_to_run)
    codebuild_id = codebuild_response['build']['id']
    print('CodebuildID: ', codebuild_id)
    while True:
        cb_status = aws_client.get_build_status(codebuild_id)
        current_phase = cb_status['builds'][0]['currentPhase']

        if current_phase == 'COMPLETED':
            print('Build completed!')
            break
        else:
            print('Sleeping for 5 minutes - build still not finished: ', current_phase)
            time.sleep(300)


def load_monitoring_tickets():
    created_after = 35
    created_before = 1

    search_criteria = to.get_search_criteria_for_time_period(created_after, created_before)
    sdp_request_details = to.get_requests_query_by_search_criteria(search_criteria)
    sdp_response = to.get_ticket_details(sdp_request_details)
    requests_to_action, non_monitoring_requests = to.extract_hosts_and_alerts(sdp_response)
    final_requests_to_action, wrong_requests = to.format_host_arguments(requests_to_action)
    print('final_requests_to_action: ', final_requests_to_action)
    print('*'*40)
    print('wrong_requests: ', wrong_requests)

    for ticket_id in final_requests_to_action.keys():
        hosts = final_requests_to_action[ticket_id].get('hosts', None)
        app_code = final_requests_to_action[ticket_id].get('app_code', None)
        alerts = final_requests_to_action[ticket_id].get('alerts', None)
        env = final_requests_to_action[ticket_id].get('host_env', None)

        if not hosts or not env or not alerts:
            print('*'* 40)
            print(f'Ticket with id {ticket_id} has missing parameters!!!')
            print(f'Values for the run -> {final_requests_to_action[ticket_id]}')
            continue
        
        print('*'* 40)
        print(f'Values for the run -> {final_requests_to_action[ticket_id]}')
        # main()



if __name__=='__main__':
    parser = ArgumentParser(description='Automate the process of setting up monitoring and alerting for new hosts!')
    parser.add_argument('--params_mode', default='SDP')
    parser.add_argument('--action', choices=['monitoring', 'alerting', 'delete', 'alerting_only', 'url_alerting'], default='alerting')
    parser.add_argument('--elastic_key', default=None)
    args = parser.parse_args()
    params_mode = args.params_mode
    action = args.action
    elk_key = args.elastic_key

    if 'SDP' not in params_mode:
        params = None
        with open('monitoring_params.json', 'r') as f:
            params = json.load(f)

        # print('Params is: ', params)
        hosts = params.get('hosts', None)
        alerts = params.get('alarms', None)
        env = params.get('env', None)
        ticket_id = params.get('ticket_id', None)

        main()
    else:
        load_monitoring_tickets()
