import scrapy

from parsers.bili_parser import parse_season, parse_recommend_urls
from parsers.bili_urls import recommend_api
from GH_scrapy.items import BiliItem

from urllib.parse import urlencode
import json

# URL = "https://www.bilibili.com/bangumi/play/ss41012?from_spmid=666.25.recommend.0"
URL = "https://www.bilibili.com/bangumi/play/ep5852945?from_spmid=666.9.recommend.1"

class BiliSpider(scrapy.Spider):
    name = "bilibili"
    allowed_domains = ["bilibili.com"]
    start_urls = [URL]
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {"GH_scrapy.middlewares.BilibiliScrapyDownloaderMiddleware": 543},
        "ITEM_PIPELINES": {"GH_scrapy.pipelines.BiliMySQLPipeline": 300},
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "DOWNLOAD_DELAY": 0.2,
        "MYSQL_DB": "Yqq",  # 同库不同表也完全可以，省一个库
        "DEFAULT_REQUEST_HEADERS": {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36 Edg/155.0.0.0",
            "referer": "https://www.bilibili.com/anime/?spm_id_from=333.1007.0.0"
        }
    }

    async def start(self):
        for u in self.start_urls:
            yield scrapy.Request(url=u, callback=self.parse_season)   # 回环开始

    def parse_season(self, response):    # 回环的入口，也是终点
        info = parse_season(response)
        yield BiliItem(**info)
        url, params = recommend_api(info["season_id"])
        yield scrapy.Request(url=f"{url}?{urlencode(params)}", callback=self.parse_recommend)

    def parse_recommend(self, response):
        for u in parse_recommend_urls(response.json()):
            yield scrapy.Request(url=u, callback=self.parse_season)  # 回环闭合

import os

def redis_available():
    if os.environ.get("SCRAPY_OPEN") != "1":
        return False
    try:
        import scrapy_redis
    except ImportError:
        return False
    return True

if redis_available():
    from scrapy_redis.spiders import RedisSpider

    class BiliRedisSpider(RedisSpider):
        name = "bili_redis"
        redis_key = "bili_redis:start_urls"
        redis_batch_size = 8
        allowed_domains = ["bilibili.com"]
        custom_settings = {
            "DOWNLOADER_MIDDLEWARES": {"GH_scrapy.middlewares.BilibiliScrapyDownloaderMiddleware": 543},
            "ITEM_PIPELINES": {"GH_scrapy.pipelines.BiliMySQLPipeline": 300},
            "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
            "DOWNLOAD_DELAY": 0.7,
            "MYSQL_DB": "Yqq",  # 同库不同表也完全可以，省一个库
            "DEFAULT_REQUEST_HEADERS": {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36 Edg/155.0.0.0",
            "referer": "https://www.bilibili.com/anime/?spm_id_from=333.1007.0.0"
            }
        }

        parse            = BiliSpider.parse_season
        parse_season     = BiliSpider.parse_season
        parse_recommend  = BiliSpider.parse_recommend

        @classmethod
        def from_crawler(cls, crawler, *args, **kwargs):
            spider = super().from_crawler(crawler, *args, **kwargs)   # 内部会 setup_redis，self.server 已就绪
            # 只在这一轮没跑过时自举一次
            if spider.server.scard("bili_redis:dupefilter") == 0:
                spider.server.lpush(spider.redis_key, json.dumps({"url": URL}))
                spider.logger.info("新的一轮：已把种子 URL 投进 %s", spider.redis_key)
            return spider