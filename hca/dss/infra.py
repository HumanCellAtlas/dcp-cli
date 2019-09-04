#!/usr/bin/env python
# coding: utf-8
import logging


def get_logger(obj, level=None):
    logging.basicConfig()
    logger = logging.getLogger(obj.__name__)
    if level is not None:
        logger.setLevel(level)

    return logger
