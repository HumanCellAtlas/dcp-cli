#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import logging


def get_logger(obj, level=None):
    logging.basicConfig()
    logger = logging.getLogger(obj.__name__)
    if level is not None:
        logger.setLevel(level)

    return logger
