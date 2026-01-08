"""
This script is designed to easily give us a chance to verify whether we have monitoring/alerting
enabled for a specific host or a group of hosts.
Usage:
python3 check_monitors.py --api_key '<API_KEY>'
"""
from argparse import ArgumentParser
from modules.elastic.monitor_setup import MonitorHandler
import json


def main(api_key):
    with open('monitoring_params.json', 'r') as f:
        params = json.load(f)
    
    hosts = params['hosts']

    elk_client = MonitorHandler(api_key=api_key)

    hosts_with_monitoring, hosts_without_monitoring = elk_client.validate_hosts(hosts)

    hosts_alerts = []
    hosts_no_alerts = []
    check_alerts(hosts_alerts, hosts_no_alerts, hosts_with_monitoring, elk_client)
    check_alerts(hosts_alerts, hosts_no_alerts, hosts_without_monitoring, elk_client)

    print('Hosts with monitoring:\n', hosts_with_monitoring)
    print('*'*40)
    print('Hosts without monitoring:\n', hosts_without_monitoring)
    print('='*80)
    print('Hosts with alerts enabled:\n', hosts_alerts)
    print('*'*40)
    print('Hosts with no alerts:\n', hosts_no_alerts)

    print('Filter for sdp_amdb:')
    # sdp_filter = pass



def check_alerts(hosts_alerts, hosts_no_alerts, host_list, elk_client):
    for host in host_list:
        res = elk_client.check_host_alerts(host)
        if not res:
            hosts_no_alerts.append(host)
        else:
            print('Res for enabled alert: ', res)
            hosts_alerts.append(host)



if __name__=='__main__':
    parser = ArgumentParser(description='Verify whether we have monitoring/alerting enabled.')
    parser.add_argument('--api_key', required=True)

    args = parser.parse_args()

    api_key = args.api_key

    main(api_key)