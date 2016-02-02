# -*- coding: utf-8 -*-


import sqlite3 as sqlite



class SqliteWriterPipeline(object):
    def __init__(self,sqlite_db):
       self.sqlite_db = sqlite_db
       self.write_counter = 0
       self.write_chunks = 100 #number of rows to write in one transaction
    
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
        tokenized_type=self.tokenize_entry(item['type'],item['url'],'Вид работа'.decode('utf-8'),spider)
        tokenized_level=self.tokenize_entry(item['level'],item['url'],'Ниво'.decode('utf-8'),spider)
        tokenized_work_grade=self.tokenize_entry(item['work_grade'],item['url'],'Вид заетост'.decode('utf-8'),spider)
        
        
        insert_sql = 'insert into bgjobs (url,title,ref_no,description_requirements,' + \
                        'location,advertiser,date,category,type,level,work_grade,salary) ' + \
                        'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                        
        #if not self.write_counter % self.write_chunks: #new transaction
        #    self.cursor.execute('BEGIN TRANSACTION')          
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
        #if not self.write_counter % self.write_chunks:
        #    spider.logger.debug('Writing chunk %s',self.write_counter)
        #    self.cursor.execute('END TRANSACTION')
        #    self.connection.commit()            
        #log.msg("Item stored : " % item, level=log.DEBUG)
        return item

    def tokenize_entry(self,text,job_id,token,spider):
        ''' example text
        Категория:

        Контакт центрове (Call Centers),
        Търговия, Продажби - Продавачи и помощен персонал
        
        would return a list ['Категория', 'Контакт центрове (Call Centers)','Търговия, Продажби - Продавачи и помощен персонал']
        '''
        characters_to_strip=',/: '
        tokenized = filter(None, [x.strip(characters_to_strip).rstrip(characters_to_strip) for x in text.splitlines()])
        try:        
            if tokenized[0] != token:
                spider.logger.error("Warning for job %s: Cannot tokenize token %s/%s" % (job_id,token,tokenized[0]))
                return []
        except IndexError as e:
            #something must be pretty wrong to come here
            spider.logger.error('Cannot tokenize token %s for job %s. Probably failed XPATH for that token.',(token,job_id))
            return []
        
        return tokenized[1:]        
