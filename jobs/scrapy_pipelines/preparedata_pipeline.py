# -*- coding: utf-8 -*-

"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""

from scrapy.exceptions import DropItem
import os
import sys
import logging

from simple_logging.custom_logging import setup_custom_logger

class PrepareDataPipeline(object):
    # set up the logger
    LOGGING_LEVEL = logging.INFO
    logger = setup_custom_logger('PrepareDataPipeline', LOGGING_LEVEL,
                                 flog=os.path.join(sys.path[0],
                                                   "logs/jobs_spider.log"))
    def process_item(self, item, spider):
        #Date
        if 'date' in item:
            #get the date string
            try:
                date = item['date'].split(':')[1].split(' ')[0]
                item['date'] = date
            except IndexError:
                PrepareDataPipeline.logger.warning("Cannot parse date %s for job %s" % (item['date'], item['url']))
                DropItem("Cannot parse date %s for job %s" % (item['date'], item['url']))

        #default values for unspecified keys
        for item_key in item.fields:
            if not item_key in item.keys():
                item[item_key] = ''.encode('utf-8')
            item[item_key] = item[item_key].decode('utf-8')
        # check if the item is a valid job ad.
        # sometimes the job is expired but is still present in the search results
        # hence the url will point to a job-expired-page
        # if this is the case all item fields will be empty, except the url
        jobValid=False
        for item_key in item:
            if item_key != 'url' and item[item_key] != '':
                jobValid=True
                break
        if not jobValid:
            PrepareDataPipeline.logger.warning("Job expired %s" % item['url'])
            DropItem("Job expired %s" % item['url'])
        else:
            item['description_requirements'] = item['description_requirements'].encode('utf-8').encode('zlib')
            return item
