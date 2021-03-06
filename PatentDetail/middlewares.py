# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
import json
import requests
from twisted.internet.error import TimeoutError
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
import logging
from .Proxy import Proxy


logger = logging.getLogger(__name__)
PROXY = Proxy()


class GetFromLocalityMiddleware(object):
    def process_request(self, request, spider):
        """
        尝试从本地获取源文件，如果存在，则直接获取
        :param request:
        :param spider:
        :return:
        """
        # 提取出code
        filename = request.meta['publication_number']
        # 文件存放位置
        path = request.meta['path']
        # 该路径存在该文件
        filepath = os.path.join(path, '%s.html' % filename)
        if os.path.exists(filepath):
            fp = open(filepath, 'rb')
            body = fp.read()
            fp.close()
            # 从本地加载的文件不再重新写入
            request.meta['load_from_local'] = True
            return HtmlResponse(url=request.url, headers=request.headers, body=body, request=request)
        return None


class RetryOrErrorMiddleware(RetryMiddleware):
    """在之前的基础上增加了一条判断语句，当重试次数超过阈值时，发出错误"""

    def _retry(self, request, reason, spider):
        # 获取当前的重试次数
        retry_times = request.meta.get('retry_times', 0) + 1
        # 最大重试次数
        max_retry_times = self.max_retry_times
        if 'max_retry_times' in request.meta:
            max_retry_times = request.meta['max_retry_times']

        # 超出最大 直接报错即可
        if retry_times > max_retry_times:
            logger.error('%s %s retry times beyond the bounds' % (request.url, request.meta['title']))
        super()._retry(request, reason, spider)

    def process_exception(self, request, exception, spider):
        # 碰到时间异常则直接返回
        # if isinstance(exception, TimeoutError):
        PROXY.dirty = True
        return request


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        # 最大重试次数
        retry_times = request.meta.get('retry_times', 0)
        max_retry_times = spider.crawler.settings.get('MAX_RETRY_TIMES')
        # 如果存在尝试，则换一个代理
        global PROXY
        proxy = PROXY.get_proxy()
        # 最后一次尝试不使用代理
        if proxy and retry_times != max_retry_times:
            logger.info('使用代理%s' % proxy)
            request.meta['proxy'] = 'http://%s' % proxy
        else:
            reason = '代理获取失败' if proxy is None else ('达到最大重试次数[%d/%d]' % (retry_times, max_retry_times))
            logger.warning('%s，使用自己的IP' % reason)

