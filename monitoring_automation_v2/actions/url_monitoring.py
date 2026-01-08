import os
from datetime import datetime
import yaml
from actions.base import BaseAction
from modules.elastic.monitor_setup import URLHandler
from modules.git.git_setup import GitHandler
from helpers.general.notify_teams import notify_urls_added, notify_url_configs_added_to_git

BASE_REPO_PATH = '/tmp/'
REPO_NAME = 'hs_elastic_heartbeat_MS01-11ELKHB01'

REPO_URL = 'git@ghe.hedgeserv.net:ITSMA/hs_elastic_hearbeat_MS01-11ELKHB01.git'

REPO_CONFIG_DIR = f"{BASE_REPO_PATH}{REPO_NAME}/monitors.d"


class URLMonitoringAction(BaseAction):

    def __init__(self, elk_key, request, **kwargs):
        super().__init__(elk_key, request, **kwargs)
        self.setup_step = kwargs.get('step', '1')

    def execute_action(self):
        # Set up clients
        if not self.elk_key:
            elk_client = URLHandler()
        else:
            elk_client = URLHandler(api_key=self.elk_key)

        if self.setup_step == '1':
            try:
                git = GitHandler()
                branch_name = 'new_automated_config_'
                if self.request.ticket_id:
                    branch_name += self.request.ticket_id
                else:
                    today = datetime.today().strftime('%Y-%m-%d')
                    branch_name += str(today)
                git.clean_tmp_repo(f"{BASE_REPO_PATH}{REPO_NAME}")
                repo = git.clone_repo(REPO_URL, f"{BASE_REPO_PATH}{REPO_NAME}")
                git.git_pull_master(repo)

                git.switch_branch(repo, branch_name)
                file_name = self.create_monitoring_configs()
                commit_message = 'Added new monitoring configuration.'
                git.commit_updates(repo, file_name, commit_message)

                git.push_commits(repo, branch_name)
                git.clean_tmp_repo(f"{BASE_REPO_PATH}{REPO_NAME}")

                if self.elk_logger:
                    self.elk_logger.save_log(self.elk_logger.format_log(log_level='INFO', message=f"URL related config request was actioned by the automation",ticket_id=self.request.ticket_id))

                hosts_report = {
                    'hosts': self.request.hosts,
                    'message': f"Url configs created successfully for branch - {branch_name}"
                }
                self.update_sdp_request()
                notify_url_configs_added_to_git(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)
            except Exception as e:
                message = f"There was an error adding new URL configs to git. Error: {e}"
                if self.elk_logger:
                    self.elk_logger.save_log(self.elk_logger.format_log(log_level='ERROR', message=message, ticket_id=self.request.ticket_id))

                hosts_report = {
                    'hosts': self.request.hosts,
                    'message': f"There was an error adding new URL configs to git. Error: {e}"
                }
                self.update_sdp_request()
                notify_url_configs_added_to_git(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)

        else:
            sdp_url_monitors, sdp_url_error_monitors = elk_client.save_url_monitor_records(self.request.hosts, self.request.alerts)

            if len(sdp_url_error_monitors) > 0:
                """Need to log the error to elastic"""
                pass
            
            # logger.debug(f"Added monitoring successfully for these urls in sdp_amdb -> {sdp_url_monitrs}")

            hosts_report = {
                'sdp_hosts': sdp_url_monitors,
                'sdp_error_hosts': sdp_url_error_monitors
            }
            self.update_sdp_request()
            notify_urls_added(hosts_report=hosts_report, ticket_id=self.request.ticket_id, ticket_link=self.ticket_link)


    def create_monitoring_configs(self):
        if self.request.action == 'ping_monitoring':
            yml_configs = self._set_up_ping_configs()
        elif self.request.action == 'port_monitoring':
            yml_configs = self._set_up_port_configs()
        else:
            yml_configs = self._set_up_url_configs()
        
        file_name = self._create_new_file(yml_configs)
        return file_name
    

    def _create_new_file(self, configs):
        file_name = 'monitoring_automation_placeholder_1'
        file_extension = '.yml'
        if self.request.ticket_id:
            file_name = file_name.replace('placeholder', self.request.ticket_id)
        else:
            today = datetime.today().strftime('%Y-%m-%d')
            file_name = file_name.replace('placeholder', today)
            if os.path.exists(f"{REPO_CONFIG_DIR}/{file_name}{file_extension}"):
                file_prefix = file_name[:-1]
                files = [filename for filename in os.listdir(REPO_CONFIG_DIR) if filename.startswith(file_prefix)]
                file_name = file_prefix + str(len(files) + 1)

        full_path = f"{REPO_CONFIG_DIR}/{file_name}{file_extension}"

        with open(full_path, 'w') as f:
            yaml.dump(configs, f, default_flow_style=False, sort_keys=False)
            # yaml.dump(configs, f, default_flow_style=False, sort_keys=False)

        return full_path
    
    
    def _set_up_url_configs(self):
        yml_configs = []
        for host in self.request.hosts:
            if not host.startswith('http'):
                name = host.split('/')[0]
            else:
                name = host.split('/')[2]
            # url_config = URLConfig('http', [host], name, host, [])
            host_config = {
                "type": "http",
                "tags": [],
                "id": host,
                "name": name,
                "hosts": [host],
                "ssl.verification_mode": "none",
                "schedule": "@every 30s"
            }

            yml_configs.append(host_config)
            # yml_configs.append(url_config)

        return yml_configs


    def _set_up_port_configs(self):
        confs = {}
        for host_conf in self.request.hosts:
            host = host_conf.split(':')[0]
            port = host_conf.split(':')[1]
            if confs.get(host, None):
                confs[host].append(int(port))
            else:
                confs[host] = [int(port)]
        yml_configs = []
        for host, ports in confs.items():
            host_config = {
                "type": "tcp",
                "tags": [],
                "id": host,
                "name": host,
                "hosts": [host],
                "ports": ports,
                "schedule": "@every 30s"
            }

            yml_configs.append(host_config)

        return yml_configs
    
    def _set_up_ping_configs(self):
        yml_configs = []
        for host in self.request.hosts:
            host_config = {
                "type": "icmp",
                "tags": [],
                "id": host,
                "name": host,
                "hosts": [host],
                "schedule": "@every 30s"
            }

            yml_configs.append(host_config)
        
        return yml_configs
