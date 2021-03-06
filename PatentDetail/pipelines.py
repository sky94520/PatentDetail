# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import re
import json
import pymongo
import datetime
import logging
from scrapy.exceptions import DropItem
from PatentDetail.items import PatentItem


logger = logging.getLogger(__name__)


class FilterPipeline(object):
    """清除特殊字符"""
    def __init__(self):
        # 字符串转为数组
        self.array_keys = ['inventor', 'patent_cls_number', 'agent', 'applicant', 'joint_applicant']
        # TODO:字符串转为datetime
        # self.date_keys = ['application_date', 'publication_date']
        self.date_keys = []
        # 去多个换行
        self.text_keys = ['sovereignty', 'summary']
        self.pattern = re.compile(r'[\n|\r]+')
        # 转成int
        self.int_keys = ['page_number']

    def process_item(self, item, spider):
        try:
            for key, value in item.items():
                if key in self.array_keys:
                    item[key] = []
                    for v in value.split(';'):
                        if len(v) > 0:
                            item[key].append(v)
                elif key in self.date_keys:
                    item[key] = datetime.datetime.strptime(value, '%Y-%m-%d')
                elif key in self.text_keys:
                    item[key] = re.sub(self.pattern, '', value)
                elif key in self.int_keys:
                    item[key] = int(value)
            if 'response' in item:
                del item['response']
        except Exception as e:
            # 在解析时出现错误，则报错后移除该item
            logger.error('process [%s] error: %s' % (item['publication_number'], e))
            raise DropItem()

        return item


class SavePagePipeline(object):
    def process_item(self, item, spider):
        response = item['response']
        # 该文件从本地获取，不再重新保存
        if 'load_from_local' in response.meta and response.meta['load_from_local']:
            return item

        path = response.meta['path']
        publication_number = response.meta['publication_number']

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.html' % publication_number)
        with open(filename, "wb") as fp:
            fp.write(response.body)
        return item


class JsonPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            basedir=crawler.settings.get('BASEDIR'),
        )

    def __init__(self, basedir):
        self.save_path = os.path.join(basedir, 'files', 'detail')
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def process_item(self, item, spider):
        filename = os.path.join(self.save_path, '%s.json' % item['publication_number'])
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(dict(item), ensure_ascii=False, indent=2))
        return item


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None
        # 缓冲区 一定数量则填充一次
        self.buffer = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spdier):
        # 通过application_number保证唯一
        collection = self.db[item.collection]
        result = collection.find_one({'publication_number': item['publication_number']}, {'_id': 1})
        if result is not None:
            raise DropItem('the %s has already saved in database' % item['publication_number'])
        cur_count, max_count = spdier.counter[item['source']]
        # 只有在该json文件全部链接都爬取完成的时候，才会写入到redis中
        if cur_count + 1 >= max_count:
            spdier.db.sadd('page_links', item['source'])
            spdier.counter.pop(item['source'])
        else:
            spdier.counter[item['source']] = (cur_count + 1, max_count)

        del item['source']
        self.buffer.append(dict(item))
        # 每1000个数据写入到数据库中
        if len(self.buffer) >= 100:
            self.db[PatentItem.collection].insert_many(self.buffer)
            self.buffer.clear()
        # 不返回item，则不再输出到控制台
        # return item

    def close_spider(self, spider):
        if len(self.buffer) > 0:
            self.db[PatentItem.collection].insert_many(self.buffer)
            self.buffer.clear()
        self.client.close()


