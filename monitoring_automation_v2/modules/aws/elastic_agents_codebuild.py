import time
from .aws_client import AWSClient

BUILD_PROJECT_NAME = 'core-shd-ansible-us-east-2-playbook-elastic_agents'
AWS_SERVICE = 'codebuild'


class ElasticAgentsCodebuild(AWSClient):

    def __init__(self):
        super().__init__(service=AWS_SERVICE)


    def _start_codebuild(self, env, servers):
        response = self.client.start_build(
            projectName=BUILD_PROJECT_NAME,
            environmentVariablesOverride=[
                {
                    'name': 'ENVIRONMENT',
                    'value': env
                },
                {
                    'name': 'LIST',
                    'value': servers
                }
            ]
        )

        print('Response is: \n', response)
        return response

    
    def _get_build_status(self, build_id=None):
        if not build_id or len(build_id) == 0:
            print('Build id cannot be empty!')
            return None
        response = self.client.batch_get_builds(
            ids=[
                build_id
            ]
        )

        # print('Build status: \n', response)
        print('Build status: \n', response['builds'][0])
        print('*'*40)
        print(response['builds'][0]['currentPhase'])
        print(response['builds'][0]['buildStatus'])
        print('*'*40)
        print(response['builds'][0]['phases'])
        return response
    
    
    def install_agents(self, hosts, env):
        servers_to_run = ''
        for host in hosts:
            servers_to_run += host.lower() + ',' + host.upper() + ','
            # print('Servers to run in progress: ', servers_to_run)
        servers_to_run = servers_to_run[:-1]
        
        codebuild_response = self._start_codebuild(env=env, servers=servers_to_run)
        codebuild_id = codebuild_response['build']['id']
        print('CodebuildID: ', codebuild_id)
        while True:
            cb_status = self._get_build_status(codebuild_id)
            current_phase = cb_status['builds'][0]['currentPhase']

            if current_phase == 'COMPLETED':
                print('Build completed!')
                break
            else:
                print('Sleeping for 5 minutes - build still not finished: ', current_phase)
                time.sleep(300)
        
        return codebuild_id