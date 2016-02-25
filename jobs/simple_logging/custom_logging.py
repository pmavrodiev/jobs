# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 15:25:31 2016

@author: Pavlin Mavrodiev
"""

import logging


def setup_custom_logger(name, logging_level, flogging_level=logging.DEBUG,
                        flog='db.log'):
    formatter = logging.Formatter(fmt=("%(asctime)s - %(levelname)s "
                                       "- %(module)s - %(message)s"))

    shandler = logging.StreamHandler()
    shandler.setFormatter(formatter)
    shandler.setLevel(logging_level)

    fhandler = logging.FileHandler(flog)
    fhandler.setFormatter(formatter)
    fhandler.setLevel(flogging_level)

    logger = logging.getLogger(name)
    logger.setLevel(flogging_level)
    logger.addHandler(shandler)
    logger.addHandler(fhandler)
    return logger
