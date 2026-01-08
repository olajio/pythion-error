import yaml
import json
import os
import requests
import base64
import requests
from argparse import ArgumentParser
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#### Config Section
CONSUL_HOSTS = ["https://consul-dev.hedgeservtest.com","https://consul-qa.hedgeservtest.com","https://consul-uat.hedgeservtest.com","https://consul.hedgeservcustomers.com"]
####

class ConsulHandler():

    def __init__(self):
        self._consul_hosts = CONSUL_HOSTS


    def _load_env_from_yaml(self, yaml_string):
        dt = yaml.load(yaml_string, Loader=yaml.FullLoader)
        return dt
    

    def _load_envs_from_consul(self, consul_urls):
        environments = []
        for consul_url in consul_urls:
            try:
                result = requests.get(f"{consul_url}/v1/kv/environment_automation/environments/?recurse=true", verify=False).json()
            except ValueError:
                print ('Consul host unreachable') 
            for env in result:
                if env['Key'].endswith('/definition'):
                    yaml_string = base64.b64decode(env['Value'])
                    environment = self._load_env_from_yaml(yaml_string)
                    environment['status'] = {}
                    environment['consul_host'] = consul_url
                    env_code = env['Key'].split('/')[2]
                    statuses = [{"key": s['Key'], "value": s['Value']} for s in result if f"{env_code}/status/" in s['Key']]
                    for status in statuses:
                        datacenter = status['key'].split('/')[-1]
                        value = base64.b64decode(status['value']).decode("utf-8")
                        environment['status'][datacenter] = value

                    environments.append(environment)

        return environments
    

    def _build_inventory(self, environments, servers):
        inventory = {}
        if len(servers) == 0:
            print('No servers sent to check in consul, returning...')
            return inventory
        for env in environments:
            for server in env['servers']:
                host_lower = server['hostname'].lower() in servers
                host_upper = server['hostname'].upper() in servers
                if host_lower:
                    inventory[server['hostname'].lower()] = {
                        "environment":  env['environment'],
                        "environment_code": env['environment_code'],
                        "environment_status": env['status'][server['datacenter']] if server['datacenter'] in env['status'] else "unknown",
                        "consul_host": env['consul_host'],                
                        "datacenter": server['datacenter'],
                        "os": server['os'],                      
                        "roles": server['roles'],
                        "tags": server['tags']
                    }
                elif host_upper:
                    inventory[server['hostname'].upper()] = {
                        "environment":  env['environment'],
                        "environment_code": env['environment_code'],
                        "environment_status": env['status'][server['datacenter']] if server['datacenter'] in env['status'] else "unknown",
                        "consul_host": env['consul_host'],                
                        "datacenter": server['datacenter'],
                        "os": server['os'],                      
                        "roles": server['roles'],
                        "tags": server['tags']
                    }

        return inventory
    

    def _convert(self, inventory):
        return json.dumps(inventory, indent=4)


    def pull_consul_config_by_hosts(self, servers=[]):
        not_in_consul = []
        environments = self._load_envs_from_consul(self._consul_hosts)
        consul_host_configs = self._build_inventory(environments=environments, servers=servers)
        for server in servers:
            server_config = consul_host_configs.get(server, None)
            if not server_config:
                not_in_consul.append(server)
        
        return (consul_host_configs, not_in_consul)

    

    def __call__(self, servers=[]):
        return self.pull_consul_config_by_hosts(servers)