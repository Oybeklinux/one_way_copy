import logging


def get_logger(module_name):
    # Create a logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Create handlers
    file_handler = logging.FileHandler('sync_server/app.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatters and add them to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger (to avoid duplicate handlers)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger