from __future__ import annotations
from pathlib import Path

import never_jscore
import threading
import json
import time
import requests
import base64
import orjson

from bs4 import BeautifulSoup


def singer_list_parse(response):
    singer_list = orjson.loads(response.body)

# data = {"comm":{"cv":4747474,"ct":24,"format":"json","inCharset":"utf-8","outCharset":"utf-8","notice":0,"platform":"yqq.json","needNewCode":1,"uin":2730137205,"g_tk_new_20200303":927559093,"g_tk":927559093},
#         "req_1":{"module":"music.musicsearch.HotkeyService","method":"GetHotkeyForQQMusicMobile","param":{"searchid":"19307312594925880","remoteplace":"txt.yqq.top","from":"yqqweb"}},
#         "req_2":{"module":"music.globalComment.CommentRead","method":"GetNewCommentList","param":{"BizType":4,"BizId":"4","LastCommentSeqNo":"","PageSize":25,"PageNum":0,"FromCommentId":"","WithHot":1,"PicEnable":1,"LastTotal":0,"LastTotalVer":"0"}},
#         "req_3":{"module":"music.globalComment.CommentRead","method":"GetHotCommentList","param":{"BizType":4,"BizId":"4","LastCommentSeqNo":"","PageSize":15,"PageNum":0,"HotType":2,"WithAirborne":1,"PicEnable":1}},
#         "req_4":{"module":"music.globalComment.CommentAsset","method":"GetCmBgCard","param":{}},
#         "req_5":{"module":"yqq.WhiteListServer","method":"Pass","param":{}},
#         "req_6":{"module":"music.paycenterapi.LoginStateVerificationApi","method":"GetChargeAccount","param":{"appid":"mlive"}},
#         "req_7":{"module":"userInfo.VipQueryServer","method":"SRFVipQuery_V2","param":{"uin_list":["2730137205"]}},
#         "req_8":{"module":"userInfo.BaseUserInfoServer","method":"get_user_baseinfo_v2","param":{"vec_uin":["2730137205"]}},
#         "req_9":{"module":"music.lvz.VipIconUiShowSvr","method":"GetVipIconUiV2","param":{"PID":3}},
#         "req_10":{"module":"MessageCenter.MessageCenterServer","method":"GetMessage","param":{"uin":"2730137205","red_dot":[{"msg_type":1}]}},
#         "req_11":{"module":"GlobalComment.GlobalCommentMessageReadServer","method":"GetMessage","param":{"uin":"2730137205","page_num":0,"page_size":1,"last_msg_id":"","type":0}}
# }


# 一个页面会发三次请求
data1 = {"comm":{"cv":4747474,"ct":24,"format":"json","inCharset":"utf-8","outCharset":"utf-8","notice":0,"platform":"yqq.json","needNewCode":1,"uin":0,"g_tk_new_20200303":927559093,"g_tk":927559093},
        "req_1":{"module":"music.musicsearch.HotkeyService","method":"GetHotkeyForQQMusicMobile","param":{"searchid":"28376814568304979","remoteplace":"txt.yqq.top","from":"yqqweb"}},     # 热搜词
        "req_2":{"module":"music.paycenterapi.LoginStateVerificationApi","method":"GetChargeAccount","param":{"appid":"mlive"}},
        "req_3":{"module":"musicToplist.ToplistInfoServer","method":"GetAll","param":{}}}   # 排行榜
data2 = {"comm":{"cv":4747474,"ct":24,"format":"json","inCharset":"utf-8","outCharset":"utf-8","notice":0,"platform":"yqq.json","needNewCode":1,"uin":0,"g_tk_new_20200303":927559093,"g_tk":927559093},
        "req_1":{"module":"musicToplist.ToplistInfoServer","method":"GetDetail","param":{"topid":4,"offset":0,"num":100,"period":""}}} # topid：榜单id；num：返回该榜歌曲数量
# data3 = {"comm":{"cv":4747474,"ct":24,"format":"json","inCharset":"utf-8","outCharset":"utf-8","notice":0,"platform":"yqq.json","needNewCode":1,"uin":0,"g_tk_new_20200303":927559093,"g_tk":927559093},
#         "req_1":{"module":"music.globalComment.CommentRead","method":"GetNewCommentList","param":{"BizType":4,"BizId":"4","LastCommentSeqNo":"","PageSize":25,"PageNum":0,"FromCommentId":"","WithHot":1,"PicEnable":1,"LastTotal":0,"LastTotalVer":"0"}},
#         "req_2":{"module":"music.globalComment.CommentRead","method":"GetHotCommentList","param":{"BizType":4,"BizId":"4","LastCommentSeqNo":"","PageSize":15,"PageNum":0,"HotType":2,"WithAirborne":1,"PicEnable":1}},
#         "req_3":{"module":"music.globalComment.CommentAsset","method":"GetCmBgCard","param":{}}}


