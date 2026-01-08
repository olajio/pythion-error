from .elastic_client import ElasticClient
from datetime import datetime


ELASTIC_HOST = 'https://de26459b90754aceb3234fe7969cb1ee.us-east-1.aws.found.io:9243' # CCS
API_KEY = ''
TEST_INDICES = 'prod:metricbeat-*,qa:metricbeat-*,dev:metricbeat-*' # Looking from CCS
URL_TEST_INDICES = 'prod:heartbeat-*'
SDP_AMDB_INDEX = 'sdp_amdb'

class MonitorHandler(ElasticClient):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key)
        self.test_indices = test_indices
        self.sdp_amdb = SDP_AMDB_INDEX


    def validate_hosts(self, servers):
        servers = self._update_hosts_lower_upper(servers)
        query = self._get_search_query(servers)
        print('query: ', query)
        results = self.es.search(index=self.test_indices, body=query, request_timeout=100)
        found_hosts = []
        # print('Results: ', results)
        for host in results['aggregations']['hosts']['buckets']:
            # print('Host: ', host['key'])
            found_hosts.append(host['key'])
            servers.remove(host['key'].lower())
            servers.remove(host['key'].upper())

        not_found_hosts = []
        # print('Servers: ', servers)
        for server in servers:
            if server.lower() not in not_found_hosts:
                not_found_hosts.append(server.lower())
        return found_hosts, not_found_hosts
    

    def check_host_alerts(self, host):
        try:
            result = self.es.get(index=self.sdp_amdb, id=host)
            return result['_source']
        except Exception as e:
            print('Error:\n', str(e))
            return None
    

    def _update_hosts_lower_upper(self, servers):
        # print('List of servers to validate initial: ', servers)
        updated_server_list = []
        for host in servers:
            updated_server_list.append(host.lower())
            updated_server_list.append(host.upper())
        
        # print('Updated host list: ', updated_server_list)
        return updated_server_list
            


    def _get_search_query(self, hosts=None):

        query = {
            "size": 0,
            "query": {
                "bool": {
                "filter": [
                    {
                    "terms": {
                        "host.hostname": hosts
                    }
                    },
                    {
                    "range": {
                        "@timestamp": {
                        "gte": "now-5m"
                        }
                    }
                    }
                ]
                }
            },
            "aggs": {
                "hosts": {
                "terms": {
                    "field": "host.hostname",
                    "size": 1000
                }
                }
            }
        }

        return query
    

    def _get_domain_from_datacenter(self, datacenter):
        datacenter_domains = {
            'CS01': 'hedgeservcustomers.com',
            'CS51': 'hedgeservcustomers.com',
            'CW01': 'hedgeservweb.com',
            'CW51': 'hedgeservweb.com',
            'TS01': 'hedgeservtest.com',
            'TS51': 'hedgeservtest.com',
            'TW01': 'hedgeservtestweb.com',
            'TW51': 'hedgeservtestweb.com',
            'EW01': 'hew.com',
            'EW51': 'hew.com',
            'ES01': 'funddevelopmentservices.com',
            'ES03': 'funddevelopmentservices.com',
            'ES51': 'funddevelopmentservices.com',
            'MS01': 'hedgeservmgmt.com',
            'MS51': 'hedgeservmgmt.com',
            'VS01': 'hedgeservvendor.com',
            'VS51': 'hedgeservvendor.com'
        }

        return datacenter_domains.get(datacenter.upper(), '')
    

    def _remove_domain_from_hosts(self, hosts):
        updated_hosts = []
        for host in hosts:
            if '.' in host:
                hostname = host.split('.')[0]
                updated_hosts.append(hostname)
            else:
                updated_hosts.append(host)
        
        return updated_hosts


    def _add_domain_to_hosts(self, hosts):
        updated_hosts = []
        for host in hosts:
            if '.' in host:
                updated_hosts.append(host)
            else:
                datacenter = host.split('-')[0].upper()
                domain = self._get_domain_from_datacenter(datacenter)
                if domain == '':
                    hostname = host
                else:
                    hostname = f"{host}.{domain}"
                updated_hosts.append(hostname)
        
        return updated_hosts



