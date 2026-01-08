import requests


class TicketUpdater:

    def __init__(self, sdp_info=None):
        self.sdp = sdp_info


    def comment_ticket(self, ticket_id, message):
        url = self.sdp['comment_ticket_url'].replace('(ticket_id)', ticket_id)
        print('url: ', url)
        headers = self.sdp['headers']
        input_data = '''{
            "note": {
                "mark_first_response": false,
                "add_to_linked_requests": false,
                "notify_technician": false,
                "show_to_requester": false,
                "description": "(message)"
            }
        }'''.replace('(message)', message)
        data = {
            "input_data": input_data
        }
        print('data: ', data)

        try:
            sdp_response = requests.post(url, headers=headers, params=data)
            print(f'sdp_response on commenting a ticket {ticket_id}: ', sdp_response)
            # print('headers: ', sdp_response.headers)
            print(sdp_response.json())
        except Exception as e:
            print(f'There was an error trying to comment ticket {ticket_id}: \n', e)