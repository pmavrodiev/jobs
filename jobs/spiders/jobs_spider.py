# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""

import scrapy
import re
from jobs.items import JobItem
import logging
from scrapy import spiders, signals
from scrapy.xlib.pydispatch import dispatcher

class JobsSpider(spiders.Spider):
    name = "jobsSpider"
    allowed_domains = ["jobs.bg"]
    start_urls = [
        "http://www.jobs.bg/front_job_search.php?first_search=1&all_cities=0&all_categories=0&all_type=0&all_position_level=1&all_company_type=1&keyword="
    ]

    def __init__(self, Name=name, **kwargs):        
        super(JobsSpider, self).__init__(Name, **kwargs)
        #register a signal listener for a spider close event in order
        #to send an email upon finish
        dispatcher.connect(self.quit, signals.spider_closed)
        '''        
        rootLogger is just a convenience attribute to shorthen the code.
        self.logger is a property object, which returns an instance of 
        logging.LoggerAdapter. To get the logger belonging to the adaptor
        one needs to call self.logger.logger, which is just confusing
        Better do self.rootLogger
        '''        
        self.rootLogger = self.logger.logger
        self.rootLogger.setLevel(logging.NOTSET)

        logFormatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        #TODO read logdir from global settings     
        logdir = 'jobs/logs/'
        # file handlers
        infoHandler = logging.FileHandler(logdir + Name + '_info.log')
        infoHandler.setLevel(logging.INFO)
        infoHandler.setFormatter(logFormatter)
        #
        errorHandler = logging.FileHandler(logdir + Name + '_error.log')
        errorHandler.setLevel(logging.ERROR)
        errorHandler.setFormatter(logFormatter)
        #
        debugHandler = logging.FileHandler(logdir + Name + '_debug.log')
        debugHandler.setLevel(logging.DEBUG)
        debugHandler.setFormatter(logFormatter)
        #
        self.rootLogger.addHandler(infoHandler)
        self.rootLogger.addHandler(errorHandler)
        self.rootLogger.addHandler(debugHandler)
        
        # console handler
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.ERROR)
        consoleHandler.setFormatter(logFormatter)
        self.rootLogger.addHandler(consoleHandler)              
       
       
        
    def get_location_hint(self, response):        
        '''
        Gets a hint about location of the job from the search page.        
        The search page *typically* displays the date and location of the job 
        in 2 <span> elements, each on a separate row, e.g.:           
            днес
            Конструктор
            Русе           
           
        The title is in-between the 2 span elements.

        '''    
        job_locations = response.xpath('//*[@class=\'joblink\']//..//div/span/text()').extract()
        #remove new lines and tabs        
        job_locations = [jl.strip() for jl in job_locations]       
        
        return job_locations    
            

    def parse(self, response):
        '''
        Parsing is done in 2 steps:
            1. The start page (start_url) is parsed and all job postings there
               are processed by calls to parse_job
            2. Pagination info read from the start page is used to advance

        '''
        joblocations = self.get_location_hint(response)
        #get the first bunch of job postings from the start_url
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()
        ignoreHints=False
        if len(joblocations) != len(joblinks):
            #log.warnings.warn(''Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints',response.url')
            self.rootLogger.warning('Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints',response.url)
            ignoreHints=True
        #
        #process the first bunch of job postings from the start_url
        for idx_joblink in range(len(joblinks)):
            url = response.urljoin(joblinks[idx_joblink])
            locationHint = "".encode('utf-8')
            if not ignoreHints:
                locationHint = joblocations[idx_joblink].encode('utf-8')
            request = scrapy.Request(url, callback = self.parse_job)
            #parse the jobs
            request.meta['location_hint'] = locationHint            
            yield request
        ###
                
        #extract the total number of results
        #pagination_text looks like: 1-15 от 28348
        pagination_text = response.xpath('//div[@id=\'search_results_div\']/table/tr/td/table/tr[3]/td[1]/text()').extract()[0]
        pagination_splitted = re.split(r'\D+',pagination_text)
        if len(pagination_splitted) != 3:
            #log.err('Cannot get pagination info %s from %s',pagination_text,response.url)
            self.rootLogger.error('Cannot get pagination info %s from %s',pagination_text,response.url)
            #TODO - raise an error
        pagination_splitted = [int(num) for num in pagination_splitted]
        start_page = pagination_splitted[0]
        step_pagination = pagination_splitted[1]
        total_entries = pagination_splitted[2]
        #log.msg('Number of jobs - start (%s), end (%s), pagination (%s)' % (start_page, total_entries, step_pagination), log.INFO)
        self.rootLogger.info('Number of jobs - start (%s), end (%s), pagination (%s)',start_page, total_entries, step_pagination)
        #create the URLs to follow by using the information in pagination_splitted
        url_left_part="http://www.jobs.bg/front_job_search.php?frompage="
        url_right_part="&all_cities=0&all_categories=0&all_type=0&all_position_level=1&all_company_type=1&keyword=#paging"
        #loop through all pages
        
        for page in range(step_pagination,total_entries,step_pagination):
            url = url_left_part + str(page) + url_right_part          
            yield scrapy.Request(url, callback=self.parse_search_page)
        
        
    def parse_search_page(self, response):
        #parse the current result page
        joblocations = self.get_location_hint(response)
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()
        ignoreHints=False
        if len(joblocations) != len(joblinks):
            #log.warnings.warn('Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints' % response.url)
            self.rootLogger.warning('Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints',response.url)
            ignoreHints=True            
        for joblink in range(len(joblinks)):
            url = response.urljoin(joblinks[joblink])
            locationHint = "".encode('utf-8')
            if not ignoreHints:
                locationHint = joblocations[joblink].encode('utf-8')
            request = scrapy.Request(url, callback = self.parse_job)
            request.meta['location_hint'] = locationHint            
            yield request    
        #joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()             
        #for joblink in joblinks:
        #    url = response.urljoin(joblink)
        #    yield scrapy.Request(url, callback = self.parse_job)
        ###
 
    def parse_job(self, response):
        item = JobItem()
        item['url'] = response.url
        #
        try:
            title = response.xpath('//*[@class=\'jobTitle\']/text()')[0].extract()
            item['title'] = title.encode('utf-8')
        except IndexError as e: #title does not exist
            #log.msg('Job %s - title not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - title not specified',response.url)
        #
        try:
            ref_no = response.xpath('//*[@class=\'jobTitleViewBold\' and contains(translate(text(),\'REFNO\',\'refno\'), \'ref.no\')]//..//td[2]//text()')[0].extract()
            item['ref_no'] = ref_no
        except IndexError as e:
            #log.msg('Job %s - ref_no not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - ref_no not specified',response.url)        #
        try:
            description = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Описание\')]//..//td[2]//text()').extract()
            description = ''.join(description).strip().encode('utf-8')
            item['description_requirements'] = description
        except IndexError as e:
            #log.msg('Job %s - description and requirements do not exist' % response.url, log.INFO)
            self.rootLogger.info('Job %s - description and requirements do not exist',response.url)
        #
        location_hint = response.meta['location_hint'].decode('utf-8')
        try:
            location = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Месторабота\')]//..//td[2]//text()')[0].extract()
            location = location.split('/')[0] # e.g. София / България            
            location = re.sub(r'\s+','',location)                        
            if  location_hint != location:
                self.rootLogger.info('Location hint (%s) and location (%s) do not match for job %s. Preferring location',location_hint,location,response.url)
                #log.msg('Location hint (%s) and location (%s) do not match for job %s. Preferring location' % (location_hint,location,response.url), log.INFO)
            item['location'] = location.encode('utf-8')
        except IndexError as e:
            if location_hint != '':
                self.rootLogger.info('Job %s - location not specified, but using location hint %s',response.url,location_hint)
                #log.msg('Job %s - location not specified, but using location hint %s' % (response.url,location_hint), log.INFO)                
                item['location'] = location_hint.encode('utf-8')
            else:
                #log.msg('Job %s - location not specified' % response.url, log.INFO)
                self.rootLogger.info('Job %s - location not specified',response.url)
        #
        try:
            salary = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Заплата\')]//..//td[2]//text()')[0].extract()
            item['salary'] = salary.encode('utf-8')
        except:
            #log.msg('Job %s - salary not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - salary not specified',response.url)            
        #
        advertiser = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Организация\')]//..//td[2]//tr[1]//text()').extract()
        advertiser = "".join(advertiser).strip()
        item['advertiser'] = advertiser.encode('utf-8')
        #
        #date = response.xpath(u'//*[@class=\'jobTitle\']/../../../../../tr/td[3]/table/tr[2]/td[2]/table/tr[1]//text()').extract()        
        date = response.xpath(u'//*[text()=\'Дата:\']//..//..//text()').extract()        
        if len(date) == 0:
            #log.msg('Job %s - date not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - date not specified',response.url)
        else:
            date = ''.join(date)
            date = date.replace('\n','').replace('\t','')
            item['date'] = date
        #
        category = response.xpath(u'//*[text()=\'Категория:\']//..//..//text()').extract()        
        if len(category) == 0:
            #log.msg('Job %s - category not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - category not specified',response.url)
        else:
            category = ''.join(category)
            category = category.replace('\t','')
            item['category'] = category.encode('utf-8')
        #
        Type = response.xpath(u'//*[text()=\'Вид работа:\']//..//..//text()').extract()        
        if len(Type) == 0:
            #log.msg('Job %s - Type not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - Type not specified',response.url)
        else:
            Type = ''.join(Type)
            Type = Type.replace('\t','')
            item['Type'] = Type.encode('utf-8')
        #
        level = response.xpath(u'//*[text()=\'Ниво:\']//..//..//text()').extract()        
        if len(level) == 0:
            #log.msg('Job %s - level not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - level not specified',response.url)
        else:
            level = ''.join(level)
            level = level.replace('\t','')
            item['level'] = level.encode('utf-8')
        #
        work_grade = response.xpath(u'//*[text()=\'Вид заетост:\']//..//..//text()').extract()        
        if len(work_grade) == 0:
            #log.msg('Job %s - work_grade not specified' % response.url, log.INFO)
            self.rootLogger.info('Job %s - work_grade not specified',response.url)
        else:
            work_grade = ''.join(work_grade)
            work_grade = work_grade.replace('\t','')
            item['work_grade'] = work_grade.encode('utf-8')
        #           
        yield item
                
    def quit(self, spider):
        import yagmail
        
        spider.rootLogger.info('Spider %s finished, sending email', spider.name)
        
        yag = yagmail.SMTP('pmavrodiev@gmail.com', 'password')