_SHIM = r"""
globalThis.window = globalThis;
globalThis.self = globalThis;
globalThis.navigator = {
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  platform: "Win32", language: "zh-CN", languages: ["zh-CN", "zh"],
  hardwareConcurrency: 8, deviceMemory: 8, webdriver: undefined, plugins: [],
};
globalThis.location = {
  href: "https://y.qq.com/", origin: "https://y.qq.com", protocol: "https:",
  host: "y.qq.com", hostname: "y.qq.com", pathname: "/", search: "", hash: "",
};
globalThis.document = {
  createElement: () => ({ style: {}, getContext: () => null, appendChild() {}, setAttribute() {} }),
  documentElement: { style: {} }, cookie: "", referrer: "https://y.qq.com/",
  addEventListener() {}, getElementsByTagName: () => [], querySelector: () => null,
};
globalThis.screen = {width: 1920, height: 1080, availWidth: 1920, availHeight: 1040,
                     colorDepth: 24, pixelDepth: 24};
globalThis.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
globalThis.requestAnimationFrame = (cb) => setTimeout(() => cb(Date.now()), 0);
"""

_SIGN_PATH = Path(__file__).resolve().parent.parent / "parsers" / "tme_sign.js"
_engine: never_jscore.JSEngine | None = None
_init_lock = threading.Lock()



def init() -> None:
    global _engine
    if _engine is not None:
        return
    with _init_lock:
        # 重新检测：八个线程同时执行 init() 时，if _engine is not None: 会先执行，提前检测，然后七个等锁，需要在锁开之后重新检测一遍以防剩下七个根据刚刚 None 的结果新建引擎
        if _engine is None:
            with open(_SIGN_PATH, "r", encoding='utf-8') as f:
                content = f.read()
            _engine = never_jscore.JSEngine(_SHIM + "\n" + content, workers=8)


def get_sign(data):
    init()
    sign = _engine.call("get_sign", [json.dumps(data)])
    if sign is None:
        raise RuntimeError("sign 返回空值")
    # print(sign)
    return sign

def encrypt_budy(data):
    init()
    en_data = _engine.call("encrypt", [json.dumps(data)])
    # print(en_data)
    return en_data

def response(sign,en_data) -> dict:
    url = "https://u6.y.qq.com/cgi-bin/musics.fcg"
    params = {
        "_": str(int(time.time() * 1000)),
        "encoding": "ag-1",
        "sign": sign
    }
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
        "referer": "https://y.qq.com/",
        "accept": "application/octet-stream",
        "cookie": "pgv_pvid=639648080; fqm_pvqid=1e1b2713-dd16-4f41-83e5-0d1d69cd7d27; fqm_sessionid=ea966420-3d6e-419c-aa2c-40932cb18040; pgv_info=ssid=s5171476354; ts_last=y.qq.com/; ts_uid=7202732808"
    }
    resp = requests.post(url, params=params, headers=headers, data=en_data)
    de_resp = decrypt_resp(resp)
    print(de_resp)
    return de_resp

def decrypt_resp(resp):
    init()
    de_resp = _engine.call("decrypt", [list(resp.content)])
    # de_resp = _engine.call("decrypt", [list(resp)])
    if not de_resp:
        raise RuntimeError("解密失败")
    j = orjson.loads(de_resp)
    if j["code"] == 2001:
        raise RuntimeError("sign 被拒绝，重新签名")
    # print(de_resp)
    return j

def singer_data() -> dict:
    all_data = []
    for i in range(1, 11):
        cur_page = i + 1
        sin = i * 80
        data_singer = {"comm": {"cv": 4747474, "ct": 24, "format": "json", "inCharset": "utf-8", "outCharset": "utf-8",
                          "notice": 0, "platform": "yqq.json", "needNewCode": 1, "uin": 0, "g_tk_new_20200303": 927559093, "g_tk": 927559093},
                 "req_1": {"module": "music.musichallSinger.SingerList", "method": "GetSingerListIndex",
                           "param": {"area": -100, "sex": -100, "genre": -100, "index": -100, "sin": sin, "cur_page": cur_page}}}

        all_data.append(data_singer)
    return all_data


