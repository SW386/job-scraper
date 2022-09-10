# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class JobsItem(scrapy.Item):

    Company = scrapy.Field()
    Job = scrapy.Field()
    Application = scrapy.Field()
    Category = scrapy.Field() 
    Location = scrapy.Field()
