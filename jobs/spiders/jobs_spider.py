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

    def parse(self, response):        
        #parse the current result page
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()             
        for joblink in joblinks:
            url = response.urljoin(joblink)
            yield scrapy.Request(url, callback = self.parse_job)
        ###
                
        #extract the total number of results
        #pagination_text looks like: 1-15 от 28348        
        pagination_text = response.xpath('//*[@id=\'search_results\']/table/tr[2]/td[1]/text()').extract()[0]
        pagination_splitted = re.split(r'\D+',pagination_text)
        if len(pagination_splitted) != 3:
            print("Error")
            #TODO - raise an error
        pagination_splitted = [int(num) for num in pagination_splitted]
        start_page = pagination_splitted[0]
        step_pagination = pagination_splitted[1]
        total_entries = pagination_splitted[2]
        
        #create the URLs to follow by using the information in pagination_splitted
        url_left_part="http://www.jobs.bg/front_job_search.php?frompage="
        url_right_part="&all_cities=0&all_categories=0&all_type=0&all_position_level=1&all_company_type=1&keyword=#paging"
        
        #for page in range(step_pagination,total_entries,step_pagination):
        #    url = url_left_part + str(page) + url_right_part
        #    yield scrapy.Request(url, callback=self.parse_search_page)
        
    def parse_search_page(self, response):
        #parse the current result page
        joblinks = response.xpath('//*[@class=\'joblink\']/@href').extract()             
        for joblink in joblinks:
            url = response.urljoin(joblink)
            yield scrapy.Request(url, callback = self.parse_job)
        ###
 
    def parse_job(self, response):
        item = JobItem()
        item['url'] = response.url
        #
        try:
            title = response.xpath('//*[@class=\'jobTitle\']/text()')[0].extract()
            item['title'] = title.encode('utf-8')
        except IndexError as e: #title does not exist
            item['title'] = ''
            item['has_title'] = False            
        #
        try:
            ref_no = response.xpath('//*[@class=\'jobTitleViewBold\' and contains(translate(text(),\'REFNO\',\'refno\'), \'ref.no\')]//..//td[2]//text()')[0].extract()
            item['ref_no'] = ref_no
        except IndexError as e:
            item['ref_no'] = ''
            item['has_ref_no'] = False
        #
        try:
            description = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Описание\')]//..//td[2]//text()').extract()
            description = ''.join(description).strip().encode('utf-8')
            item['description_requirements'] = description
        except IndexError as e:
            item['description_requirements'] = ''
            item['has_description_requirements'] = False
        #
        try:
            location = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Месторабота\')]//..//td[2]//text()')[0].extract()
            item['location'] = location.encode('utf-8')
        except IndexError as e:
            item['location'] = ''
            item['has_location'] = False
        #
        advertiser = response.xpath(u'//*[@class=\'jobTitleViewBold\' and contains(text(),\'Организация\')]//..//td[2]//tr[1]//text()').extract()
        advertiser = "".join(advertiser).strip()
        item['advertiser'] = advertiser.encode('utf-8')
        #
        #date = response.xpath(u'//*[@class=\'jobTitle\']/../../../../../tr/td[3]/table/tr[2]/td[2]/table/tr[1]//text()').extract()        
        date = response.xpath(u'//*[contains(text(),\'Дата\')]//..//..//text()').extract()        
        if len(date) == 0:
            item['date'] = ''
            item['has_date'] = False
        else:
            date = ''.join(date)
            date = date.replace('\n','').replace('\t','')
            item['date'] = date
        #
        category = response.xpath(u'//*[contains(text(),\'Категория\')]//..//..//text()').extract()        
        if len(category) == 0:
            item['category'] = ''
            item['has_category'] = False
        else:
            category = ''.join(category)
            category = category.replace('\t','')
            item['category'] = category.encode('utf-8')
        #
        Type = response.xpath(u'//*[contains(text(),\'Вид работа\')]//..//..//text()').extract()        
        if len(Type) == 0:
            item['type'] = ''
            item['has_type'] = False
        else:
            Type = ''.join(Type)
            Type = Type.replace('\t','')
            item['type'] = Type.encode('utf-8')
        #
        level = response.xpath(u'//*[contains(text(),\'Ниво\')]//..//..//text()').extract()        
        if len(level) == 0:
            item['level'] = ''
            item['has_level'] = False
        else:
            level = ''.join(level)
            level = level.replace('\t','')
            item['level'] = level.encode('utf-8')
        #
        work_grade = response.xpath(u'//*[contains(text(),\'Вид заетост\')]//..//..//text()').extract()        
        if len(work_grade) == 0:
            item['work_grade'] = ''
            item['has_work_grade'] = False
        else:
            work_grade = ''.join(work_grade)
            work_grade = work_grade.replace('\t','')
            item['work_grade'] = work_grade.encode('utf-8')

        yield item
                
        
