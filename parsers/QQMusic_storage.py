from __future__ import annotations

import logging

import pymysql
import json

import datetime

logger = logging.getLogger(__name__)

SONG_DDL = """
    CREATE TABLE IF NOT EXISTS song (
        song_mid              VARCHAR(32)         NOT NULL,
        song_name             VARCHAR(256)        NOT NULL,
        singer                JSON                NOT NULL,
        album                 VARCHAR(512)        NOT NULL,
        time_public           DATETIME            NULL, 
        is_pay                TINYINT             NOT NULL DEFAULT 0,
        supported_formats     JSON                NULL,
        first_seen_at         DATETIME            NOT NULL,
        last_seen_at          DATETIME            NOT NULL,
        PRIMARY KEY (song_mid)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """

SONG_UPSERT = """
    INSERT INTO song
        (song_mid, song_name, singer, album, time_public, is_pay, supported_formats, first_seen_at, last_seen_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) AS NEW
    ON DUPLICATE KEY UPDATE 
        song_mid           = new.song_mid,
        song_name          = new.song_name,
        singer             = new.singer,
        album              = new.album,
        time_public        = new.time_public,
        is_pay             = new.is_pay,
        supported_formats  = new.supported_formats,
        last_seen_at       = new.last_seen_at
"""

def as_json(value):
    return json.dumps(value, ensure_ascii=False)

def connect(cfg):
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"],
        user=cfg["user"], password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=5, read_timeout=30, write_timeout=30,
    )

def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(SONG_DDL)
    conn.commit()

def have_tables(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM song LIMIT 1")

def as_text(value):
    """NOT NULL 的字符串列：None / 空串统一落成 ""，避免 1048。"""
    if value is None:
        return ""
    return str(value).strip()

def as_datetime(value):  # DATETIME 拒绝 "", 转换为 None 入库
    """DATETIME 列：空串、'0000-00-00'、非法格式一律落成 NULL，避免 1292。"""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.startswith("0000-00-00"):
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None

def song_row(rec, now):
    return (
        rec.get("song_mid"),
        as_text(rec.get("song_name")),
        as_json(rec.get("singer")),
        as_text(rec.get("album")),
        as_datetime(rec.get("time_public")),
        rec.get("is_pay"),
        as_json(rec.get("supported_formats")),
        now,
        now
    )

def save_song(conn, records, now=None):
    now = now or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not records:
        return 0

    ok = 0
    failures = []
    with conn.cursor() as cur:
        for rec in records:
            row = song_row(rec, now)
            try:
                cur.execute(SONG_UPSERT, row)
                ok += 1
            except pymysql.Error as err:
                # 单条失败不拖累整批：MySQL 语句级回滚，事务里已有的成功语句仍然有效
                failures.append((row[0], str(err)))

    conn.commit()

    if failures and ok == 0:
        raise RuntimeError(f"本批 {len(failures)} 条全部失败，有：{failures[:3]}")
    if failures:
        # 部分成功：数据已提交，只记录失败明细，交给上层日志汇总
        logger.warning("song 本批成功 %d 条、失败 %d 条, 有 %s", ok, len(failures), failures[:3])
    return ok

# def stats(conn):
#     with conn.cursor() as cur:
#         cur.execute("SELECT COUNT(*), MAX(last_seen_at) FROM song")
