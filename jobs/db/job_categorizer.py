#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-

"""
Created on Sat Oct  3 16:43:50 2015

@author: Pavlin Mavrodiev
"""
from __future__ import division

from location_classifier import LocationClassifier
from sqlitereader import SqliteReader
from tree_parser import TreeParser
from basic_tree import sanitize_id
from location_classifier import nowhitespaces
from custom_logging import setup_custom_logger

import logging
import sqlite3 as sqlite
import re
import os


# a regex to split a string on the many hyphens in existence
hyphens = (u"\u002D", u"\u058A", u"\u05BE", u"\u1400", u"\u1806",
           u"\u2010", u"\u2011", u"\u2012", u"\u2013", u"\u2014",
           u"\u2015", u"\u2E17", u"\u2E1A", u"\u2E3A", u"\u2E3B",
           u"\u2E40", u"\u301C", u"\u3030", u"\u30A0", u"\uFE31",
           u"\uFE32", u"\uFE58", u"\uFE63", u"\uFF0D")
regexPattern = '|'.join(map(re.escape, hyphens))
nohyphens = re.compile(regexPattern)


class JobCategorizer(object):

    # set up the logger
    LOGGING_LEVEL = logging.WARNING
    logger = setup_custom_logger('JobCategorizer', LOGGING_LEVEL)

    # takes initialized instances
    def __init__(self, location_classifier, tree_parser, sqlite_reader):
        self.lc = location_classifier
        self.tp = tree_parser
        self.sqlite_reader = sqlite_reader
        self.categorized_nuts = {}  # main data structure

    def __split_dashes(self, string):
        list_nohyphens = nohyphens.split(string)
        # on return remove elements that consist of blank spaces only
        return filter(lambda item: len(nowhitespaces.sub("", item)),
                      list_nohyphens)

    def populate_tree(self):
        if not (self.lc.ekatte_dict and lc.ekatte_locations and
                tp.initialized):
            JobCategorizer.logger.error(("Something went wrong with the initialization. "
                          "Investigate"))
            return False

        sqlite_reader.open_db()
        # TODO: the column ids are hard-coded. Not nice. Get them from the
        # db schema
        db_url = 1
        db_location = 5
        db_location2 = 6
        all_jobs = self.sqlite_reader.runQuery("SELECT * from bgjobs limit 10")
        if type(all_jobs) == sqlite.ProgrammingError:
            JobCategorizer.logger.error(all_jobs.message)
            return False

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
            if len(job_categories) == 0:  # []
                JobCategorizer.logger.warning("Categories not parsed for job %s", row[db_url])
                continue
            #
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
        # TODO: serialize self.tp for faster access
        sqlite_reader.close_db()
        return True

    def get_categories(self, job_url):
        categories_list = []
        # query the tbl_category table
        query = "SELECT * FROM tbl_category WHERE job_url=\'" + job_url + "\'"
        all_categories = self.sqlite_reader.runQuery(query)

        for row in all_categories:
            cat = row[2]
            # split on a hyphen, which is used by jobs.bg to denote
            # subcategories, e.g. ИТ - Административни дейности и продажби
            cat_splitted = self.__split_dashes(cat)
            if len(cat_splitted) == 2:
                leaf = sanitize_id(cat_splitted[1].encode("utf-8"))
                parent = sanitize_id(cat_splitted[0].encode("utf-8"))
                identifier = parent + leaf
                most_similar = self.tp.get_most_similar(identifier)
                # try to find leaf in the category tree
                # if identifier in self.tp:
                if most_similar:
                    # good, category is resolved
                    categories_list.append(most_similar)
                    JobCategorizer.logger.debug("Category %s fully resolved for job %s",
                                 cat, job_url)
                else:
                    # leaf not found, likely misspecified category config.
                    JobCategorizer.logger.warning(("Mismatch in hierarchical structures "
                                    "between database and category file "
                                    "for category %s, job %s"), cat, job_url)
            elif len(cat_splitted) == 1:
                # category is not hyphenated, find it in the tree as it is
                leaf = sanitize_id(cat.encode("utf-8"))
                most_similar = self.tp.get_most_similar(leaf)
                if most_similar in self.tp:
                    # found it, we are done
                    categories_list.append(most_similar)
                    JobCategorizer.logger.debug(("Category %s fully resolved for "
                                  "job %s"), cat, job_url)
                else:
                    # not found, likely misspecified category config.
                    JobCategorizer.logger.warning(("Mismatch in hierarchical structures "
                                    "between database and category file "
                                    "for category %s, job %s"), cat, job_url)
            else:
                # should never happen
                JobCategorizer.logger.error("Impossible category %s. Investigate.", cat)
        # end for row in all_categories
        return categories_list

    # stub
    def output_writer(self, **kwargs):

        nuts3 = kwargs.get("nuts3", None)
        nuts4 = kwargs.get("nuts4", None)
        output_dir = kwargs.pop("outdir", "")

        if not nuts3 and nuts4:
            JobCategorizer.logger.error("Cannot request nuts4 without specifying nuts3 ")
            return

        filename = "all.csv"
        if nuts3:
            filename = nuts3 + ".csv" if not nuts4 else nuts3 + "." + nuts4 +".csv"
        filename = os.path.join(output_dir, filename)

        try:
            out = open(filename, 'w')
        except IOError as e:
            JobCategorizer.logger.error("%s", e)
            return

        for leaf in self.tp.get_leaves():
            branch = self.tp.get_branch(leaf, **kwargs)
            if branch:
                out.write(branch + "\n")
        #
        out.close()


if __name__ == "__main__":

    sqlite_reader = SqliteReader("../crawled/data-2016-2-6_21-50-52.sqlite")
    lc = LocationClassifier("Ek_atte.csv", "provinces.csv")
    tp = TreeParser("jobCategories.txt")
    tp.build_tree()

    jc = JobCategorizer(lc, tp, sqlite_reader)
    success = jc.populate_tree()
    # jc.tp.show("root")
    if success:
        jc.output_writer(**{"outdir": "json_data"})
        all_nuts = jc.lc.get_all_nuts()
        nuts3_codes = all_nuts.keys()
        for nuts3 in nuts3_codes:
            jc.output_writer(**{"nuts3": nuts3, "outdir": "json_data"})
            for nuts4 in all_nuts[nuts3]:
                jc.output_writer(**{"nuts3": nuts3, "nuts4": nuts4,
                                    "outdir": "json_data"})
