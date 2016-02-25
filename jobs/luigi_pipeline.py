# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 01:23:40 2016

@author: Pavlin Mavrodiev
"""

import luigi
import os
import sys

from luigi import file
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def generate_sqlite_fname():
    # generate the sqlite filename
    sqlite_db = os.path.join(sys.path[0], "./crawled/data")
    # append a timestamp to the name
    from datetime import datetime
    dt = datetime.now()
    tt = dt.timetuple()
    timestamp = str(tt.tm_year) + '-' + str(tt.tm_mon) + '-' + \
    str(tt.tm_mday) + '_' + str(tt.tm_hour) + '-' + \
    str(tt.tm_min)  + '-' + str(tt.tm_sec)
    #
    return sqlite_db + '-' + timestamp + '.sqlite'


class TaskSpider(luigi.Task):
    sqlite_db = generate_sqlite_fname()

    def output(self):
        return [file.LocalTarget(path=TaskSpider.sqlite_db)]

    def run(self):
        #
        process = CrawlerProcess(get_project_settings())
        process.crawl("jobsSpider",  sqlitedb=TaskSpider.sqlite_db)
        process.start()
        # done

if __name__ == "__main__":
    luigi.run()
