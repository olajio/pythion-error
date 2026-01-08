FILE = 'handled_request.txt'


def save_processed_requests(processed_requests, file=FILE):
    with open(file, 'w') as f:
        # f.write(str(processed_requests))
        for request_id in processed_requests:
            f.write(request_id)
            f.write('\n')


def check_request(request_id, processed_requests):
    processed = False
    if request_id in processed_requests:
        processed = True
    
    return processed


def load_processed_requests(file=FILE):
    with open(file, 'r') as f:
        processed_requests = f.readlines()

    for i, req in enumerate(processed_requests):
        processed_requests[i] = req[:-1]
    
    return processed_requests


def remove_missing_requests(found_requests, old_requests):
    latest_requests = []
    for request in old_requests:
        if request in found_requests:
            latest_requests.append(request)
    
    for request in found_requests:
        if request not in latest_requests:
            latest_requests.append(request)

    return latest_requests
