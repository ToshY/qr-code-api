import logging
import json


class CustomJSONFormatter(logging.Formatter):
    def __init__(self, fmt):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        logging.Formatter.format(self, record)
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)

        return json.dumps(get_log(record), indent=None)


def get_log(record):
    d = {
        "time": record.asctime,
        "process_name": record.processName,
        "process_id": record.process,
        "thread_name": record.threadName,
        "thread_id": record.thread,
        "level": record.levelname,
        "logger_name": record.name,
        "pathname": record.pathname,
        "line": record.lineno,
        "message": record.getMessage(),
    }

    if record.exc_text:
        d["exception_text"] = record.exc_text

    if hasattr(record, "extra_info"):
        d["request"] = record.extra_info["request"]
        d["trace_id"] = record.extra_info["trace_id"]
        d["response"] = record.extra_info["response"]

    return d
