from __future__ import annotations
from pathlib import Path

import threading
import orjson
import math


def singer_list_parse(response):
    singer_list = orjson.loads(response.body)
    singer_mid = [singer["singer_mid"] for singer in singer_list["req_1"]["data"]["singerlist"]]

    return singer_mid

def song_list_parse(response):
    resp = orjson.loads(response.body)
    songList = resp["req_5"]["data"]["songList"] or []
    song_num = resp["req_5"]["data"]["totalNum"] or 0
    max_page = math.ceil(song_num)
    recommend_singer_list = resp["req_7"]["data"]["singerlist"] or []

    items = []
    for song in songList:
        mid = song["songInfo"].get("mid")
        name = song["songInfo"].get("name")
        singer = [{"singer_mid": one_singer.get("mid"), "singer_name": one_singer.get("name")} for one_singer in song["songInfo"].get("singer")]
        album = song["songInfo"]["album"].get("name")
        time_public = song["songInfo"].get("time_public")
        is_pay = int(1 in song["songInfo"].get("pay", {}).values())  # 是否需要付费
        formats_keys = {"size_24aac", "size_48aac", "size_96aac", "size_192ogg", "size_192aac", "size_128mp3", "size_320mp3",
                        "size_ape", "size_flac", "size_96ogg", "size_dts", "size_dolby"}
        supported_formats = {k: v for k, v in song["songInfo"].get("file", {}).items()
                             if k in formats_keys and v is not None and v != 0}

        item =  {
            "song_mid": mid,
            "song_name": name,
            "singer": singer,
            "album": album,
            "time_public": time_public,
            "is_pay": is_pay,
            "supported_formats": supported_formats
        }
        items.append(item)

    return max_page, recommend_singer_list, items
