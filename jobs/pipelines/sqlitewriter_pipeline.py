# -*- coding: utf-8 -*-


import sqlite3 as sqlite



class SqliteWriterPipeline(object):
    def __init__(self,sqlite_db):
       self.sqlite_db = sqlite_db
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(sqlite_db = crawler.settings.get('SQLITEDB'))        
        
    def open_spider(self, spider):               
        self.connection = sqlite.connect(self.sqlite_db)
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS bgjobs ' + \
                    '(id INTEGER PRIMARY KEY, ' + \
                    'url TEXT, ' + \
                    'title TEXT,' + \
                    'ref_no TEXT,' + \
                    'description_requirements BLOB, ' + \
                    'location TEXT, '+ \
                    'advertiser TEXT, '+ \
                    'date TEXT, ' + \
                    'category TEXT, '+  \
                    'type TEXT,' + \
                    'level TEXT,' + \
                    'work_grade TEXT,'+  \
                    'salary TEXT' +  \
                    ')')

    def close_spider(self, spider):
        self.connection.commit()
        self.connection.close()
        
    # Take the item and put it in database - do not allow duplicates
    def process_item(self, item, spider):
        insert_sql = 'insert into bgjobs (url,title,ref_no,description_requirements,' + \
                        'location,advertiser,date,category,type,level,work_grade,salary) ' + \
                        'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'          
        self.cursor.execute(insert_sql,(item['url'], item['title'],
                                        item['ref_no'],
                                        sqlite.Binary(item['description_requirements']),
                                        item['location'],
                                        item['advertiser'],
                                        item['date'],
                                        item['category'],
                                        item['type'],
                                        item['level'],
                                        item['work_grade'],
                                        item['salary']))
        #log.msg("Item stored : " % item, level=log.DEBUG)
        return item

