#!/usr/bin/python

import time
import urllib
import base64
import hmac
import hashlib

def aws_signed_request(region, params, public_key, private_key, associate_tag=None, version='2011-08-01'):
    
    """
    Copyright (c) 2010-2012 Ulrich Mierendorff

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
    """
    
    """
    Parameters:
        region - the Amazon(r) region (ca,com,co.uk,de,fr,co.jp)
        params - a dictionary of parameters, for example
                    {'Operation': 'ItemLookup',
                     'ItemId': 'B000X9FLKM',
                     'ResponseGroup': 'Small'}
        public_key - your "Access Key ID"
        private_key - your "Secret Access Key"
        version [optional]
    """
    
    # some paramters
    method = 'GET'
    host = 'webservices.amazon.' + region
    uri = '/onca/xml'
    
    # additional parameters
    params['Service'] = 'AWSECommerceService'
    params['AWSAccessKeyId'] = public_key
    params['Timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    params['Version'] = version
    if associate_tag:
        params['AssociateTag'] = associate_tag
    
    # create the canonicalized query
    canonicalized_query = [urllib.quote(param).replace('%7E', '~') + '=' + urllib.quote(params[param]).replace('%7E', '~')
                            for param in sorted(params.keys())]
    canonicalized_query = '&'.join(canonicalized_query)
    
    # create the string to sign
    string_to_sign = method + '\n' + host + '\n' + uri + '\n' + canonicalized_query;
    
    # calculate HMAC with SHA256 and base64-encoding
    signature = base64.b64encode(hmac.new(key=private_key, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    
    # encode the signature for the request
    signature = urllib.quote(signature).replace('%7E', '~')

    return 'http://' + host + uri + '?' + canonicalized_query + '&Signature=' + signature

