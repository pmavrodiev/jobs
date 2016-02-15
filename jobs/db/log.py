# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 15:25:31 2016

@author: Pavlin Mavrodiev
"""

import logging


def setup_custom_logger(name, logging_level):
    formatter = logging.Formatter(fmt=("%(asctime)s - %(levelname)s "
                                       "- %(module)s - %(message)s"))

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)
    logger.addHandler(handler)
    return logger
