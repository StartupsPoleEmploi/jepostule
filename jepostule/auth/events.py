import logging


# TODO we should probably configure the logger destination somewhere. In syslog maybe?
logger = logging.getLogger(__name__)


def log(event):
    logger.info(event)
