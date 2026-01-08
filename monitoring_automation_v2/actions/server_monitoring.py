from actions.base import BaseAction
from modules.elastic.monitor_setup import AlertHandler
from modules.aws.elastic_agents_codebuild import ElasticAgentsCodebuild
from modules.aws.aws_logs import ElasticLogs
from helpers.general.consul_handler import ConsulHandler
from helpers.general.notify_teams import notify_hosts_added

class ServerMonitoringAction(BaseAction):

    def __init__(self, elk_key, request, **kwargs):
        super().__init__(elk_key, request, **kwargs)

    def execute_action(self):
        if not self.elk_key:
            elk_client = AlertHandler()
        else:
            elk_client = AlertHandler(api_key=self.elk_key)

        consul = ConsulHandler()
        aws_client = ElasticAgentsCodebuild()
        aws_logs = ElasticLogs()
        # Step 1 -> run codebuild and wait for finish
        if self.request.action != 'alerting_only':
            # aws_client.install_agents(aws_client=aws_client, hosts=hosts, env=env)
            codebuild_id = aws_client.install_agents(hosts=self.request.hosts, env=self.request.env)
            logs_url = aws_logs.get_codebuild_logs(codebuild_id)
            log_message = f"To view the CodeBuild please open the following link - {logs_url}"
            # self.ticket_handler.add_ticket_note(ticket_id=ticket_id,message=log_message)
            # time.sleep(20)
        # Step 2 -> validate hosts in elastic
        found_hosts, not_found_hosts = elk_client.validate_hosts(self.request.hosts) # Elastic validation !!!!
        # print('2. Elastic found_hosts: ', found_hosts)
        
        # Step 3 -> notify for failed hosts
        if len(not_found_hosts) > 0:
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',log_level='ERROR',message=f"Hosts not found in elastic: {not_found_hosts}",ticket_id=self.request.ticket_id))
        
        if self.request.action == 'monitoring':
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',log_level='INFO',message=f"Hosts found in elastic: {found_hosts}",ticket_id=self.request.ticket_id))
            hosts_report = {
                'elastic_found_hosts': found_hosts,
                'elastic_not_found': not_found_hosts,
                'consul_configs_hosts': 'NA for Monitoring only request',
                'consul_not_found': 'NA for Monitoring only request',
                'sdp_hosts': 'NA for Monitoring only request',
                'sdp_error_hosts': 'NA for Monitoring only request'
            }
            self.update_sdp_request()
            notify_hosts_added(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)
            return
        
        # Step 4 -> pull consul config for verified hosts
        consul_hosts, not_in_consul = consul(found_hosts) # Consul config !!!!
        consul_hosts_list = [host for host in consul_hosts.keys()] # Consul config !!!!
        
        # Step 5 -> notify for missing consul configs for hosts
        # print('5. not in consul: ', not_in_consul)
        if len(not_in_consul) > 0:
            # logger_params['message'] = f"Consul configs not found for hosts: {not_in_consul}"
            # logger_params['line_number'] = 140
            # elk_logger.save_log(elk_logger.format_log(logger_params))
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',message=f"Consul configs not found for hosts: {not_in_consul}",ticket_id=self.request.ticket_id))
        
        # Step 6 -> for valid hosts with consul configs set up alert record
        # print('6. consul host: ', consul_hosts)

        sdp_hosts, sdp_error_hosts = elk_client.save_sdp_amdb(hosts=found_hosts, alerts=self.request.alerts, consul_hosts=consul_hosts) # sdp_amdb records !!!!
        
        if not sdp_hosts and not sdp_error_hosts:
            # logger_params['message'] = f"Creating records in sdp_amdb failed! Either no hosts were sent or there were no consul configs for the hosts..."
            # logger_params['line_number'] = 145
            # elk_logger.save_log(elk_logger.format_log(logger_params))
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',message=f"Creating records in sdp_amdb failed! Either no hosts were sent or there were no consul configs for the hosts...",ticket_id=self.request.ticket_id))
        elif len(sdp_error_hosts) > 0:
            # logger_params['message'] = f"Hosts with errors when saving in sdp_amdb: {sdp_error_hosts}"
            # logger_params['line_number'] = 157
            # elk_logger.save_log(elk_logger.format_log(logger_params))
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',message=f"Hosts with errors when saving in sdp_amdb: {sdp_error_hosts}",ticket_id=self.request.ticket_id))

        
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
        self.update_sdp_request()
        notify_hosts_added(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)
