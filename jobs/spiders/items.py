# -*- coding: utf-8 -*-

"""
Created on Sat Sep 26 19:15:10 2015

@author: pmavrodiev

"""



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
    location = Field() #location of the job, typically the city
    '''    
    Ff location is smaller than a city, e.g. a village the job posting 
    mentions the province e.g.: село Приселци / Област Варна / България
    
    In this case the extracted location will be село Приселци, but we 
    need to extract also the province, which together with the EKATTE list 
    will allows to infer the municipality.
    
    Ideally we could do without this, but there are villages with the same
    name belonging to difference provinces. Hence, the village name and
    the EKATTE list is not enough    
    '''
    location2 = Field() #province 
    advertiser = Field() #the organization advertizing the job
    date = Field()
    category = Field()
    Type = Field()
    level = Field()
    work_grade = Field()
    salary = Field()
   