class AlertHandler(MonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)

    
    def save_sdp_amdb(self, hosts=None, alerts=[], consul_hosts=None):
        if not hosts or not consul_hosts:
            # print('Hosts and consul_configs need to be specified to create entry for a host in the sdp_amdb index!')
            return None, None
        
        hosts_without_errors = []
        hosts_with_errors = []
        for host in hosts:
            if host not in consul_hosts:
                # print(f'No consul information found for host: {host}; continuing to next host!')
                continue
            
            doc = self.check_host_alerts(host)
            if not doc:
                doc = self._get_save_host_template(consul_values=consul_hosts[host], host=host, alerts=alerts)
            else:
                for alert in alerts:
                    doc['group'].append(alert)

            try:
                res = self.es.index(index=SDP_AMDB_INDEX, id=host, body=doc)
                print (f'Res for host: {host} is: ', res)
                if res['result'].lower() == 'updated' or res['result'].lower() == 'created':   
                    hosts_without_errors.append(host)
                else:
                    hosts_with_errors.append(host)
            except Exception as e:
                print(f"There was an error for host {host}:\n", str(e))
                hosts_with_errors.append(host)
        return hosts_without_errors, hosts_with_errors


    def _get_save_host_template(self, consul_values, host, alerts):
        domain = self._get_domain_from_datacenter(consul_values.get('datacenter', ''))
        tags = consul_values.get('tags', None)

        template = {
            "hostname": host,
            "os": consul_values.get('os', ''),
            "domain": domain,
            "client": consul_values.get('environment_code', ''),
            "datacenter": consul_values.get('datacenter', ''),
            "group": alerts,
            "app_code": tags.get('hs:std:app-code', '') if tags else '',
            "alert_status": "enabled" ,
            "svc_operator": tags.get('hs:std:svc-operator', '') if tags else '',
            "svc_software_owner": tags.get('hs:std:svc-software-owner', '') if tags else '',
            "type": "server",
            "record": {
                "created_by": "monitoring_automation_process",
                "created_timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        }

        return template
    


class URLHandler(MonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=URL_TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)


    def save_url_monitor_records(self, urls=None, alerts=[]):
        if not urls or len(urls) < 1:
            print('No urls were passed to be saved in sdp_amdb!')
            return None, None
        
        urls_without_errors = []
        urls_with_errors = []

        for url in urls:
            url = url.replace('/', '-')

            doc = self.check_host_alerts(url)
            if not doc:
                doc = self._get_save_url_template(url, alerts)
            else:
                for alert in alerts:
                    doc['group'].append(alert)

            try:
                res = self.es.index(index=SDP_AMDB_INDEX, id=url, body=doc)
                print(f'res for url - {url} is: ', res)
                if res['result'].lower() == 'updated' or res['result'].lower() == 'created':   
                    urls_without_errors.append(url)
                else:
                    urls_with_errors.append(url)
            except Exception as e:
                print(f"There was an error for url - {url}:\n", str(e))
                urls_with_errors.append(url)
        
        return urls_without_errors, urls_with_errors


    def _get_save_url_template(self, monitor, alerts):

        template = {
            'hostname': monitor,
            'alert_status': 'enabled',
            'type': 'url',
            'group': alerts,
            'app_code': '',
            'record': {
                "created_by": "monitoring_automation_process",
                "created_timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        }

        return template
    


class ESXHandler(MonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)

    
    def validate_hosts(self, hosts):
        updated_hosts = self._add_domain_to_hosts(hosts)
        found_full_hosts, not_found_full_hosts = super().validate_hosts(updated_hosts)
        found_hostnames = self._remove_domain_from_hosts(found_full_hosts)
        not_found_hostnames = self._remove_domain_from_hosts(not_found_full_hosts)
        return found_hostnames, not_found_hostnames


    def _get_search_query(self, hosts=None):

        query = {
            "size": 0,
            "query": {
                "bool": {
                "filter": [
                    {
                    "terms": {
                        "vsphere.host.name": hosts
                    }
                    },
                    {
                    "range": {
                        "@timestamp": {
                        "gte": "now-15m"
                        }
                    }
                    }
                ]
                }
            },
            "aggs": {
                "hosts": {
                "terms": {
                    "field": "vsphere.host.name",
                    "size": 1000
                }
                }
            }
        }

        return query
    

    def save_sdp_amdb(self, hosts=None, alerts=[]):
        if not hosts:
            return None, None
        
        hosts_without_errors = []
        hosts_with_errors = []
        for host in hosts:
            doc = self.check_host_alerts(host)
            if not doc:
                doc = self._get_save_host_template(host=host, alerts=alerts)
            else:
                for alert in alerts:
                    doc['group'].append(alert)

            try:
                res = self.es.index(index=SDP_AMDB_INDEX, id=host, body=doc)
                print (f'Res for host: {host} is: ', res)
                if res['result'].lower() == 'updated' or res['result'].lower() == 'created':   
                    hosts_without_errors.append(host)
                else:
                    hosts_with_errors.append(host)
            except Exception as e:
                print(f"There was an error for host {host}:\n", str(e))
                hosts_with_errors.append(host)
        return hosts_without_errors, hosts_with_errors


    def _get_save_host_template(self, host, alerts):
        domain = self._get_domain_from_datacenter(host.split('-')[0])

        template = {
            "hostname": host,
            "domain": domain,
            "client": "Shared services",
            "group": alerts,
            "app_code": "",
            "alert_status": "enabled" ,
            "type": "VMware ESX/ESXi",
            "record": {
                "created_by": "monitoring_automation_process",
                "created_timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        }

        return template
    


class DatastoreHandler(MonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)

    
    def validate_hosts(self, hosts):
        found_hosts, not_found_hosts = super().validate_hosts(hosts)
        return found_hosts, not_found_hosts


    def _get_search_query(self, hosts=None):

        query = {
            "size": 0,
            "query": {
                "bool": {
                "filter": [
                    {
                    "terms": {
                        "vsphere.datastore.name": hosts
                    }
                    },
                    {
                    "range": {
                        "@timestamp": {
                        "gte": "now-60m"
                        }
                    }
                    }
                ]
                }
            },
            "aggs": {
                "hosts": {
                "terms": {
                    "field": "vsphere.datastore.name",
                    "size": 1000
                }
                }
            }
        }

        return query
    

    def save_sdp_amdb(self, hosts=None, alerts=[]):
        if not hosts:
            return None, None
        
        hosts_without_errors = []
        hosts_with_errors = []
        for host in hosts:
            doc = self.check_host_alerts(host)
            if not doc:
                doc = self._get_save_host_template(host=host, alerts=alerts)
            else:
                for alert in alerts:
                    doc['group'].append(alert)

            try:
                res = self.es.index(index=SDP_AMDB_INDEX, id=host, body=doc)
                print (f'Res for host: {host} is: ', res)
                if res['result'].lower() == 'updated' or res['result'].lower() == 'created':   
                    hosts_without_errors.append(host)
                else:
                    hosts_with_errors.append(host)
            except Exception as e:
                print(f"There was an error for host {host}:\n", str(e))
                hosts_with_errors.append(host)
        return hosts_without_errors, hosts_with_errors


    def _get_save_host_template(self, host, alerts):

        template = {
            "hostname": host,
            "group": alerts,
            "app_code": "",
            "alert_status": "enabled" ,
            "type": "datastore",
            "record": {
                "created_by": "monitoring_automation_process",
                "created_timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        }

        return template



class DeleteMonitorHandler(MonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)


    def remove_sdp_host(self, hosts=None):
        if not hosts:
            print('No hosts were specified for deletion!')
            return None, None
        
        hosts_removed = []
        hosts_failed = []
        for host in hosts:
            try:
                res = self.es.delete(index=SDP_AMDB_INDEX, id=host)
                print(f'Res on deleting host: {host} from sdp_amdb is: ', res)
                if res['result'] == 'deleted':
                    if not host.upper() in hosts_removed and not host.lower() in hosts_removed:
                        hosts_removed.append(host)
                        if host.upper() in hosts_failed:
                            hosts_failed.remove(host.upper())
                        if host.lower() in hosts_failed:
                            hosts_failed.remove(host.lower())
            except Exception as e:
                print(f"Exception trying to delete sdp_amdb record for host {host}\n", str(e))
                if 'NotFoundError' in str(e):
                    if not host.upper() in hosts_removed and not host.lower() in hosts_removed:
                        hosts_removed.append(host)
                        if host.upper() in hosts_failed:
                            hosts_failed.remove(host.upper())
                        if host.lower() in hosts_failed:
                            hosts_failed.remove(host.lower())
                elif not host.lower() in hosts_removed and not host.lower() in hosts_failed and \
                    not host.upper() in hosts_removed and not host.lower() in hosts_removed:
                    hosts_failed.append(host)

        return hosts_removed, hosts_failed


class DeleteESXTypeMonitor(DeleteMonitorHandler):

    def __init__(self, elastic_host=ELASTIC_HOST, api_key=API_KEY, test_indices=TEST_INDICES):
        super().__init__(elastic_host=elastic_host, api_key=api_key, test_indices=test_indices)

    
    def remove_sdp_host(self, hosts=None):
        if not hosts:
            print('No hosts were specified for deletion!')
            return None, None
        
        domain_hosts = self._add_domain_to_hosts(hosts)
        short_name_hosts = self._remove_domain_from_hosts(hosts)

        domain_hosts_removed, domain_hosts_not_removed = super().remove_sdp_host(domain_hosts)
        short_name_hosts_removed, short_name_hosts_not_removed = super().remove_sdp_host(short_name_hosts)

        final_hosts_removed = domain_hosts_removed + short_name_hosts_removed
        final_hosts_not_removed = domain_hosts_not_removed + short_name_hosts_not_removed

        return final_hosts_removed, final_hosts_not_removed