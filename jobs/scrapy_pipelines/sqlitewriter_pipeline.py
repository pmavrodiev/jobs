# -*- coding: utf-8 -*-

"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""


import sqlite3 as sqlite

import sys
import os
import logging

from simple_logging.custom_logging import setup_custom_logger

class SqliteWriterPipeline(object):
    # set up the logger
    LOGGING_LEVEL = logging.INFO
    logger = setup_custom_logger('SqliteWriterPipelin', LOGGING_LEVEL,
                                 flog=os.path.join(sys.path[0],
                                                   "logs/jobs_spider.log"))

    def __init__(self):
       self.write_counter = 0
       self.write_chunks = 100 #number of rows to write in one transaction



    def open_spider(self, spider):
        self.connection = sqlite.connect(spider.sqlite_db)
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS bgjobs ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'url TEXT, ' + \
                    'title TEXT,' + \
                    'ref_no TEXT,' + \
                    'description_requirements BLOB, ' + \
                    'location TEXT, '+ \
                    'location2 TEXT, '+ \
                    'advertiser TEXT, '+ \
                    'date TEXT, ' + \
                    'category TEXT, '+  \
                    'type TEXT,' + \
                    'level TEXT,' + \
                    'work_grade TEXT,'+  \
                    'salary TEXT' +  \
                    ')')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS tbl_category ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'job_url TEXT, ' + \
                    'category TEXT' + \
                    ')')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS tbl_type ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'job_url TEXT, ' + \
                    'type TEXT' + \
                    ')')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS tbl_level ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'job_url TEXT, ' + \
                    'level TEXT' + \
                    ')')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS tbl_work_grade ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'job_url TEXT, ' + \
                    'work_grade TEXT' + \
                    ')')
        self.connection.commit()

    def close_spider(self, spider):
        #if self.write_counter % self.write_chunks: #need to end the last transaction
        #    spider.logger.debug('Writing chunk %s',self.write_counter)
        #    self.cursor.execute('END TRANSACTION')
        #    self.connection.commit()
        self.connection.close()

    # Take the item and put it in database - do not allow duplicates
    def process_item(self, item, spider):
        tokenized_category=self.tokenize_entry(item['category'],item['url'],'Категория'.decode('utf-8'),spider)
        tokenized_type=self.tokenize_entry(item['Type'],item['url'],'Вид работа'.decode('utf-8'),spider)
        tokenized_level=self.tokenize_entry(item['level'],item['url'],'Ниво'.decode('utf-8'),spider)
        tokenized_work_grade=self.tokenize_entry(item['work_grade'],item['url'],'Вид заетост'.decode('utf-8'),spider)


        insert_sql = 'insert into bgjobs (url,title,ref_no,description_requirements,' + \
                        'location,location2,advertiser,date,category,type,level,work_grade,salary) ' + \
                        'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'

        #if not self.write_counter % self.write_chunks: #new transaction
        #    self.cursor.execute('BEGIN TRANSACTION')
        self.cursor.execute(insert_sql,(item['url'], item['title'],
                                        item['ref_no'],
                                        sqlite.Binary(item['description_requirements']),
                                        item['location'],
                                        item['location2'],
                                        item['advertiser'],
                                        item['date'],
                                        item['category'],
                                        item['Type'],
                                        item['level'],
                                        item['work_grade'],
                                        item['salary']))
        for cat in tokenized_category:
            insertSQL = 'INSERT INTO tbl_category (job_url, category) VALUES (?, ?)'
            self.cursor.execute(insertSQL,(item['url'],cat))
        #
        for Type in tokenized_type:
            insertSQL = 'INSERT INTO tbl_type (job_url, type) VALUES (?, ?)'
            self.cursor.execute(insertSQL,(item['url'],Type))
        #
        for level in tokenized_level:
            insertSQL = 'INSERT INTO tbl_level (job_url, level) VALUES (?, ?)'
            self.cursor.execute(insertSQL,(item['url'],level))
        #
        for work_grade in tokenized_work_grade:
            insertSQL = 'INSERT INTO tbl_work_grade (job_url, work_grade) VALUES (?, ?)'
            self.cursor.execute(insertSQL,(item['url'],work_grade))
        #
        self.write_counter = self.write_counter + 1
        self.connection.commit()
        SqliteWriterPipeline.logger.info('Processed %s',item['url'])
        #if not self.write_counter % self.write_chunks:
        #    spider.logger.debug('Writing chunk %s',self.write_counter)
        #    self.cursor.execute('END TRANSACTION')
        #    self.connection.commit()
        #log.msg("Item stored : " % item, level=log.DEBUG)
        return item

    def tokenize_entry(self,text,job_id,token,spider):
        '''
        Upon parsing a job posting, the entries about the Category, Description,
        Type of work, Level and Working type contain a key word and
        a bullet-type list
        This function extracts the category name and the bullet points and
        stores them in a separate table for easier processing later

        Example
        -------
        Категория:

        Контакт центрове (Call Centers),
        Търговия, Продажби - Продавачи и помощен персонал

        Returns
        -------
        A list ['Контакт центрове (Call Centers)','Търговия, Продажби - Продавачи и помощен персонал']
        '''
        characters_to_strip=',/: '
        tokenized = filter(None, [x.strip(characters_to_strip).rstrip(characters_to_strip) for x in text.splitlines()])
        try:
            if tokenized[0] != token:
                SqliteWriterPipeline.logger.warning("Warning for job %s: Cannot tokenize token %s/%s", job_id,token,tokenized[0])
                return []
        except IndexError:
            #the token has been missing from the job posting html
            SqliteWriterPipeline.logger.error('Cannot tokenize token %s for job %s. Probably failed XPATH for that token.', token,job_id)
            return []

        return tokenized[1:]
