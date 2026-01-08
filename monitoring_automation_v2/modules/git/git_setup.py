import shutil
from git import Repo

BASE_REPO_PATH = '/tmp/'
REPO_NAME = 'hs_elastic_heartbeat_MS01-11ELKHB01'

REPO_URL = 'git@ghe.hedgeserv.net:ITSMA/hs_elastic_hearbeat_MS01-11ELKHB01.git'


class GitHandler:

    def clone_repo(self, repo_url, local_dir):
        repo = Repo.clone_from(repo_url, local_dir)

        print('repo: ', repo)
        return repo


    def get_local_repo(self, local_path):
        repo = Repo(local_path)

        print('repo: ', repo)
        return repo


    def git_pull_master(self, repo):
        master = repo.heads.master
        repo.git.pull('origin', master)


    def commit_updates(self, repo, updated_files, commit_message):
        repo.index.add(updated_files)
        repo.index.commit(commit_message)


    def switch_branch(self, repo, new_branch):
        new_branch = repo.create_head(new_branch, 'HEAD')
        repo.head.reference = new_branch
        print('Branch switched with: ', new_branch)


    def push_commits(self, repo, new_branch):
        repo.git.push('--set-upstream', 'origin', new_branch)
        print('Commit pushed!')

    
    def clean_tmp_repo(self, local_path):
        try:
            shutil.rmtree(local_path)
            print('Temp repo removed!')
        except Exception as e:
            print('Error removing temp repo: ', str(e))




# if __name__=='__main__':
#     # repo = clone_repo(REPO_URL, f"{BASE_REPO_PATH}{REPO_NAME}")
#     repo = get_local_repo(f"{BASE_REPO_PATH}{REPO_NAME}")
#     new_branch = 'test_branch'
#     # git_pull_master(repo)
#     # switch_branch(repo, new_branch)
#     updated_files = ['monitors.d/TEST.yml']
#     commit_updates(repo, updated_files, "Adding new test file")
#     push_commits(repo, new_branch)