import re
import datetime
from walmart_spider.aws_signed_request import aws_signed_request
from scrapy import Spider
from scrapy.http import Request, FormRequest
from scrapy.loader import ItemLoader
from scrapy.log import WARNING, DEBUG, INFO, ERROR

import requests
from walmart_spider.items import WalmartItem
import urllib2
from bs4 import BeautifulSoup
import time
import xml.etree.ElementTree as ET
import sys
from fake_useragent import UserAgent
ua = UserAgent()

is_empty = lambda x, y="": x[0] if x else y

# try:
#     from captcha_solver import CaptchaBreakerWrapper
# except Exception as e:
#     print '!!!!!!!!Captcha breaker is not available due to: %s' % e
#
#     class CaptchaBreakerWrapper(object):
#         @staticmethod
#         def solve_captcha(url):
#             msg("CaptchaBreaker in not available for url: %s" % url,
#                 level=WARNING)
#             return None


class WalmartSpider(Spider):
    name = 'walmart'

    allowed_domains = ['www.walmart.com', 'www.amazon.com']
    start_urls = ['http://www.walmart.com/all-departments']

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0'

    BASE_URL = 'http://www.walmart.com'

    AMAZON_SEARCH_URL = "http://www.amazon.com/s/ref=nb_sb_noss?" \
                        "field-keywords={upc}"

    # def __init__(self, captcha_retries='10', *args, **kwargs):
    #     self.captcha_retries = int(captcha_retries)
    #     self._cbw = CaptchaBreakerWrapper()
    #     super(WalmartSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        headers = {"Accept": "*/*",
                   "Accept-Encoding": "gzip, deflate",
                   "User-Agent": "runscope/0.1"}
        yield Request(url=self.start_urls[0], headers=headers,
                      callback=self.parse_category)

    # def parse_captcha(self, response):
    #     if self._has_captcha(response):
    #         result = self._handle_captcha(response, self.parse_captcha)
    #     else:
    #         result = self.parse_without_captcha(response)
    #     return result
    #
    # def parse_without_captcha(self, response):
    #     links = response.xpath(
    #         '//a[@class="all-depts-links-category"]/@href'
    #     ).extract()
    #
    #     for link in links:
    #         print '-'*25, link, '-'*25
    #         yield Request(url=self.BASE_URL+link, callback=self.parse_product)

    def parse_category(self, response):
        links = response.xpath(
            '//a[@class="all-depts-links-category"]/@href'
        ).extract()

        for link in links:
            print '-'*25, link, '-'*25
            yield Request(url=self.BASE_URL+link, callback=self.parse_product)

    def parse_product(self, response):

        product_links = response.xpath(
            '//ul[@class="tile-list tile-list-grid"]/li/div/'
            'a[@class="js-product-title"]/@href'
        ).extract()

        for product_link in product_links:
            yield Request(url=self.BASE_URL+product_link, callback=self.parse)

        next_link = is_empty(response.xpath(
            '//a[@class="paginator-btn paginator-btn-next"]/@href'
        ).extract())
        if next_link:
            next_link = re.sub(
                '\?.*', next_link, response.url, flags=re.IGNORECASE
            )

            yield Request(url=next_link, callback=self.parse_product)

    def parse(self, response):
        l = ItemLoader(item=WalmartItem(), response=response)
        upc = response.xpath('//meta[@property="og:upc"]/@content').extract()
        price = ''.join(
            response.xpath(
                '//div[@itemprop="price"][1]/text() |'
                ' //div[@itemprop="price"][1]/*/text()'
            ).extract()
        )

        if not price:
            script = is_empty(response.xpath(
                '//script[contains(text(), "productSellersMap")]/text()'
            ).extract())
            price = is_empty(
                re.findall('\"currencyAmount\":([\d+,]?\d+.\d+)', script)
            )
            if not price:
                script = is_empty(
                    response.xpath(
                        '//script[contains(text(),"item_price")]/text()'
                    ).extract()
                )
                price = is_empty(
                    re.findall("item_price\',\'(\$[\d+,]?\d+.\d+)\'", script)
                )
            else:
                price = '$' + price

        l.add_value('upc', is_empty(upc))
        if price:
            l.add_value('walmart_price', price.replace(" ", ''))

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
                "ItemId": upc[0],
                "ResponseGroup": "SalesRank, ItemAttributes, Offers, OfferListings",
                "Operation": "ItemLookup",
                "SearchIndex": "All"
            }

            url = aws_signed_request(region, params, public_key, private_key, associate_tag, version='2011-08-01')

            print url

            #time.sleep(1)
            try:
                header = ua.random
                headers = {"User-Agent": header}
                r = requests.get(url, headers=headers)
                content = r.text.encode("UTF-8")
                root = ET.fromstring(content)

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
                                            #time.sleep(1)
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
                                                        price = ' '.join(span.text.split())
                                                        new_price.append(price)
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
                    
                    if "-" in price:
                        w_price = price.split("-")
                        price1 = float(w_price[0].split("$")[1])
                        price2 = float(w_price[1].split("$")[1])
                        if price2 < amazon_price1:
                            walmart_price = price2
                        else:
                            walmart_price = price1
                    else:
                        walmart_price = float(price.split("$")[1])

                    weight = float(weight)
                    amazon_price1 = new_price[0].split("$")
                    amazon_price1 = float(amazon_price1[1])

                    wt_cost = weight * 0.55
                    l.add_value('wt_cost', wt_cost)
                    
                    Tax_Cost = walmart_price * 0.065
                    l.add_value('Tax_Cost', Tax_Cost)
                    
                    Fees = amazon_price1 * 0.27
                    l.add_value('Fees', Fees)
                    
                    Tot_Cost = walmart_price + wt_cost + Tax_Cost + Fees
                    l.add_value('Tot_Cost', Tot_Cost)
                    
                    Profit = amazon_price1 - Tot_Cost
                    l.add_value('Profit', Profit)
                    
                    ROI = Profit / (walmart_price + wt_cost + Tax_Cost)
                    l.add_value('ROI', ROI)
                    yield l.load_item()
            except:
                pass
        # if upc:
        #     new_meta = response.meta.copy()
        #     new_meta['item'] = l
        #     yield Request(url=self.AMAZON_SEARCH_URL.format(upc=upc[0]),
        #                   meta=new_meta, callback=self.parse_amazon_category)
        # else:
        
        #yield l.load_item()

    #TODO: handling amazon
