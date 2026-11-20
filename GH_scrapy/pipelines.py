import pymysql

from parsers.QQMusic_storage import connect, init_db, have_tables, save_song
from parsers.QQMusic_storage import init_db as song_init_db

from parsers.bili_storage import save_seasons
from parsers.bili_storage import init_db as season_init_db

class BaseMySQLPipeline:
    def __init__(self, cfg, flush_size=1000):
        self.cfg = cfg
        self.flush_size = flush_size
        self.conn = None
        self.buffer = []

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        return cls(
            cfg={
                "host":       s.get("MYSQL_HOST", "127.0.0.1"),
                "port":       s.getint("MYSQL_PORT", 3306),
                "user":       s.get("MYSQL_USER", "crawler"),
                "password":   s.get("MYSQL_PASSWORD", ""),
                "database":   s.get("MYSQL_DB", "Yqq"),
            },
            flush_size=s.get("MYSQL_FLUSH_SIZE", 1000),
        )

    def open_spider(self, spider):
        self.conn = connect(self.cfg)

    def process_item(self, item, spider):
        self.buffer.append(dict(item))
        if len(self.buffer) > self.flush_size:
            self.flush(spider)

        return item

    def close_spider(self, spider):
        try:
            self.flush(spider)
        finally:
            if self.conn:
                self.conn.close()

    def flush(self, spider):
        if not self.buffer:
            return
        batch, self.buffer = self.buffer, []
        try:
            self.conn.ping(reconnect=True)
            n = self.save(self.conn, batch)
        except (pymysql.Error, RuntimeError) as err:
            spider.logger.error("MySQL写入失败（本批 %d 条）：%s", len(batch), err)
            raise
        spider.logger.info("本批入库 %d 条", n)

    def save(self, conn, batch):
        raise NotImplementedError



class YqqMySQLPipeline(BaseMySQLPipeline):
    def open_spider(self, spider):
        super().open_spider(spider)
        song_init_db(self.conn)
        have_tables(self.conn)
        spider.logger.info("MySQL 就绪：%s:%s/%s", self.cfg["host"], self.cfg["port"], self.cfg["database"])

    def save(self, conn, batch):
        return save_song(conn, batch)

class BiliMySQLPipeline(BaseMySQLPipeline):
    def open_spider(self, spider):
        super().open_spider(spider)
        season_init_db(self.conn)

    def save(self, conn, batch):
        return save_seasons(conn, batch)