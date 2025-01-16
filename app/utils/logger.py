# logger.py
import logging

logging.basicConfig(level=logging.INFO)

def log_error(error):
    logging.error(f"Error: {error}")
