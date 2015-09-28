# -*- coding: utf-8 -*-



from scrapy.exceptions import DropItem

class PrepareDataPipeline(object):    

    def process_item(self, item, spider):
        #Date
        if 'date' in item:
            #get the date string
            try:
                date = item['date'].split(':')[1]
                item['date'] = date
            except IndexError as e:
                spider.logger.warning("Cannot parse date %s for job %s" % (item['date'], item['url']))            
                DropItem("Cannot parse date %s for job %s" % (item['date'], item['url']))            
        
        #default values for unspecified keys        
        for item_key in item.fields:            
            if not item_key in item.keys():
                item[item_key] = ''.encode('utf-8')
            item[item_key] = item[item_key].decode('utf-8')
        #            
        item['description_requirements'] = item['description_requirements'].encode('utf-8').encode('zlib')
        return item
