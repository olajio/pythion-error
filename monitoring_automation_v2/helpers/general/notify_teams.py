import requests
import json

# Teams connectors webhook
TEST_WEBHOOK_URL = 'https://hedgeservcorp.webhook.office.com/webhookb2/39110328-ac0c-49b2-9261-eb9e4c8b1ae4@39e63823-376a-43fc-9fdd-4a3932faab97/IncomingWebhook/9f1709cd85a34a71b97e5e492cf5d1fc/e3eba5a8-883d-40d1-83e2-1430ecc2abf3'
# PROD_WEBHOOK_URL = 'https://hedgeservcorp.webhook.office.com/webhookb2/39110328-ac0c-49b2-9261-eb9e4c8b1ae4@39e63823-376a-43fc-9fdd-4a3932faab97/IncomingWebhook/7df33208264949f7bd3a95110ec283e7/38575604-9373-497f-97fd-6f3d1bd9c254'

# Teams workflow webhook
PROD_WEBHOOK_URL = 'https://prod-19.westus.logic.azure.com:443/workflows/d5d9dde59c7641b2b35f1ca9f4d960b3/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IhaSTPiTfsFnd2UrKZEO4tr95ioQVk7UWGReejMkRwY'


def notify_hosts_added(url=PROD_WEBHOOK_URL, hosts_report=None, ticket_id=None, ticket_link=None):
    if not hosts_report:
        print('No report was sent, skipping notification!')
        return None

    # New event template using workflows
    event = {
        'url': url,
        'headers': {
            'Content-Type': 'application/json'
        },
        'template': {
            'type': 'message',
            'attachments': [
                {
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'content': {
                        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                        'type': 'AdaptiveCard',
                        'version': '1.0',
                        'msteams': {
                            'width': 'full'
                        },
                        'body': [
                            {
                                'type': 'TextBlock',
                                'text': f'Setup alerting on hosts report from request - {ticket_id}',
                                'id': 'Title',
                                'spacing': 'Medium',
                                'horizontalAlignment': 'Center',
                                'size': 'ExtraLarge',
                                'weight': 'Bolder',
                                'color': 'Accent',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Setup Monitoring/Alerting ticket with id - {ticket_id}: {ticket_link}',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts monitored in Elastic: {hosts_report.get('elastic_found_hosts', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts not monitored in Elastic: {hosts_report.get('elastic_not_found', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts with configs in Consul: {hosts_report.get('consul_configs_hosts', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts with missing configs in Consul: {hosts_report.get('consul_not_found', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts setup for alerting: {hosts_report.get('sdp_hosts', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"Hosts not setup for alerting: {hosts_report.get('sdp_error_hosts', [])}",
                                'wrap': 'true'
                            }
                        ]
                    }
                }
            ]
        }
    }

    return send_message(event)



def notify_url_configs_added_to_git(url=PROD_WEBHOOK_URL, hosts_report=None, ticket_id=None, ticket_link=None):
    # New event template using workflows
    event = {
        'url': url,
        'headers': {
            'Content-Type': 'application/json'
        },
        'template': {
            'type': 'message',
            'attachments': [
                {
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'content': {
                        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                        'type': 'AdaptiveCard',
                        'version': '1.0',
                        'msteams': {
                            'width': 'full'
                        },
                        'body': [
                            {
                                'type': 'TextBlock',
                                'text': f'Setup monitoring/alerting on urls report from request - {ticket_id}',
                                'id': 'Title',
                                'spacing': 'Medium',
                                'horizontalAlignment': 'Center',
                                'size': 'ExtraLarge',
                                'weight': 'Bolder',
                                'color': 'Accent',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Setup Monitoring/Alerting ticket with id - {ticket_id}: {ticket_link}',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"URLs added to git: {hosts_report.get('hosts', [])}",
                                'wrap': 'true'
                            }
                        ]
                    }
                }
            ]
        }
    }

    return send_message(event)


def notify_urls_added(url=PROD_WEBHOOK_URL, hosts_report=None, ticket_id=None, ticket_link=None):
    if not hosts_report:
        print('No report was sent, skipping notification!')
        return None

    # New event template using workflows
    event = {
        'url': url,
        'headers': {
            'Content-Type': 'application/json'
        },
        'template': {
            'type': 'message',
            'attachments': [
                {
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'content': {
                        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                        'type': 'AdaptiveCard',
                        'version': '1.0',
                        'msteams': {
                            'width': 'full'
                        },
                        'body': [
                            {
                                'type': 'TextBlock',
                                'text': f'Setup monitoring/alerting on urls report from request - {ticket_id}',
                                'id': 'Title',
                                'spacing': 'Medium',
                                'horizontalAlignment': 'Center',
                                'size': 'ExtraLarge',
                                'weight': 'Bolder',
                                'color': 'Accent',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Setup Monitoring/Alerting ticket with id - {ticket_id}: {ticket_link}',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"URLs added to sdp_amdb for alerting: {hosts_report.get('sdp_hosts', [])}",
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f"URLs not added to sdp_amdb for alerting: {hosts_report.get('sdp_error_hosts', [])}",
                                'wrap': 'true'
                            }
                        ]
                    }
                }
            ]
        }
    }

    return send_message(event)


def notify_hosts_removed(url=PROD_WEBHOOK_URL, hosts_removed=[], hosts_failed=[], ticket_id=None, ticket_link=None):

    # New event template using workflows
    event = {
        'url': url,
        'headers': {
            'Content-Type': 'application/json'
        },
        'template': {
            'type': 'message',
            'attachments': [
                {
                    'contentType': 'application/vnd.microsoft.card.adaptive',
                    'content': {
                        '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                        'type': 'AdaptiveCard',
                        'version': '1.0',
                        'msteams': {
                            'width': 'full'
                        },
                        'body': [
                            {
                                'type': 'TextBlock',
                                'text': f'Remove alerting on hosts report from request - {ticket_id}',
                                'id': 'Title',
                                'spacing': 'Medium',
                                'horizontalAlignment': 'Center',
                                'size': 'ExtraLarge',
                                'weight': 'Bolder',
                                'color': 'Accent',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Remove Monitoring/Alerting ticket with id - {ticket_id}: {ticket_link}',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Successfully removed alerts for: {hosts_removed}',
                                'wrap': 'true'
                            },
                            {
                                'type': 'TextBlock',
                                'text': f'Failed to remove alerts for: {hosts_failed}',
                                'wrap': 'true'
                            }
                        ]
                    }
                }
            ]
        }
    }

    return send_message(event)


def send_message(event):
    url = event.get('url', None)
    headers = event.get('headers', None)
    json_data = event.get('template', None)
    # print(f"URL: {url}\nHeaders: {headers}\nData: {json_data}")
    try:
        # response = requests.post(url=url, headers=headers, json=json_data).json()
        response = requests.post(url=url, headers=headers, json=json_data, verify=False)
        # print('Response from msteasm: \n', response)
    except Exception as e:
        print('Failed to send message to teams:\n', str(e))
        response = {}
    return response