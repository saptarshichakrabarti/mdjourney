import logging
import sys
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add run_id to the root of the log entry
        if 'run_id' in record.__dict__:
            log_record['run_id'] = record.__dict__['run_id']

        # Restructure to have a 'details' object
        if 'details' not in log_record:
            log_record['details'] = {}

        # Move all non-standard fields into 'details'
        standard_fields = {'timestamp', 'level', 'name', 'message', 'run_id', 'details'}
        for key, value in record.__dict__.items():
            if key not in standard_fields and key not in log_record['details']:
                log_record['details'][key] = value

        # Ensure run_id is also in details for consistency
        if 'run_id' in log_record:
            log_record['details']['run_id'] = log_record['run_id']


def setup_logger(run_id):
    """Configures a JSON logger for the test suite."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    log_handler = logging.FileHandler(f"test_run_{run_id}.log")

    # Use our custom formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )

    log_handler.setFormatter(formatter)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(log_handler)

    # Add a filter to inject run_id into every log record
    class RunIdFilter(logging.Filter):
        def filter(self, record):
            record.run_id = run_id
            return True

    logger.addFilter(RunIdFilter())

    return logger

if __name__ == '__main__':
    # Example usage:
    run_id = "manual_test_123"
    logger = setup_logger(run_id)
    logger.info("This is a test message.", extra={'details': {'custom_field': 'custom_value'}})
    logger.warning("This is a warning.", extra={'details': {'code': 500}})

    api_logger = logging.getLogger("api_stresser")
    api_logger.info(
        "API request completed",
        extra={
            'details': {
                "endpoint": "/api/projects/p_abc/datasets",
                "method": "GET",
                "status_code": 200,
                "latency_ms": 152,
                "outcome": "success"
            }
        }
    )
    print(f"Log file 'test_run_{run_id}.log' created with test entries.")
