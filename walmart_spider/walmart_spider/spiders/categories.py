from scrapy import Spider
from scrapy.loader import ItemLoader

from walmart_spider.items import CategoryItem

is_empty = lambda x, y="": x[0] if x else y

class WalmartSpider(Spider):
    name = 'categories'

    allowed_domains = ['www.arbitragedashboard.com']
    start_urls = ['http://www.arbitragedashboard.com/software/top-rank-chart/']

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0'

    def parse(self, response):
        trs = response.xpath('//tr')
        for tr in trs:
            l = ItemLoader(item=CategoryItem(), response=response)
            category = is_empty(tr.xpath('./td[1]/text()').extract())
            top5 = is_empty(tr.xpath('./td[5]/text()').extract())

            l.add_value('category', category)
            l.add_value('top5', top5)

            yield l.load_item()

