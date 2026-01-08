import time

from .ticket_extractor import TicketExtractor
from .ticket_updater import TicketUpdater

SDP = {
    'headers': {
        'Content-Type': 'application/x-www-form-urlencoded',
        'technician_key': 'sdp_key'
    },
    'ticket_url': 'https://support.hedgeserv.com/WorkOrder.do?woMode=viewWO&woID=(ticket_id)',
    'comment_ticket_url': 'https://support.hedgeserv.com/api/v3/requests/(ticket_id)/notes',
    # 'url': 'https://support.hedgeserv.com/WorkOrder.do?woMode=viewWO&woID=',
    'url': 'https://support.hedgeserv.com/api/v3/requests',
    "list_info": {
        'list_info': {
            'row_count': 100,
            'start_index': 1,
            'sort_field': 'id',
            'sort_order': 'asc',
            'get_total_count': 'true',
            'fields_required': [
                'id',
                'status.name',
                'group.name',
                'subject',
                # 'subject.name',
                # 'technician.name',
                # 'requester.name'
                'created_time',
                'priority.name',
                'udf_fields.udf_sline_75301',
                # 'udf_fields.udf_sline_75302',
                'udf_fields.udf_pick_75601',
                'udf_fields.udf_pick_77105'
            ]
            # "search_criteria": '<PLACEHOLDER>'
        }
    }
}


SEARCH_CRITERIA = [
    {
        'field': 'status.name',
        'condition': 'is',
        'values': [
            'Open',
            # 'In Progress',
            # 'Closed',
            # 'Canceled',
            # 'Resolved',
            # 'OnHold'
        ]
    },
    # {
    #     'field': 'created_time',
    #     'condition': 'greater than',
    #     'value': '<IN_MINUTES>',
    #     'logical_operator': 'and'
    # },
    # {
    #    'field': 'created_time',
    #     'condition': 'lesser than',
    #     'value': '<IN_MINUTES>',
    #     'logical_operator': 'and' 
    # },
    {
        'field': 'group.name',
        'condition': 'is',
        'logical_operator': 'and',
        'value': 'Monitoring and Analytics'
    }
]



class TicketHandler:

    def __init__(self, search_start_time=30, search_end_time=0, elk_logger=None, sdp_key=None):
        # self.search_criteria = self.build_search_criteria_for_time_period(created_after=search_start_time, created_before=search_end_time)
        self.search_criteria = SEARCH_CRITERIA
        self.sdp = self.build_requests_query(self.search_criteria)
        self.add_key(sdp_key)
        self.ticket_extractor = TicketExtractor(self.sdp)
        self.ticket_updater = TicketUpdater(self.sdp)
        self.elk_logger = elk_logger


    def run_extract(self):
        sdp_response = self.ticket_extractor.get_ticket_details()
        requests_to_action, non_actionable_requests = self.ticket_extractor.extract_hosts_and_alerts(sdp_response)
        final_requests_to_action, wrong_requests = self.ticket_extractor.format_host_arguments(requests_to_action)
        
        return final_requests_to_action, wrong_requests
    

    def add_ticket_note(self, ticket_id, message):
        self.ticket_updater.comment_ticket(ticket_id=ticket_id, message=message)


    def build_ticket_link(self, ticket_id=None):
        if not ticket_id:
            print('A ticket id is needed to get a link to a specific ticket...')
            return None

        return SDP['ticket_url'].replace('(ticket_id)', ticket_id)
    

    def build_search_criteria_for_time_period(self,created_after=30, created_before=0):
        now_in_millis = int(time.time() * 1000)
        SEARCH_CRITERIA[1]['value'] = now_in_millis - (created_after * 60000)
        SEARCH_CRITERIA[2]['value'] = now_in_millis - (created_before * 60000)
        return SEARCH_CRITERIA


    def build_requests_query(self, search_criteria):
        SDP['list_info']['list_info']['search_criteria'] = search_criteria
        return SDP
    
    def add_key(self, sdp_key):
        self.sdp['headers']['technician_key'] = sdp_key