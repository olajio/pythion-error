#!/usr/bin/env python3
#ytomov - HedgeServ Monitoring Team
# This example shows how the logger can be set up to use a custom JSON format.
import json
import logging
import sys
import datetime

import json_logging

service_type= "monitoring-scripts"
service_name= "logger-testing"

def extra(**kw):
    '''Add the required nested props layer'''
    return {'extra': {'props': kw}}


class CustomJSONLog(json_logging.JSONLogFormatter):
    """
    Customized logger
    """

    def format(self, record):
        time = datetime.datetime.utcnow().isoformat() + "Z"
        json_customized_log_object = ({
            "@timestamp": time,
            "file": {
                "name": record.filename,
                "path": record.pathname,
            },
            "service": {
                "type": service_type,
                "name": service_name,
            },
            "log":{
                "level": record.levelname
            },
            "process": {
                "thread": {
                    "name": record.threadName
                },
                "process": {
                    "name": record.processName
                },
            },
            "labels": {
                "function_name": record.funcName,
                "line_number": record.lineno
            },
            "message": record.getMessage()
        })
        if hasattr(record,'props'):
            record.props.update({
                "function_name": record.funcName,
                "line_number": record.lineno
            })
            json_customized_log_object['labels']=record.props

        return json.dumps(json_customized_log_object)


# You would normally import logger_init and setup the logger in your main module - e.g.
# main.py

if __name__ == '__main__':
    json_logging.init_non_web(custom_formatter=CustomJSONLog, enable_json=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    logger.info('sample log message', extra={'props': {'extra_property': 'extra_value','extra_property2':'extra_value2'}})
