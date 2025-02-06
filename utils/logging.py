import sys
import os
from loguru import logger
from utils.data import DataSet

configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')
fileNames = configurations.get('LogFiles').get('fileNames')
max_size = configurations.get('LogFiles').get('maxSize')

class Logging():
    def __init__(self, name):
        filepath = os.path.join("logs",fileNames.get(name))
        # Extracts the directory from the given path
        log_dir = os.path.dirname(filepath)
        # Creates the directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        # Removes default handlers
        logger.remove()
        logger.add(
            filepath,
            # Rotates log when it reaches max_size (e.g., 10MB)
            rotation=max_size,
            # Keeps logs for 10 days
            retention="10 days",
            # Compresses old logs to save space
            compression="zip",
            level="WARNING",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    def info(self, message):
        logger.info(message)

    def debug(self, message):
        logger.debug(message)

    def error(self, message):
        logger.error(message)

    def warning(self, message):
        logger.warning(message)

    def critical(self, message):
        logger.critical(message)