#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 16:43:50 2015

@author: pmavrodiev
"""

import sqlite3 as sqlite
import os.path
import errno
import sys



class SqliteReader(object):
    def __init__(self,sqlite_db):
       if os.path.isfile(sqlite_db):
           self.sqlite_db = sqlite_db
           self.category_column_index=8
           self.job_id_index = 1
           self.db_id_index = 0
           self.write_counter=0
           self.write_chunks=1000
       else:
           raise IOError((errno.ENOENT,'File not found %s'%sqlite_db))

    
    def open_db(self):
        self.connection = sqlite.connect(self.sqlite_db,isolation_level=None)
        self.cursor = self.connection.cursor()
    
    def read_db(self,tablename):
        self.open_db()
        self.cursor.execute('SELECT * FROM {}'.format(tablename))   
        self.all_rows = self.cursor.fetchall()
        self.connection.close()

    def insert_db(self,insert_what,*args):
        if not self.write_counter % self.write_chunks: #new transaction
            self.cursor.execute('BEGIN TRANSACTION')
       
        self.cursor.execute(insert_what,tuple(args))
        self.write_counter = self.write_counter + 1
        if not self.write_counter % self.write_chunks:
            self.cursor.execute('END TRANSACTION')
            self.connection.commit()
            
            
    
    def tokenize_entry(self,text,job_id,db_id):
        ''' example text
        Категория:

        Контакт центрове (Call Centers),
        Търговия, Продажби - Продавачи и помощен персонал
        
        would return a list ['Категория', 'Контакт центрове (Call Centers)','Търговия, Продажби - Продавачи и помощен персонал']
        '''
        characters_to_strip=',/: '
        tokenized = filter(None, [x.strip(characters_to_strip).rstrip(characters_to_strip) for x in text.splitlines()])
        try:        
            if tokenized[0].encode('utf-8') != 'Категория':
                print("Warning for job %s: Cannot tokenize category" % db_id)
                return []
        except IndexError as e:
            #something must be pretty wrong to come here
            print(job_id)
            return []
        
        return tokenized[1:]        
        
    def extract_category(self):
        self.open_db()
        #
        for job in self.all_rows:
            db_id = job[self.db_id_index]
            job_id = job[self.job_id_index]
            category = job[self.category_column_index]
            tokenized = self.tokenize_entry(category,job_id,db_id)
            #write the different categories into a new table
            for cat in tokenized:
                insertSQL = 'INSERT INTO tbl_category (job_id, category) VALUES (?, ?)'
                self.insert_db(insertSQL,job_id,cat)
        #need to end the last transaction
        if self.write_counter % self.write_chunks: 
            self.cursor.execute('END TRANSACTION')
            self.connection.commit()
        self.connection.close() 
    
        
if __name__ == '__main__':
    db_reader = SqliteReader('/home/pmavrodiev/Projects/jobs/jobs/jobs.sqlite')
    db_reader.read_db('bgjobs')
    db_reader.extract_category()
    