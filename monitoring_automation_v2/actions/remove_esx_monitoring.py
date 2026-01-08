from actions.base import BaseAction
from modules.elastic.monitor_setup import DeleteESXTypeMonitor
from helpers.general.notify_teams import notify_hosts_removed

class RemoveESXMonitoringAction(BaseAction):

    def __init__(self, elk_key, request, **kwargs):
        super().__init__(elk_key, request, **kwargs)

    def execute_action(self):
        # Set up clients
        if not self.elk_key:
            elk_client = DeleteESXTypeMonitor()
        else:
            elk_client = DeleteESXTypeMonitor(api_key=self.elk_key)
        # elk_logger, _, _, _, _, ticket_id, ticket_link, _ = extract_arguments(**kwargs)
        hosts_for_deletion = []
        for host in self.request.hosts:
            hosts_for_deletion.append(host.lower())
            hosts_for_deletion.append(host.upper())

        hosts_removed, hosts_failed = elk_client.remove_sdp_host(hosts_for_deletion)
        self.update_sdp_request()
        notify_hosts_removed(hosts_removed=hosts_removed, hosts_failed=hosts_failed, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)
        self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',log_level='DEBUG',message=f"Monitoring and alerting successfully removed for hosts: {hosts_removed}",ticket_id=self.request.ticket_id))
        if len(hosts_failed) > 0:
            self.elk_logger.save_log(self.elk_logger.format_log(function_name='execute_action',log_level='ERROR',message=f"Failed to remove monitoring/alerting for hosts: {hosts_failed}",ticket_id=self.request.ticket_id))