#     def parse_amazon_category(self, response):
#         if self._has_captcha(response):
#             yield self._handle_captcha(response, self.parse_amazon_category)
#         else:
#             link = response.xpath('//a[@class="a-link-normal s-access-detail-page'
#                                   '  a-text-normal"]/@href').extract()
#             if link:
#                 new_meta = response.meta.copy()
#                 new_meta['item'] = response.meta['item']
#                 yield Request(url=link[0], meta=new_meta,
#                               callback=self.parse_amazon_product)
#
#     def parse_amazon_product(self, response):
#         if self._has_captcha(response):
#             yield self._handle_captcha(response, self.parse_amazon_product)
#         else:
#             l = response.meta['item']
#             title = response.xpath(
#                 '//span[@id="productTitle"]/text()'
#             ).extract()
#             l.add_value('title', is_empty(title))
#
#             amazon_price = response.xpath(
#                 '//span[@id="priceblock_ourprice"]/text()'
#             ).extract()
#             l.add_value('amazon_price', is_empty(amazon_price))
#
#             weight = is_empty(response.xpath(
#                 '//div[@class="content"]/ul/li/b[contains(text(),'
#                 ' "Weight")]/following::text() | '
#                 '//table[@id="productDetails_detailBullets_sections1"]/'
#                 'tr[contains(.,"Weight")]/td/text()'
#             ).extract(),'').replace('(', '').strip()
#             l.add_value('weight', weight)
#
#             rank_category = response.xpath(
#                 '//li[@id="SalesRank"]/text() |'
#                 '//table[@id="productDetails_detailBullets_sections1"]'
#                 '/tr[contains(.,"Best Seller")]/td'
#             ).re('#(\d+[,\d+]*) in (.*) \(')
#             if rank_category:
#                 l.add_value('rank', rank_category[0])
#                 l.add_value('category', rank_category[1])
#             else:
#                 category = response.xpath(
#                     '//div[@id="wayfinding-breadcrumbs_feature_div"]/ul'
#                     '/li[1]/span/a/text()'
#                 ).extract()
#                 if category:
#                     category = category[0].strip()
#                 l.add_value('category', category)
#
#             yield l.load_item()
#
# # Captcha handling functions.
#     def _has_captcha(self, response):
#         return '.images-amazon.com/captcha/' in response.body_as_unicode()
#
#     def _solve_captcha(self, response):
#         forms = response.xpath('//form')
#         assert len(forms) == 1, "More than one form found."
#
#         captcha_img = forms[0].xpath(
#             '//img[contains(@src, "/captcha/")]/@src').extract()[0]
#
#         self.log("Extracted capcha url: %s" % captcha_img, level=DEBUG)
#         return self._cbw.solve_captcha(captcha_img)
#
#     def _handle_captcha(self, response, callback):
#         captcha_solve_try = response.meta.get('captcha_solve_try', 0)
#         url = response.url
#         self.log("Captcha challenge for %s (try %d)."
#                  % (url, captcha_solve_try),
#                  level=INFO)
#
#         captcha = self._solve_captcha(response)
#
#         if captcha is None:
#             self.log(
#                 "Failed to guess captcha for '%s' (try: %d)." % (
#                     url, captcha_solve_try),
#                 level=ERROR
#             )
#             result = None
#         else:
#             self.log(
#                 "On try %d, submitting captcha '%s' for '%s'." % (
#                     captcha_solve_try, captcha, url),
#                 level=INFO
#             )
#             meta = response.meta.copy()
#             meta['captcha_solve_try'] = captcha_solve_try + 1
#             result = FormRequest.from_response(
#                 response,
#                 formname='',
#                 formdata={'field-keywords': captcha},
#                 callback=callback,
#                 dont_filter=True,
#                 meta=meta)
#
#         return result
