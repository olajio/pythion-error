


class Request:

    def __init__(self, **kwargs):
        self.extract_arguments(**kwargs)


    def validate_request(self):
        valid_request = True
        if not self.hosts:
            valid_request = False
        elif self.action == 'monitoring' and not self.env:
            valid_request = False
        elif self.action == 'alerting' and (not self.env or not self.alerts):
            valid_request = False
        # print('valid_request: ', valid_request)
        return valid_request
    

    def extract_arguments(self, **kwargs):
        self.hosts = kwargs.get('hosts', None)
        self.alerts = kwargs.get('alerts', None)
        self.env = kwargs.get('env', None)
        self.action = kwargs.get('action', None)
        self.ticket_id = kwargs.get('ticket_id', None)
    

    def __str__(self):
        request = f"ticket_id: {self.ticket_id}, hosts: {self.hosts}, alerts: {self.alerts}, env: {self.env}, action: {self.action}"
        return request