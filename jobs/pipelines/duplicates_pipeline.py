# -*- coding: utf-8 -*-

from scrapy.exceptions import DropItem

class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['url'] in self.ids_seen:
            spider.logger.info("Duplicate job item found for job: %s" % item['url'])            
            raise DropItem("Duplicate job item found for job: %s" % item['url'])
        else:
            self.ids_seen.add(item['url'])
            return item