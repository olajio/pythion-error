import os
from subprocess import Popen, PIPE
from pathlib import Path


SETUP_PROCESS_PATH = '/usr/local/bin/'
ROOT_FILE_PATH = '~/'
ENCODER_FILE = 'encode.py'
ENCODED_FILE = 'config'
DECODED_FILE = 'roles_anywhere_decoded'
PK_PATH = '/etc/pki/tls/private/HOST.key'
AWS_CONFIG_FILE = 'AWS_CONFIG_FILE'



def decode_configuration():
    process = Popen(['hostname'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    hostname = stdout.decode().strip()
    # print('stdout: ', hostname)
    pk_full_path = PK_PATH.replace('HOST', hostname)
    # print('pk_full: ', pk_full_path)

    # decode_command = f"python3 {SETUP_PROCESS_PATH}{ENCODER_FILE} -d {ROOT_FILE_PATH}{ENCODED_FILE} {ROOT_FILE_PATH}{DECODED_FILE} {pk_full_path}".split()
    decode_command = f"python3 {SETUP_PROCESS_PATH}{ENCODER_FILE} -d {ROOT_FILE_PATH}{ENCODED_FILE} {ROOT_FILE_PATH}{DECODED_FILE} {pk_full_path}"
    # print('decode_command:', decode_command)
    try:
        os.system(decode_command)
        # print('Config file decoded!')
    except Exception as e:
        print('Could not decode the config file to use Roles Anywhere: ', str(e))
    # decode_process = Popen(decode_command, stdout=PIPE, stderr=PIPE)
    # stdout, stderr = process.communicate()
    # print('decode_process: ', stdout)
    # print('decode_process errors: ', stderr)


def export_new_config():
    # export_command = f"export {AWS_CONFIG_FILE}={ROOT_FILE_PATH}{DECODED_FILE}".split()
    # export_command = f"export {AWS_CONFIG_FILE}='{ROOT_FILE_PATH}{DECODED_FILE}'"
    # print('export_command: ', export_command)

    # process = Popen(export_command, stdout=PIPE, stderr=PIPE)
    # print('process: ', process)
    os.environ[AWS_CONFIG_FILE] = f"{ROOT_FILE_PATH}{DECODED_FILE}"
    # os.system(f"export {AWS_CONFIG_FILE}={ROOT_FILE_PATH}{DECODED_FILE}")
    # print('AWS_CONFIG_FILE: ', os.environ[AWS_CONFIG_FILE])


def remove_decoded_file():
    # try:
    #     path_to_remove_file = f"{ROOT_FILE_PATH}{DECODED_FILE}"
    #     print('path_to_remove: ', path_to_remove_file)
    #     file_to_remove = Path(path_to_remove_file)
    #     file_to_remove.unlink()
    #     print('File removed!')
    # except Exception as e:
    #     print('File not removed: ', str(e))
    rm_command = f"rm -f {ROOT_FILE_PATH}{DECODED_FILE}"
    try:
        os.system(rm_command)
        # print('Decoded config removed!')
    except Exception as e:
        print('Failed to remove roles_anywhere file: ', str(e))



if __name__=='__main__':
    # decode_configuration()
    # export_new_config()
    # remove_decoded_file()
    pass