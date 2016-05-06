import re
import json

from scrapy import Spider
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.utils.response import open_in_browser

from walmart_spider.items import WalmartItem

is_empty = lambda x, y="": x[0] if x else y

class KohlsSpider(Spider):
    name = 'kohls'

    allowed_domains = ['www.kohls.com']

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0'

    BASE_URL = 'http://www.kohls.com'

    start_urls = ['http://www.kohls.com/feature/sitemapmain.jsp']

    def parse(self, response):
        links = response.xpath(
            '//div[@id="sitemap-content"]/div/ul/li/a[contains(@href,"catalog")]/@href'
        ).extract()

        for link in links:
            yield Request(url=self.BASE_URL+link, callback=self.parse_product)

    def parse_product(self, response):

        script = response.xpath(
            '//script[contains(text(), "pmpSearchJsonData")]'
        ).extract()[0].replace('\n', '').strip()

        data = json.loads(re.findall('pmpSearchJsonData = ({.*});', script)[0])

        for product in data['productInfo']['productList']:
            l = ItemLoader(item=WalmartItem(), response=response)

            l.add_value('title', product['productTitle'])
            l.add_value('price', product['pricing']['regularPrice'])

            yield l.load_item()

        next_link = is_empty(
            response.xpath('//link[@rel="next"]/@href').extract()
        )
        if next_link:
            yield Request(url=self.BASE_URL+next_link,
                          callback=self.parse_product)
