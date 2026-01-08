SDP_MESSAGE = 'This ticket was processed by the monitoring automation framework'


class BaseAction:

    def __init__(self, elk_key, request, **kwargs):
        self.elk_key = elk_key
        self.request = request
        self.extract_arguments(**kwargs)

    def execute_action(self):
        '''Empty method to be implemented by child Action classes.'''
        pass

    def update_sdp_request(self, message=SDP_MESSAGE):
        if self.ticket_handler and self.request.ticket_id:
            try:
                self.ticket_handler.add_ticket_note(self.request.ticket_id, message)
            except Exception as e:
                print('There was an error trying to update the sdp request: ', e)
                pass

    def extract_arguments(self, **kwargs):
        self.elk_logger = kwargs.get('elk_logger', None)
        self.ticket_handler = kwargs.get('ticket_handler', None)
        self.ticket_link = kwargs.get('ticket_link', None)

    def __str__(self):
        fmt = f"{self.__class__.__name__}: hosts -> {self.request.hosts}, alerts -> {self.request.alerts}, action -> {self.request.action}"
        return fmt
