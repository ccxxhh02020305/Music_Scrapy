from __future__ import annotations
from pathlib import Path

import never_jscore
import threading

import json
import orjson


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

_SIGN_PATH = Path(__file__).resolve().parent / "tme_sign.js"
_engine: never_jscore.JSEngine | None = None
_init_lock = threading.Lock()

_MAX_CALLS = 100
_calls = 0
_call_lock = threading.Lock()



def init() -> None:
    global _engine
    if _engine is not None:
        return
    with _init_lock:
        # 重新检测：八个线程同时执行 init() 时，if _engine is not None: 会先执行，提前检测，然后七个等锁，需要在锁开之后重新检测一遍以防剩下七个根据刚刚 None 的结果新建引擎
        if _engine is None:
            with open(_SIGN_PATH, "r", encoding='utf-8') as f:
                content = f.read()
            _engine = never_jscore.JSEngine(_SHIM + "\n" + content, workers=6)
            _calls = 0

def _call(name, args):
    global _engine, _calls
    with _call_lock:
        init()
        try:
            return _engine.call(name, args)
        finally:
            _calls += 1
            if _calls >= _MAX_CALLS:
                _engine = None
                _calls = 0

def sign_encrypt(data):
    init()
    sign = _call("get_sign", [json.dumps(data)])
    en_data = _call("encrypt", [json.dumps(data)])
    if sign is None:
        raise RuntimeError("sign 返回空值")
    # print(sign)
    return sign, en_data

# def encrypt_budy(data):
#     init()
#     en_data = _engine.call("encrypt", [json.dumps(data)])
#     # print(en_data)
#     return en_data

def decrypt_resp(resp):
    init()
    de_resp = _call("decrypt", [list(resp.body)])  # resp.body 直接输出字节
    # de_resp = _engine.call("decrypt", [list(resp)])
    if not de_resp:
        raise RuntimeError("解密失败")
    # j = orjson.loads(de_resp)
    # if j["code"] == 2001:
    #     raise RuntimeError("sign 被拒绝，重新签名")
    # print(de_resp)
    return de_resp