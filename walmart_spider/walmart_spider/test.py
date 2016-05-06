from aws_signed_request import aws_signed_request
import datetime
import requests

# Service=AWSECommerceService&
# AWSAccessKeyId=AKIAJCAIVLPWYX553QKA&
# AssociateTag=esfera01-20&
# Operation=ItemSearch&
# Keywords=horse,bridle&
# SearchIndex=PetSupplies,SportingGoods&
# Timestamp={timestamp}&
# Signature=[Request Signature]


# http://webservices.amazon.com/onca/xml?
# Service=AWSECommerceService&
# AWSAccessKeyId=[AWS Access Key ID]&
# AssociateTag=[Associate ID]&
# Operation=ItemSearch&
# Keywords=Potter&
# SearchIndex=Books&
# ItemPage=4
# &Timestamp=[YYYY-MM-DDThh:mm:ssZ]
# &Signature=[Request Signature]

region = "com"
public_key = "AKIAJCAIVLPWYX553QKA"
private_key = "VNCDZ5l0IEUqJIrr/0wuh1Cyj+ZxfbA/42d3Cu/a"
associate_tag = "esfera01-20"

params = {
	"AWSAccessKeyId": public_key,
    "Service": "AWSECommerceService",
    "Timestamp": datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
    "AssociateTag": associate_tag,
    "Operation": "ItemSearch",
    #"ItemPage": "1",
    "SearchIndex": "Electronics",
    #"Keywords": "Electronics"
}

url = aws_signed_request(region, params, public_key, private_key, associate_tag, version='2011-08-01')
print "url : ", url

# response = requests.get(url)
# content = response.text

# print "\n content : ", content