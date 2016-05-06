import re
import json
import datetime
from scrapy import Spider
from scrapy.http import Request
from walmart_spider.aws_signed_request import aws_signed_request
from scrapy.loader import ItemLoader
from bs4 import BeautifulSoup
import requests
import urllib2

from walmart_spider.items import WalmartItem
import time
import xml.etree.ElementTree as ET
from fake_useragent import UserAgent
ua = UserAgent()

is_empty = lambda x, y="": x[0] if x else y

class TargetSpider(Spider):
	name = 'target'

	allowed_domains = ['www.target.com', 'tws.target.com']

	user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
			'Gecko/20100101 Firefox/35.0'

	BASE_URL = 'http://www.target.com'

	start_urls = ['http://www.target.com/c/more/-/N-5xsxf#?lnk=ct_menu_12_1&'
				  'intc=1865103|null']

	JSON_SEARCH_URL = "http://tws.target.com/searchservice/item/" \
					  "search_results/v2/by_keyword?" \
					  "callback=getPlpResponse" \
					  "&response_group=Items%2CVariationSummary" \
					  "&category={category}" \
					  "&sort_by=bestselling" \
					  "&pageCount=60" \
					  "&zone=PLP" \
					  "&facets=" \
					  "&view_type=medium" \
					  "&page={page}" \
					  "&offset={index}" \
					  "&stateData="

	def parse(self, response):
		categories = response.xpath(
			'//ul[@class="innerCol"]/li/a/@href').re('N-(.*)#')

		for category in categories:
			new_meta = response.meta.copy()
			new_meta['category'] = category
			new_meta['next_page'] = 2
			new_meta['index'] = new_meta['next_page']*60

			yield Request(url=self.JSON_SEARCH_URL.format(category=category,
														  page=1,
														  index=0),
						  meta=new_meta,
				 		  callback=self.parse_product)

	def parse_product(self, response):
		data = json.loads(
			re.findall('getPlpResponse\((.*)\)', response.body)[0]
		)

		if len(data['searchResponse']['items']['Item']) > 0:

			for product in data['searchResponse']['items']['Item']:
				l = ItemLoader(item=WalmartItem(), response=response)
				if 'priceSummary' in product.keys():
					l.add_value('upc', product['upc'])
					l.add_value('target_price',
								product['priceSummary']['offerPrice']['amount'])
					upc = product['upc']
					target_price = product['priceSummary']['offerPrice']['amount']
					print "upc : ", upc
					print "target_price : ", target_price

					if upc:
						region = REGION
						public_key = AWS_ACCESS_KEY_ID
						private_key = AWS_ACCESS_SECRET_KEY
						associate_tag = ASSOCIATE_TAG
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
						time.sleep(1)
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
													print "\n link : ", link
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
								
								amazon_price1 = new_price[0].split("$")
								amazon_price1 = float(amazon_price1[1])

								if "-" in target_price:
									price = target_price.split("-")
									price1 = float(price[0].split("$")[1])
									price2 = float(price[1].split("$")[1])
									if price2 < amazon_price1:
										target_price = price2
									else:
										target_price = price1
								else:
									target_price = float(target_price.split("$")[1])

								
								weight = float(weight)
							
								wt_cost = weight * 0.55
								l.add_value('wt_cost', wt_cost)
								
								
								Tax_Cost = target_price * 0.065
								l.add_value('Tax_Cost', Tax_Cost)
								
								Fees = amazon_price1 * 0.27
								l.add_value('Fees', Fees)
								
								
								Tot_Cost = target_price + wt_cost + Tax_Cost + Fees
								l.add_value('Tot_Cost', Tot_Cost)
								
								
								Profit = amazon_price1 - Tot_Cost
								l.add_value('Profit', Profit)
								
								
								ROI = Profit / (target_price + wt_cost + Tax_Cost)
								l.add_value('ROI', ROI)
								
								yield l.load_item()
						except:
							pass

			page = response.meta['next_page']
			category = response.meta['category']
			index = response.meta['index']
			new_meta = response.meta.copy()
			new_meta['next_page'] = page + 1
			new_meta['index'] = new_meta['next_page']*60
			yield Request(url=self.JSON_SEARCH_URL.format(category=category,
														  page=page,
														  index=index),
						  meta=new_meta,
						  callback=self.parse_product)
