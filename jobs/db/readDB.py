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
import csv
from itertools import compress
import logging

#set up the logger
LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL)
logger = logging.getLogger(__name__)
# 

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
    
    def close_db(self):
        self.connection.close()        
    
    def runQuery(self,sql_query):
        self.cursor.execute(sql_query)
        return self.cursor.fetchall()
            
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
                insertSQL = 'INSERT INTO tbl_category (job_url, category) VALUES (?, ?)'
                self.insert_db(insertSQL,job_id,cat)
        #need to end the last transaction
        if self.write_counter % self.write_chunks: 
            self.cursor.execute('END TRANSACTION')
            self.connection.commit()
        self.connection.close() 


def readEKATTE(filename):
    ekatte_file = open(filename,'r')
    ekatte_csv = csv.reader(ekatte_file,delimiter=',')    
    ekatte_csv.next() #skip the header
    ekatte_dict={}
    #array of settlement names
    ekatte_locations=[]    
    for row in ekatte_csv:
        cleaned_loc = nowhitespaces.sub("",row[2].decode('utf-8')).lower()
        settlement_type = row[1].decode('utf-8')
        nuts3 = row[3]
        nuts4 = row[4]
        ekatte_locations.append(cleaned_loc)
        if ekatte_dict.has_key(cleaned_loc):
            if ekatte_dict[cleaned_loc].has_key(settlement_type):
                ekatte_dict[cleaned_loc][settlement_type].append((nuts3, nuts4))
            else:
                ekatte_dict[cleaned_loc][settlement_type] = [(nuts3, nuts4)]
        else:
            ekatte_dict[cleaned_loc] = dict({settlement_type: [(nuts3, nuts4)]})
        
    ekatte_file.close()
    return (ekatte_dict, ekatte_locations)

def readPROVINCE(filename):
    province_file = open(filename,'r')
    province_csv = csv.reader(province_file,delimiter=';')
    
    #key: province name
    #value: nuts3 code
    provinces_dict = {}
    #array of province names
    provinces = []
    for row in province_csv:
        for splitted in row[0].decode('utf-8').split('/'):
            cleaned_province = nowhitespaces.sub("",splitted.lower())           
            provinces.append(cleaned_province)
            provinces_dict[cleaned_province] = row[1]
            
    province_file.close()
    return (provinces_dict, provinces)

      
