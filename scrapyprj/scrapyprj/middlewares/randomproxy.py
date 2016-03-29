#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import base64
import logging

logger = logging.getLogger(__name__)

class ProxyDownloaderMiddleware(object):

    def __init__(self, settings):
        self.proxy_list = settings.get('PROXY_LIST')
        self.proxy_pattern = r'^\s*(\w+://)(\S+:\S+@)?(\S+)(#.*)?'
        fin = open(self.proxy_list)

        self.proxies = {}
        for line in fin.readlines():
            # extract proxy address using regular expression
            match = re.match(self.proxy_pattern, line)

            if len(match.groups()) == 0:
                continue

            # key: proxy address in format http://domain.com:port/
            # value: authentication info in format usernaem:password

            #  Cut trailing @ in username:password
            if match.group(2):
                user_pass = match.group(2)[:-1]
            else:
                user_pass = ''

            self.proxies[match.group(1) + match.group(3)] = user_pass

        fin.close()

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        return cls(settings)

    def process_request(self, request, spider):
        # Don't overwrite existing valid proxy with a random one (server-side
        # state for IP)
        if request.meta.get('proxy') and re.match(
                self.proxy_pattern, request.meta.get('proxy')):
            return

        proxy_address = random.choice(self.proxies.keys())
        proxy_user_pass = self.proxies[proxy_address]

        request.meta['proxy'] = proxy_address
        logger.debug('proxy: %s', proxy_address)
        if proxy_user_pass:
            basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
            request.headers['Proxy-Authorization'] = basic_auth

    def process_exception(self, request, exception, spider):
        proxy = request.meta['proxy']
        #  logger.debug('Removing failed proxy <%s>, %d proxies left' % (
        #  proxy, len(self.proxies)))
        try:
            if proxy in self.proxies:
                # don't delete
                #  del self.proxies[proxy]
                pass
        except ValueError:
            pass