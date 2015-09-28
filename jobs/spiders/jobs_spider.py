# -*- coding: utf-8 -*-
"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""
import scrapy
import re
from jobs.items import JobItem

class JobsSpider(scrapy.Spider):
    name = "jobsSpider"
    allowed_domains = ["jobs.bg"]
    start_urls = [
        "http://www.jobs.bg/front_job_search.php?first_search=1&all_cities=0&all_categories=0&all_type=0&all_position_level=1&all_company_type=1&keyword="
    ]

    def get_location_hint(self, response):        
        '''Get a hint about location of the job from the search page.        
           The search page *typically* displays the date and location of the job 
           in 2 <span> elements, each on a separate row, e.g.:           
           днес
           Конструктор
           Русе           
           
           The title is in-between the 2 span elements.          
        '''    
        job_locations = response.xpath('//*[@class=\'joblink\']//..//span[2]//text()').extract()
        if len(job_locations) == 0:
            '''
                if the date <span> element is not there for some reason
                the location would the the first <span>
            '''
            job_locations = response.xpath('//*[@class=\'joblink\']//..//span[1]//text()').extract()
        return job_locations    
            

    def parse(self, response):                
        joblocations = self.get_location_hint(response)
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()
        ignoreHints=False
        if len(joblocations) != len(joblinks):
            self.logger.warning('Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints',response.url)
            ignoreHints=True
            
        for joblink in range(len(joblinks)):
            url = response.urljoin(joblinks[joblink])
            locationHint = "".encode('utf-8')
            if not ignoreHints:
                locationHint = joblocations[joblink].encode('utf-8')
            request = scrapy.Request(url, callback = self.parse_job)
            request.meta['location_hint'] = locationHint            
            yield request
        ###
                
        #extract the total number of results
        #pagination_text looks like: 1-15 от 28348        
        pagination_text = response.xpath('//*[@id=\'search_results\']/table/tr[2]/td[1]/text()').extract()[0]
        pagination_splitted = re.split(r'\D+',pagination_text)
        if len(pagination_splitted) != 3:
            self.logger.error('Cannot get pagination info %s from %s',pagination_text,response.url)
            #TODO - raise an error
        pagination_splitted = [int(num) for num in pagination_splitted]
        start_page = pagination_splitted[0]
        step_pagination = pagination_splitted[1]
        total_entries = pagination_splitted[2]
        
        #create the URLs to follow by using the information in pagination_splitted
        url_left_part="http://www.jobs.bg/front_job_search.php?frompage="
        url_right_part="&all_cities=0&all_categories=0&all_type=0&all_position_level=1&all_company_type=1&keyword=#paging"
        
        #for page in range(step_pagination,total_entries,step_pagination):
        #    url = url_left_part + str(page) + url_right_part`            
        #    yield scrapy.Request(url, callback=self.parse_search_page)
        
    def parse_search_page(self, response):
        #parse the current result page
        joblocations = self.get_location_hint(response)
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()
        ignoreHints=False
        if len(joblocations) != len(joblinks):
            self.logger.warning('Mismatch in the lenghts of job results and location hints, %s. \n Ignoring location hints',response.url)
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
            self.logger.info('Job %s - title does not exist',response.url)
        #
        try:
            ref_no = response.xpath('//*[@class=\'jobTitleViewBold\' and contains(translate(text(),\'REFNO\',\'refno\'), \'ref.no\')]//..//td[2]//text()')[0].extract()
            item['ref_no'] = ref_no
        except IndexError as e:
            self.logger.info('Job %s - ref_no does not exist',response.url)        #
        try:
            description = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Описание\')]//..//td[2]//text()').extract()
            description = ''.join(description).strip().encode('utf-8')
            item['description_requirements'] = description
        except IndexError as e:
            self.logger.info('Job %s - description and requirements do not exist',response.url)
        #
        location_hint = response.meta['location_hint'].decode('utf-8')
        try:
            location = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Месторабота\')]//..//td[2]//text()')[0].extract()
            location = location.split('/')[0] # e.g. София / България            
            location = re.sub(r'\s+','',location)                        
            if  location_hint != location:
                self.logger.info('Location hint (%s) and location (%s) do not match for job %s. Preferring location',location_hint,location,response.url)
            item['location'] = location.encode('utf-8')
        except IndexError as e:
            if location_hint != '':
                self.logger.info('Job %s - location does not exist, but using location hint %s',response.url,location_hint)
                item['location'] = location_hint.encode('utf-8')
            else:
                self.logger.info('Job %s - location does not exist',response.url)
        #
        advertiser = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Организация\')]//..//td[2]//tr[1]//text()').extract()
        advertiser = "".join(advertiser).strip()
        item['advertiser'] = advertiser.encode('utf-8')
        #
        #date = response.xpath(u'//*[@class=\'jobTitle\']/../../../../../tr/td[3]/table/tr[2]/td[2]/table/tr[1]//text()').extract()        
        date = response.xpath(u'//*[contains(text(),\'Дата\')]//..//..//text()').extract()        
        if len(date) == 0:
            self.logger.info('Job %s - date does not exist',response.url)
        else:
            date = ''.join(date)
            date = date.replace('\n','').replace('\t','')
            item['date'] = date
        #
        category = response.xpath(u'//*[contains(text(),\'Категория\')]//..//..//text()').extract()        
        if len(category) == 0:
            self.logger.info('Job %s - category does not exist',response.url)
        else:
            category = ''.join(category)
            category = category.replace('\t','')
            item['category'] = category.encode('utf-8')
        #
        Type = response.xpath(u'//*[contains(text(),\'Вид работа\')]//..//..//text()').extract()        
        if len(Type) == 0:
            self.logger.info('Job %s - Type does not exist',response.url)
        else:
            Type = ''.join(Type)
            Type = Type.replace('\t','')
            item['type'] = Type.encode('utf-8')
        #
        level = response.xpath(u'//*[contains(text(),\'Ниво\')]//..//..//text()').extract()        
        if len(level) == 0:
            self.logger.info('Job %s - level does not exist',response.url)
        else:
            level = ''.join(level)
            level = level.replace('\t','')
            item['level'] = level.encode('utf-8')
        #
        work_grade = response.xpath(u'//*[contains(text(),\'Вид заетост\')]//..//..//text()').extract()        
        if len(work_grade) == 0:
            self.logger.info('Job %s - work_grade does not exist',response.url)
        else:
            work_grade = ''.join(work_grade)
            work_grade = work_grade.replace('\t','')
            item['work_grade'] = work_grade.encode('utf-8')

        yield item
                
        
