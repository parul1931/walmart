# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader.processors import TakeFirst

class WalmartItem(scrapy.Item):
    title = scrapy.Field(output_processor=TakeFirst())
    upc = scrapy.Field(output_processor=TakeFirst())
    rank = scrapy.Field(output_processor=TakeFirst())
    category = scrapy.Field(output_processor=TakeFirst())
    walmart_price = scrapy.Field(output_processor=TakeFirst())
    homedepot_price = scrapy.Field(output_processor=TakeFirst())
    target_price = scrapy.Field(output_processor=TakeFirst())
    amazon_price1 = scrapy.Field(output_processor=TakeFirst())
    amazon_price2 = scrapy.Field(output_processor=TakeFirst())
    amazon_price3 = scrapy.Field(output_processor=TakeFirst())
    weight = scrapy.Field(output_processor=TakeFirst())
    wt_cost = scrapy.Field(output_processor=TakeFirst())
    Tax_Cost = scrapy.Field(output_processor=TakeFirst())
    Fees = scrapy.Field(output_processor=TakeFirst())
    Tot_Cost = scrapy.Field(output_processor=TakeFirst())
    Profit = scrapy.Field(output_processor=TakeFirst())
    ROI = scrapy.Field(output_processor=TakeFirst())


class CategoryItem(scrapy.Item):
    category = scrapy.Field(output_processor=TakeFirst())
    top5 = scrapy.Field(output_processor=TakeFirst())
