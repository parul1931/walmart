import re
from scrapy import Spider
from scrapy.http import Request
from scrapy.loader import ItemLoader
from walmart_spider.items import WalmartItem
from walmart_spider.aws_signed_request import aws_signed_request
from bs4 import BeautifulSoup
import requests
import urllib2
import datetime
import time
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent
ua = UserAgent()

is_empty = lambda x, y="": x[0] if x else y

class HomedepotSpider(Spider):
    name = 'homedepot'

    allowed_domains = ['www.homedepot.com']

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0'

    BASE_URL = 'http://www.homedepot.com/'

    start_urls = ['http://www.homedepot.com/c/site_map']

    def start_requests(self):
        headers = {"Accept": "*/*",
                   "Accept-Encoding": "gzip, deflate",
                   "User-Agent": "runscope/0.1"}
        yield Request(url=self.start_urls[0], headers=headers,
                      callback=self.parse_category)

    def parse_category(self, response):
        links = response.xpath(
            '//ul[@class="linkList l"]/li/'
            'a[contains(@href, "www.homedepot.com/b/")]/@href'
        ).extract()

        for link in links:
            print '-'*25, link, '-'*25
            if 'http' in link:
                yield Request(url=link, callback=self.parse_product)
            else:
                yield Request(url='http://'+link, callback=self.parse_product)

    def parse_product(self, response):

        product_links = response.xpath(
            '//div[contains(@class, "product pod")]/form/*/*/a/@href'
        ).extract()

        for product_link in product_links:
            yield Request(url=self.BASE_URL+product_link, callback=self.parse)

        next_link = is_empty(
            response.xpath('//a[@title="Next"]/@href').extract()
        )
        if next_link:
            yield Request(url=self.BASE_URL+next_link,
                          callback=self.parse_product)

    def parse(self, response):
        l = ItemLoader(item=WalmartItem(), response=response)
        upc = response.xpath('//upc/text()').extract()
        price = response.xpath('//span[@itemprop="price"]/text()').extract()

        upc = is_empty(upc).strip().replace("\n",'').replace('\r', '')
        if len(upc) > 12:
            upc = upc[1:]
        homedepot_price = is_empty(price).strip().replace("\n", '').replace('\r', '')
        
        l.add_value('upc', upc)
        l.add_value('homedepot_price', is_empty(price).strip().replace(
            "\n", '').replace('\r', ''))

        print "\n\n upc : ", upc
        print "price : ", homedepot_price

        if upc:
            region = "com"
            public_key = "AKIAJCAIVLPWYX553QKA"
            private_key = "VNCDZ5l0IEUqJIrr/0wuh1Cyj+ZxfbA/42d3Cu/a"
            associate_tag = "esfera01-20"
            params = {
            "AWSAccessKeyId": public_key,
            "Service": "AWSECommerceService",
            "Timestamp": datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
            "AssociateTag": associate_tag,
            "IdType": "UPC",
            "ItemId": upc,
            "ResponseGroup": "SalesRank, ItemAttributes, Offers, OfferListings",
            "Operation": "ItemLookup",
            "SearchIndex": "All"
            }
            url = aws_signed_request(region, params, public_key, private_key, associate_tag, version='2011-08-01')
            print url
            try:
                header = ua.random
                headers = {"User-Agent": header}
                r = requests.get(url, headers=headers)
                content = r.text.encode("UTF-8")
                root = ET.fromstring(content)
                time.sleep(1)
                detail = []
                details = []
                new_price = []

                rank = ''
                weight = None
                title = None
                category = ''

                for t in root:
                    for t1 in t:
                        for t2 in t1:
                            if "SalesRank" in t2.tag:
                                rank = t2.text.encode("UTF-8")
                                
                            if "ItemAttributes" in t2.tag:
                                for t3 in t2:
                                    if "ProductTypeName" in t3.tag:
                                        category = t3.text.encode("UTF-8")

                                    if "ItemDimensions" in t3.tag:
                                        for t4 in t3:
                                            if "Weight" in t4.tag:
                                                weight = t4.text.encode("UTF-8")
                                                

                                    if "Title" in t3.tag:
                                        title = t3.text.encode("UTF-8")
                                        

                            if "Offers" in t2.tag:
                                for t5 in t2:
                                    if "MoreOffersUrl" in t5.tag:
                                        link = t5.text
                                        length = len(new_price)
                                        if link != "0" and length < 4:
                                            time.sleep(1)
                                            header = ua.random
                                            
                                            headers = {"User-Agent": header}
                                            r = requests.get(link, headers=headers)
                                            page = r.text
                                            soup = BeautifulSoup(page, 'html.parser')

                                            a = soup.find("a", {"class": "a-link-normal a-text-bold"})
                                            if a:
                                                url1 = "http://www.amazon.com"+a["href"]
                                                header = ua.random
                                                headers = {"User-Agent": header}
                                                r = requests.get(url1, headers=headers)
                                                page1 = r.text
                                                soup1 = BeautifulSoup(page1, 'html.parser')
                                            else:
                                                soup1 = soup

                                            n = 1
                                            for div in soup1.find_all("div", {"class": "a-row a-spacing-mini olpOffer"}):
                                                if n < 4:
                                                    div1 = div.find("div", {"class": "a-column a-span2"})
                                                    
                                                    span = div1.find("span", {"class": "a-size-large a-color-price olpOfferPrice a-text-bold"})
                                                    if span:
                                                        price1 = ' '.join(span.text.split())
                                                        new_price.append(price1)
                                                        n = n+1
                if new_price and title is not None and weight is not None:
                    l.add_value('title', title)
                    #l.add_value('upc', upc[0])
                    l.add_value('rank', rank)
                    l.add_value('category', category)
                    l.add_value('weight', weight)
                    #l.add_value('walmart_price', price)
                    l.add_value('amazon_price1', new_price[0])
                    try:
                        if new_price[1]:
                            l.add_value('amazon_price2', new_price[1])
                    except:
                        price1 = ''
                        l.add_value('amazon_price2', price1)

                    try:
                        if new_price[2]:
                            l.add_value('amazon_price3', new_price[2])
                    except:
                        price2 = ''
                        l.add_value('amazon_price3', price2)
                        l.add_value('weight', weight)    

                    amazon_price1 = new_price[0].split("$")
                    amazon_price1 = float(amazon_price1[1])

                    if "-" in homedepot_price:
                        price = homedepot_price.split("-")
                        price1 = float(price[0].split("$")[1])
                        price2 = float(price[1].split("$")[1])
                        if price2 < amazon_price1:
                            homedepot_price = price2
                        else:
                            homedepot_price = price1
                    else:
                        homedepot_price = float(homedepot_price.split("$")[1])

                    weight = float(weight)
                    
                    wt_cost = weight * 0.55
                    l.add_value('wt_cost', wt_cost)

                    Tax_Cost = homedepot_price * 0.065
                    l.add_value('Tax_Cost', Tax_Cost)
                    
                    Fees = amazon_price1 * 0.27
                    l.add_value('Fees', Fees)
                    
                    Tot_Cost = homedepot_price + wt_cost + Tax_Cost + Fees
                    l.add_value('Tot_Cost', Tot_Cost)
                    
                    Profit = amazon_price1 - Tot_Cost
                    l.add_value('Profit', Profit)
                    
                    ROI = Profit / (homedepot_price + wt_cost + Tax_Cost)
                    l.add_value('ROI', ROI)
                    
                    yield l.load_item()

            except Exception as e:
                print "\n Exception : ", e