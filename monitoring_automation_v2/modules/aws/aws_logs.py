from .aws_client import AWSClient


AWS_SERVICE = 'logs'
LOG_STREAMS = {
    'elastic_agents_playbook': '/aws/codebuild/core-shd-ansible-us-east-2-playbook-elastic_agents'
}
LOG_STREAM_LINKS = {
    'elastic_agents_playbook': 'https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#logsV2:log-groups/log-group/$252Faws$252Fcodebuild$252Fcore-shd-ansible-us-east-2-playbook-elastic_agents/log-events/'
}


class ElasticLogs(AWSClient):

    def __init__(self, logs_name='elastic_agents_playbook'):
        super().__init__(service=AWS_SERVICE)
        self._log_stream = LOG_STREAMS.get(logs_name, None)
        self._log_stream_link = LOG_STREAM_LINKS.get(logs_name, None)


    # def describe_log_stream(self):
    #     if not self._log_stream:
    #         return None
        
    #     response = self.client.describe_log_streams(
    #         logGroupName=self._log_stream,
    #         orderBy='LastEventTime',
    #         descending=True,
    #         limit=1
    #     )

    #     print('response: ', response)
    #     return response
    

    def get_log_events(self, build_id):
        if not self._log_stream:
            return None
        
        build_id_suffix = build_id.split(':')[1]
        response = self.client.get_log_events(
            logGroupName=self._log_stream,
            logStreamName=build_id_suffix
        )

        print('response: ', response)
        # for event in response['events']:
        #     print(event)
        #     print('*'*40)

        print('len(response["events"]): ', len(response['events']))
        return response
        # return response['events']
    

    def get_codebuild_logs(self, build_id):
        if not self._log_stream_link:
            return None
        
        build_id_suffix = build_id.split(':')[1]
        logs_url = f"{self._log_stream_link}{build_id_suffix}"
        print('logs_url: ', logs_url)
        return logs_url