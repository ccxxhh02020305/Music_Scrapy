import os

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


BOT_NAME = "GH_scrapy"

SPIDER_MODULES = ["GH_scrapy.spiders"]
NEWSPIDER_MODULE = "GH_scrapy.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# YQQ_REQUEST_HEADERS = {
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
#         "referer": "https://y.qq.com/",
#         "accept": "application/octet-stream",
#         "cookie": "pgv_pvid=639648080; fqm_pvqid=1e1b2713-dd16-4f41-83e5-0d1d69cd7d27; fqm_sessionid=ea966420-3d6e-419c-aa2c-40932cb18040; pgv_info=ssid=s5171476354; ts_last=y.qq.com/; ts_uid=7202732808"
#     }

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
# DOWNLOAD_DELAY = 0.02

MAX_IDLE_TIME_BEFORE_CLOSE = 30

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False


# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "GH_scrapy.middlewares.GhScrapySpiderMiddleware": 543,
#}


# DOWNLOADER_MIDDLEWARES = {
#    "GH_scrapy.middlewares.GhScrapyDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
   "scrapy.extensions.telnet.TelnetConsole": None,
}




MYSQL_HOST       =     os.environ.get("MYSQL_HOST", "192.168.50.2")
MYSQL_PORT       =     int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER       =     os.environ.get("MYSQL_USER", "crawler")
MYSQL_PASSWORD   =     os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB         =     os.environ.get("MYSQL_DB", "Yqq")
MYSQL_FLUSH_SIZE =     int(os.environ.get("MYSQL_FLUSH_SIZE", "100"))



# ITEM_PIPELINES = {
#    "GH_scrapy.pipelines.YqqMySQLPipeline": 300,
# }

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "GH_scrapy.dupefilter.MetaAwareDupeFilter"
SCHEDULER_PERSIST = True   # 不主动清空队列，支持断点续爬

REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.50.2")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PARAMS = {
    "password": os.environ.get("REDIS_PASSWORD", "85696060CCxxhh"),
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
