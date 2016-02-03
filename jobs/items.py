"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class JobItem(Item):    
    url = Field()
    title = Field() #the title of the job
    ref_no = Field() #Ref.No field
    description_requirements = Field() #description and requirements
    location = Field() #location of the job
    advertiser = Field() #the organization advertizing the job
    date = Field()
    category = Field()
    Type = Field()
    level = Field()
    work_grade = Field()
    salary = Field()
   