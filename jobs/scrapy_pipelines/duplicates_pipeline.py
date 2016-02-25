# -*- coding: utf-8 -*-

"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""

from scrapy.exceptions import DropItem
import sys
import os
import logging

from simple_logging.custom_logging import setup_custom_logger


class DuplicatesPipeline(object):
    # set up the logger
    LOGGING_LEVEL = logging.INFO
    logger = setup_custom_logger('DuplicatesPipeline', LOGGING_LEVEL,
                                 flog=os.path.join(sys.path[0],
                                                   "logs/jobs_spider.log"))

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['url'] in self.ids_seen:
            spider.rootLogger.info("Duplicate job item found for job: %s" % item['url'])
            raise DropItem("Duplicate job item found for job: %s" % item['url'])
        else:
            self.ids_seen.add(item['url'])
            return item