if __name__ == '__main__':
    '''
    The purpose of this module is to extract the nuts3 (province) and 
    nuts4 (municipality) codes of the location information given in the job posting.
    (NUTS = Nomenclature of Territorial Units for Statistics)
    These codes are then used to visualize a job posting on a geographical map.

    To this end, there are 3 available data sources:
    1. *Ek_atte.csv* - this is classification of settlements
       based on the EKATTE (Bulgarian region coding system).
       It contains detailed information on the nuts3 and nuts4:
       =======================================================    
       ekatte   t_v_m   name	    oblast    obstina    kmetstvo
       =======================================================
       00905,    с.,   Априлци,   KRZ,      KRZ14,    KRZ14-48
       -------------------------------------------------------

       In this example, the settlement Априлци has nuts3=KRZ and nuts4=KRZ14
       which puts it in province Кърджали and municipality Кирково.
       
       More on the mapping between nuts3/nuts4 and province/municipality
       names below.
       
    2. *provinces.csv* - this is a mapping between province names and their
        nuts3 codes. In the example above nuts3=KRZ corresponds to province
        Кърджали
        
    3. *municipalities.csv* - similarly this is a mapping between 
        municipalities names and their corresponding nuts4 codes.
        
    Given these 3 data sources a job posting is processed in the following
    way. 
    
    1. The job's 'location' and 'location2' fields are extracted from the sqlite db.
       Typically location is the name of a settlement, regardless of type, e.g. 
       city, village, resort, etc.. 
       
       'location2' is either the country or the province name in the format
       of e.g. Област Варна, i.e. the keyword Област must be discounted.
       
    2. Search for the location in the EKATTE data. 
    
    2.1. If found and unique, we easily extract the EKATTE
         nuts3 and nuts4 codes. We then use provinces.csv to extract
         the nuts3 code corresponding to 'location2'. If the EKATTE nuts3 code
         and the nuts3 code extracted from provinces.csv do not match, prefer
         the latter, i.e. give preference to the information in the sqlite db.
         Move to the next job posting.
    
    2.2. If found and *not* unique (i.e. the settlement's name is not unique),
         use provinces.csv to extract the nuts3 code corresponding to
         'location2'. Use this code to differentiate among the duplicate entries.
       
    2.3. If not found use 'location2' to extract the province.
    '''
    
    #compile a regex that removes all white spaces from a string,
    #including the annoying \xa0 (non-breaking space in Latin1 ISO 8859-1)
    import re
    nowhitespaces = re.compile(r"[\xa0\s+]")    
    
   
    #read the csv files
    """ 
    ekatte_dict
    ------------
    key: settlement name
    value: dict(key: settlement_type
                value: [(nuts3, nuts4)]
    
    some special cases:
        1. settlements with the same name in the same province
            с.,Крайна, SML, SML16
            с.,Крайна, SML, SML18
           
           will be stored as 
           ekatte_dict["Крайна"]["c."] = [(SML, SML16), (SML, SML18)]
           
        2. settlements with the same name and different settlement type
            с.,Габрово,BLG,BLG03,BLG03-00,3,8,7,1901,SW,935
            гр.,Габрово,GAB,GAB05,GAB05-00,1,1,5,1901,N,936
            с.,Габрово,KRZ,KRZ35,KRZ35-03,3,6,8,1901,S,937
            
           will be stored as 
           ekatte_dict["Габрово"]["гр."] = [(GAB, GAB05)]
           ekatte_dict["Габрово"]["с."] = [(BLG, BLG03), (KRZ, KRZ35)]
    """  
    ekatte_dict, ekatte_locations = readEKATTE('Ek_atte.csv')  
    provinces_dict, provinces = readPROVINCE('provinces.csv')  
    #
    
    #read the sqlite database    
    db_reader = SqliteReader('../crawled/data-2016-2-6_21-50-52.sqlite')
    db_reader.open_db()
    all_rows = db_reader.runQuery('SELECT * FROM bgjobs')        
    db_reader.close_db()
    
  
    #key: nuts3 code of a province
    #values: {nuts4 code: count of job postings in this nuts4 municipality}
    all_jobs = {key: dict() for key in provinces_dict.values()}
    
    for job in all_rows:
        '''
        For some reason the unicode for "Обзор" is messed up.
        The unicode should be u'\u041e\u0431\u0437\u043e\u0440',
        however in some sqlite entries it is u'O\u0431\u0437\u043e\u0440'.
        The problem is probably in the crawler and has to be investigated,
        but for now simply replacing the leading character with the proper
        unicode byte works.
        '''
        job_posting_url = job[1]
        location=job[5].replace('O',u'\u041e')
        location=nowhitespaces.sub("",location).lower()
        location2=job[6].lower()
        location2_bulgaria = True if location2 == 'българия'.decode('utf-8') else False        
        #Check if location2 is the name of a province from provinces.csv        
        location2_splitted=location2.split('област'.decode('utf-8'), 1)
        location2_resolved=False
        if len(location2_splitted) == 2:
            #e.g. location2 = 'област велико търново'
            #     location2_splitted = ['', 'вeliko търново']
            location2_cleaned = nowhitespaces.sub("",location2_splitted[1])
            if location2_cleaned in provinces:
                location2_resolved=True
        #note location2_resolved==True and location2_bulgaria==True is
        #not possible sice 'българия' is not defined as a province in
        #provinces.csv
                
        #try to find the settlement from 'location' in the EKATTE data
       
        match_list = [place == location for place in ekatte_locations]
        #get the indeces of the matches
        found = list(compress(xrange(len(match_list)),match_list))
        #only 1 match found - we have nuts3 and nuts4 codes from EKATTE
        if len(found) == 1:
            ekatte_loc = ekatte_locations[found[0]]
            settlement_type_dict = ekatte_dict[ekatte_loc]           
            #sanity check, len(found) = 1 = len(settlement_type_dict.keys())
            if len(settlement_type_dict.keys()) != 1:
                logger.error("[ERROR]: Inconsistent settlement types for settlement %s" , ekatte_loc)
                sys.exit(1)
            nuts3 = settlement_type_dict[settlement_type_dict.keys()[0]][0][0]
            nuts4 = settlement_type_dict[settlement_type_dict.keys()[0]][0][1]
            #check for mismatch between EKATTE nuts3 and 'location2'
            if location2_resolved:
                nuts3_sqlite = provinces_dict[location2_cleaned]
                if (nuts3_sqlite != nuts3):
                    logger.debug("location2 nuts3 %s does not match EKATTE nuts3 %s for job %s. Preferring EKATTE nuts3", nuts3_sqlite,nuts3,job_posting_url)
                    #nuts3=nuts3_sqlite
            #
            #add the job posting in its corresponding georgaphical 'bucket'
            if all_jobs[nuts3].has_key(nuts4):
                all_jobs[nuts3][nuts4] = all_jobs[nuts3][nuts4] + 1
            else:
                all_jobs[nuts3][nuts4] = 1
        #no settlement with name 'location' has been found in the EKATTE data
        #let's hope that location2 has been resolved
        elif len(found) == 0:
            if location2_resolved:
                nuts3 = provinces_dict[location2_cleaned]
                if all_jobs[nuts3].has_key("unnamed"):
                    all_jobs[nuts3]["unnamed"] = all_jobs[nuts3]["unnamed"] + 1
                else:
                    all_jobs[nuts3]["unnamed"] = 1               
            else:
                logger.info('Cannot find location %s and resolve location2 %s for job %s' , location, location2, job_posting_url)
        #multiple matches exist in the EKATTE data for the settlement in 'location'   
        elif len(found) > 1:
            #use location2 to differentiate            
            if location2_resolved:
                '''
                Тhe entry is e.g. с. Габрово област Благоевград
                The EKATTE data for Габрово is:
                    с.,Габрово,BLG,BLG03
                    гр.,Габрово,GAB,GAB05
                    с.,Габрово,KRZ,KRZ35
                '''
                nuts3 = provinces_dict[location2_cleaned]
                ekatte_loc = ekatte_locations[found[0]]
                settlement_type_dict = ekatte_dict[ekatte_loc]
                _found=False
                nuts4 = "unnamed"
                for types in settlement_type_dict:
                    nuts_codes = settlement_type_dict[types]
                    for nuts in nuts_codes:
                        if nuts[0] == nuts3:
                            nuts4 = nuts[1]
                            _found=True
                            break
                    if _found: break
                #add the job posting to the proper bucket
                if all_jobs[nuts3].has_key(nuts4):
                    all_jobs[nuts3][nuts4] = all_jobs[nuts3][nuts4] + 1
                else:
                    all_jobs[nuts3][nuts4] = 1
            #no location2, try to find the right settlement with name 'location'
            else:
                '''
                Тhe entry is e.g. Габрово/България
                
                The EKATTE data for Габрово is:
                    с.,Габрово,BLG,BLG03
                    гр.,Габрово,GAB,GAB05
                    с.,Габрово,KRZ,KRZ35
                    
                If location2 is simply 'българия' then always assume the job
                posting is in the city.
                '''
                if location2_bulgaria:
                    ekatte_loc = ekatte_locations[found[0]]
                    settlement_type_dict = ekatte_dict[ekatte_loc]
                    if settlement_type_dict.has_key("гр.".decode('utf-8')):
                        nuts_codes = settlement_type_dict["гр.".decode('utf-8')]
                        if len(nuts_codes) > 1:
                            logger.info("More than 1 cities exist for location %s. Without location2 cannot resolve location for job %s" , location, job_posting_url)
                        else:
                            nuts3 = nuts_codes[0][0]
                            nuts4 = nuts_codes[0][1]                               
                            if all_jobs[nuts3].has_key(nuts4):
                                all_jobs[nuts3][nuts4] = all_jobs[nuts3][nuts4] + 1
                            else:
                                all_jobs[nuts3][nuts4] = 1
                    #no cities exist with the name 'location'
                    else:
                        logger.info("Cannot resolve location %s to a main city in the absense of location2 for job %s" , location, job_posting_url)           
                #giving up on this job, nothing can be done        
                else:
                    logger.info("location2 (%s) and location (%s) cannot be resolved for job %s. Giving up." , location2, location, job_posting_url)
  
       
    #
    print(all_jobs['SLS'])
