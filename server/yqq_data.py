import os

YQQ_G_TK = int(os.environ.get("YQQ_G_TK", "0"))

comm = {"cv": 4747474, "ct": 24, "format": "json", "inCharset": "utf-8", "outCharset": "utf-8",
        "notice": 0, "platform": "yqq.json", "needNewCode": 1, "uin": 0, "g_tk_new_20200303": YQQ_G_TK, "g_tk": YQQ_G_TK}

def singer_data(page):
    sin = page * 80
    cur_page = page + 1
    data_singer = {"comm": comm,
                   "req_1": {"module": "music.musichallSinger.SingerList", "method": "GetSingerListIndex",
                             "param": {"area": -100, "sex": -100, "genre": -100, "index": -100, "sin": sin, "cur_page": cur_page}}}

    return data_singer


def song_data(singerMid, begin: int):
    order = 1   # !!!!!!!!!!!!!!!!!!!!改：order 为请求方式，begin 为行偏移（100，200，300）！！！！！！！！！！！！！！！！！！！！！！
    data_song = {
        "comm": comm,
        "req_2": {"method": "GetSingerDetail",
                  "param": {"singer_mids": [singerMid], "ex_singer": 1, "wiki_singer": 1, "group_singer": 0, "pic": 1, "photos": 0}, "module": "music.musichallSinger.SingerInfoInter"},
        "req_5": {"method": "GetSingerSongList",
                  "param": {"singerMid": singerMid, "order": order, "begin": begin, "num": 100}, "module": "musichall.song_list_server"},
        "req_7": {"method": "GetSimilarSingerList",
                  "param": {"singerMid": singerMid, "num": 5}, "module": "music.SimilarSingerSvr"},  # 相似歌手
        }

    return data_song

def data2middlewares(request, singerMid=None):
    page = request.meta.get("page")
    begin = request.meta.get("begin")
    sign = request.meta["sign"]
    if sign == "singer_data":
        return singer_data(page)
    elif sign == "song_data":
        return song_data(singerMid, begin)
    else:
        raise RuntimeError("不合法请求参数")
