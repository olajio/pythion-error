from actions.base import BaseAction
from modules.elastic.monitor_setup import ESXHandler
from helpers.general.notify_teams import notify_hosts_added

class ESXHostMonitoringAction(BaseAction):

    def __init__(self, elk_key, request, **kwargs):
        super().__init__(elk_key, request, **kwargs)

    def execute_action(self):
        if not self.elk_key:
            elk_client = ESXHandler()
        else:
            elk_client = ESXHandler(api_key=self.elk_key)

        found_hosts, missing_hosts = elk_client.validate_hosts(hosts=self.request.hosts)
        if len(missing_hosts) > 0:
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',log_level='ERROR',message=f"Hosts not found in elastic: {missing_hosts}",ticket_id=self.request.ticket_id))
        
        hosts_success, host_failure = elk_client.save_sdp_amdb(hosts=found_hosts, alerts=self.request.alerts)

        if not hosts_success and not host_failure:
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',message=f"Creating records in sdp_amdb failed...",ticket_id=self.request.ticket_id))
        if host_failure and len(host_failure) > 0:
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',message=f"Hosts with errors when saving in sdp_amdb: {host_failure}",ticket_id=self.request.ticket_id))

        hosts_report = {
            'elastic_found_hosts': found_hosts,
            'elastic_not_found': missing_hosts,
            'consul_configs_hosts': ['N/A'],
            'consul_not_found': ['N/A'],
            'sdp_hosts': hosts_success,
            'sdp_error_hosts': host_failure
        }
        # print('hosts_report: ', hosts_report)
        self.update_sdp_request()
        notify_hosts_added(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)
