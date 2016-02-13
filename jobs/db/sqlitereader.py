# -*- coding: utf-8 -*-

"""
Created on February 10, 2016

@author: Pavlin Mavrodiev
"""

import os
import errno
import sqlite3 as sqlite


class SqliteReader(object):

    def __init__(self, sqlite_db=None):
        self.sqlite_db = sqlite_db
        self.write_counter = 0
        self.write_chunks = 1000

    def open_db(self):
        if not os.path.isfile(self.sqlite_db):
            raise IOError((errno.ENOENT, 'File not found %s' % self.sqlite_db))
        self.connection = sqlite.connect(self.sqlite_db, isolation_level=None)
        self.cursor = self.connection.cursor()

    def close_db(self):
        self.connection.close()

    def runQuery(self, sql_query):
        try:
            self.cursor.execute(sql_query)
            return self.cursor.fetchall()
        except sqlite.ProgrammingError as e:
            raise e

    def extract_category(self):
        self.open_db()
        #
        for job in self.all_rows:
            db_id = job[self.db_id_index]
            job_id = job[self.job_id_index]
            category = job[self.category_column_index]
            tokenized = self.tokenize_entry(category, job_id, db_id)
            # write the different categories into a new table
            for cat in tokenized:
                insertSQL = 'INSERT INTO tbl_category (job_url, category) VALUES (?, ?)'
                self.insert_db(insertSQL, job_id, cat)
        # need to end the last transaction
        if self.write_counter % self.write_chunks:
            self.cursor.execute('END TRANSACTION')
            self.connection.commit()
        self.connection.close()
