import math
import os

import scrapy

import orjson
from scrapy_redis.spiders import RedisSpider

from parsers.QQMusic_parser import singer_list_parse, song_list_parse
from GH_scrapy.items import GhYqqItem

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

api_url = "https://u6.y.qq.com/cgi-bin/musics.fcg"

class YqqSpider(RedisSpider):
    name = "yqq"
    redis_key = "yqq:start_urls"
    redis_batch_size = 8
    allowed_domains = ["y.qq.com"]
    CALLBACKS = {"singer_data": "singer_list_parse", "song_data": "song_list_parse"}
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {"GH_scrapy.middlewares.YqqScrapyDownloaderMiddleware": 543},
        "ITEM_PIPELINES": {"GH_scrapy.pipelines.YqqMySQLPipeline": 300},
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 0.05,
        "MYSQL_DB": "Yqq",
        "DEFAULT_REQUEST_HEADERS": {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
        "referer": "https://y.qq.com/",
        "accept": "application/octet-stream",
        "cookie": os.environ.get("YQQ_COOKIE", "")
        }
    }

    def make_request_from_data(self, data):
        payload = orjson.loads(data)
        return scrapy.Request(
            payload["url"],
            method=payload["method"],
            callback=getattr(self, self.CALLBACKS[payload["meta"]["sign"]]),
            meta=payload["meta"],
            headers=self.settings.get("YQQ_REQUEST_HEADERS")
        )



    # 出于简化考虑，我将初始的歌手列表十条请求直接丢进初始队列
    def singer_list_parse(self, response):
        singer_mid = singer_list_parse(response)
        begin = 0    # 第一次请求，只拿第 1 页，具体页数等第一次返回值
        for singer in singer_mid:
            yield scrapy.Request(url=api_url, method="POST", callback=self.song_list_parse,
                                 meta={"sign": "song_data", "begin": begin, "singerMid": singer})

    def song_list_parse(self, response):
        max_page, recommend_singer_list, items = song_list_parse(response)

        if response.meta["begin"] + 100 < max_page:   # 差点将 +100 的翻页删掉，我是sb
            yield scrapy.Request(url=api_url, method="POST", callback=self.song_list_parse,
                                 meta={"sign": "song_data", "begin": response.meta["begin"] + 100, "singerMid": response.meta["singerMid"]})

        if response.meta["begin"] == 0:
            for recommend_singer in recommend_singer_list:
                yield scrapy.Request(url=api_url, method="POST", callback=self.song_list_parse,
                                     meta={"sign": "song_data", "begin": 0, "singerMid": recommend_singer["singerMid"]})

        for item in items:
            yield GhYqqItem(**item)




    @classmethod
    def singer_seed(cls, pages):
        return [orjson.dumps({"url": "https://u6.y.qq.com/cgi-bin/musics.fcg",
                              "method": "POST",
                              "meta": {"sign": "singer_data", "page": p}
                              })
                for p in range(0, pages)]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        seed = cls.singer_seed(10)

        if spider.server.llen(spider.redis_key) == 0:
            spider.server.lpush(spider.redis_key, *seed)
            spider.logger.info("新的一轮：已把种子 URL 投进 %s", spider.redis_key)

        return spider
