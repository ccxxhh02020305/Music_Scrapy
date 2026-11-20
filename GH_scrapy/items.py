import scrapy


class GhYqqItem(scrapy.Item):
    song_mid = scrapy.Field()
    song_name = scrapy.Field()
    singer = scrapy.Field()
    album = scrapy.Field()
    time_public = scrapy.Field()
    is_pay = scrapy.Field()
    supported_formats = scrapy.Field()

class BiliItem(scrapy.Item):
    season_id = scrapy.Field()
    title = scrapy.Field()
    staff = scrapy.Field()
    cv = scrapy.Field()
    introduction = scrapy.Field()
    state = scrapy.Field()
    vip = scrapy.Field()
    release_date = scrapy.Field()
    score = scrapy.Field()
    view_persons = scrapy.Field()
    follow = scrapy.Field()
    styles = scrapy.Field()
    up_name = scrapy.Field()
    share_url = scrapy.Field()

