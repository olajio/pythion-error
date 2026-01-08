import boto3

class AWSClient():

    def __init__(self, service=None):
        self._set_client(service)


    def _set_client(self, service):
        self.client = boto3.client(service)