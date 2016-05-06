import base64
import random
from scrapy.conf import settings

class ProxyMiddleware(object):
  def process_request(self, request, spider):
    request.meta['proxy'] = "http://23.81.251.102:29842"

    proxy_user_pass = "dsudom:43FVYMRy"
    encoded_user_pass = base64.encodestring(proxy_user_pass)
    request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass


class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua  = random.choice(settings.get('USER_AGENT_LIST'))
        if ua:
            request.headers.setdefault('User-Agent', ua)