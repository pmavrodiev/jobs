#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-

"""
Created on Sat Oct  3 16:43:50 2015

@author: Pavlin Mavrodiev
"""

from location_classifier import LocationClassifier
from sqlitereader import SqliteReader
from tree_parser import TreeParser
from __future__ import division

import sys


class JobCategorizer(object):

    # takes initialized instances
    def __init__(self, location_classifier, tree_parser, sqlite_reader):
        self.lc = location_classifier
        self.tp = tree_parser
        self.sqlite_reader = sqlite_reader
        self.categorized_nuts = {}  # main data structure

    def populate_tree(self):
        if not (self.lc.ekatte_dict and lc.ekatte_locations and
                tp.initialized):
            # TODO:More graceful logging and exit
            print("Something went wrong with the initialization. Investigate")
            sys.exit(1)

        sqlite_reader.open_db()
        db_url = 1
        db_location = 5
        db_location2 = 6
        all_jobs = self.sqlite_reader.runQuery("SELECT * from bgjobs")

        for row in all_jobs:
            kwargs = {"job_url": row[db_url],
                      "location": row[db_location],
                      "location2": row[db_location2]}
            (nuts3, nuts4) = lc.classify_job_location(**kwargs)
            # skip job if both nuts codes could not be resolved
            if (nuts3, nuts4) == (None, None):
                continue

            # find the category(ies) for this job
            job_categories = self.get_categories(row[db_url])
            if not job_categories:
                continue
            # job_categories = ["банкикредитиране"]
            category_weight = 1 / len(job_categories)
            for cat in job_categories:
                # data is None
                if not self.tp[cat].data:
                    self.tp[cat].data = dict({nuts3:
                                              dict({nuts4:
                                                    category_weight})})
                else:
                    if nuts3 in self.tp[cat].data:
                        self.tp[cat].data[nuts3][nuts4] = self.tp[cat].data[nuts3].get(nuts4, 0) + category_weight
                    else:
                        self.tp[cat].data[nuts3] = dict({nuts4:
                                                         category_weight})

        #
        sqlite_reader.close_db()

    # stub
    def get_categories(self, job_url):
        categories_list = None
        # body - query the tbl_category table
        return categories_list

    # stub
    def json_writer(self):
        # TODO: implement

if __name__ == "__main__":
    sqlite_reader = SqliteReader("../crawled/data-2016-2-6_21-50-52.sqlite")
    lc = LocationClassifier("Ek_atte.csv", "provinces.csv")
    tp = TreeParser("jobCategories.txt")
    tp.build_tree()

    jc = JobCategorizer(lc, tp, sqlite_reader)
    jc.populate_tree()
    jc.tp.show("root")
