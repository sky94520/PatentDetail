# -*- coding: utf-8 -*-

# Scrapy settings for PatentDetail project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os

BOT_NAME = 'PatentDetail'

SPIDER_MODULES = ['PatentDetail.spiders']
NEWSPIDER_MODULE = 'PatentDetail.spiders'
# Obey robots.txt rules
ROBOTSTXT_OBEY = False
BASEDIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

# 最大重试次数
MAX_RETRY_TIMES = 20

DOWNLOADER_MIDDLEWARES = {
    'PatentDetail.middlewares.GetFromLocalityMiddleware': 543,
    'PatentDetail.middlewares.RetryOrErrorMiddleware': 550,
    'PatentDetail.middlewares.ProxyMiddleware': 843,
}

ITEM_PIPELINES = {
    'PatentDetail.pipelines.SavePagePipeline': 300,
    'PatentDetail.pipelines.FilterPipeline': 301,
    'PatentDetail.pipelines.JsonPipeline': 302,
}
