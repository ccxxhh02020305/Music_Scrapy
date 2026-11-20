from scrapy import signals
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import time
from urllib.parse import urlencode
from server import signer
from server.yqq_data import data2middlewares
import orjson

import asyncio

class BilibiliScrapySpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BilibiliScrapyDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class YqqScrapySpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class YqqScrapyDownloaderMiddleware:
    def __init__(self):
        signer.init()

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    async def process_request(self, request, spider):
        # 中间件 replace 的本质不是修改 Request，而是将一个新的 Request二次入队，因此要在中间件开头将这部分请求不加处理抛回
        if not request.meta.get("sign") or request.meta.get("signed"):
            return None

        singerMid = request.meta.get("singerMid", None)
        _time = str(int(time.time() * 1000))
        data = data2middlewares(request, singerMid)


        sign, en_data = await asyncio.to_thread(signer.sign_encrypt, data)
        params = {
            "_": _time,
            "encoding": "ag-1",
            "sign": sign
        }

        meta = request.meta
        meta["signed"] = True

        api_url = request.url.split("?", 1)[0]
        new_request = request.replace(
            url = f"{api_url}?{urlencode(params)}",
            method = "POST",
            body = en_data,
            headers = request.headers,
            meta = meta,
            dont_filter = True, # 第一次去重在进中间层之前，使用 mate 参数，本请求重新入队后是有 params 的 url，因此不会被去重，但因为两次入队逻辑上并无不同，本次入队请求不考虑重复的可能性
        )

        return new_request

    async def process_response(self, request, response, spider):
        if not request.meta.get("sign") or not (200 <= response.status < 300):
            return response
        de_resp = await asyncio.to_thread(signer.decrypt_resp, response)
        new_response = response.replace(body = de_resp.encode())
        return new_response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