def song_data(singerMid):
    singerMid = "001fNHEf1SFEFN"
    begin = 700
    order = 1
    data_song = {"comm":{"cv":4747474,"ct":24,"format":"json","inCharset":"utf-8","outCharset":"utf-8","notice":0,"platform":"yqq.json","needNewCode":1,"uin":0,"g_tk_new_20200303":927559093,"g_tk":927559093},
                 # "req_1":{"module":"music.musicsearch.HotkeyService","method":"GetHotkeyForQQMusicMobile","param":{"searchid":"21173484477149591","remoteplace":"txt.yqq.top","from":"yqqweb"}},
                 "req_2":{"method":"GetSingerDetail","param":{"singer_mids":[singerMid],"ex_singer":1,"wiki_singer":1,"group_singer":0,"pic":1,"photos":0},"module":"music.musichallSinger.SingerInfoInter"},
                 # "req_3":{"method":"GetAlbumList","param":{"singerMid":"001fNHEf1SFEFN","order":0,"begin":0,"num":5,"songNumTag":0,"singerID":0},"module":"music.musichallAlbum.AlbumListServer"},
                 # "req_4":{"method":"GetSingerMvList","param":{"singermid":"001fNHEf1SFEFN","count":20,"start":0,"order":1},"module":"MvService.MvInfoProServer"},
                 "req_5":{"method":"GetSingerSongList","param":{"singerMid":singerMid,"order":order,"begin":begin,"num":100},"module":"musichall.song_list_server"},
                 # "req_6":{"method":"cgi_qry_concern_num","module":"Concern.ConcernSystemServer","param":{"vec_userinfo":[{"userid":"001fNHEf1SFEFN","usertype":1}]}}, # 关注数
                 "req_7":{"method":"GetSimilarSingerList","param":{"singerMid":singerMid,"num":5},"module":"music.SimilarSingerSvr"}, # 相似歌手
                 # "req_8":{"module":"music.paycenterapi.LoginStateVerificationApi","method":"GetChargeAccount","param":{"appid":"mlive"}}
                 }

    return data_song



def start_request() -> list:
    start_datas = singer_data()
    all_singer_mid = []
    for data in start_datas:
        start_sign = get_sign(data)
        start_en_data = encrypt_budy(data)
        start_resp = response(start_sign, start_en_data)
        singer_mid = [singer["singer_mid"] for singer in start_resp["req_1"]["data"]["singerlist"]]
        all_singer_mid.append(singer_mid)

    print(all_singer_mid)
    return all_singer_mid


def get_song_num(all_singer_mid):
    pass

def parse_songInfo(songList: list) -> dict:
    for song in songList:
        mid = song["songInfo"].get("mid")
        name = song["songInfo"].get("name")
        singer = [one_singer.get("name") for one_singer in song["songInfo"].get("singer")]
        album = song["songInfo"]["album"].get("name")
        time_public = song["songInfo"].get("time_public")
        is_pay = int(1 in song["songInfo"].get("pay", {}).values())  # 是否需要付费
        supported_formats = {k: v  for k, v in song["songInfo"].get("file", {}).items() if v is not None and v != 0}

    return {
        "song_mid": mid,
        "song_name": name,
        "singer": singer,
        "album": album,
        "time_public": time_public,
        "is_pay": is_pay,
        "supported_formats": supported_formats
    }


if __name__ == "__main__":
    # sign = get_sign(data2)
    # en_data = encrypt_budy(data2)
    # resp = response(sign, en_data)

    all_singer_mid = start_request()



    data_song = song_data("001fNHEf1SFEFN")
    sign = get_sign(data_song)
    en_data = encrypt_budy(data_song)
    resp = response(sign, en_data)
    songList = resp["req_5"]["data"]["songList"]
    song_num = resp["req_5"]["data"]["totalNum"]
    all_recommend_mid = [recommend_singer["singerMid"] for recommend_singer in resp["req_7"]["data"]["singerlist"]]

    print(len(resp["req_5"]["data"]["songList"]))


    # with open(r"C:\Users\27301\Desktop\u6.y.qq.com-20261102T234535-130.txt", "rb") as f:
    #     content = f.read()
    #     text = decrypt_resp(content)

