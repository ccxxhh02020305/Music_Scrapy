from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pymysql

# DDL
SEASON_DDL = """
    CREATE TABLE IF NOT EXISTS season (
        season_id         BIGINT UNSIGNED       NOT NULL,    -- 自然键，item["season_id"]
        title             VARCHAR(255)          NOT NULL DEFAULT '',
        staff             JSON                  NULL,   -- 多值 ->  JSON
        cv                JSON                  NULL,
        styles            JSON                  NULL,
        introduction      MEDIUMTEXT            NULL,
        state             VARCHAR(100)          NULL,
        vip               JSON                  NULL,
        release_date      DATETIME              NULL,
        score             DECIMAL(3,1) UNSIGNED NULL,
        view_persons      BIGINT UNSIGNED       NULL,
        follow            VARCHAR(50)           NULL,
        up_name           VARCHAR(100)          NULL,
        share_url         VARCHAR(512)          NULL,
        first_seen_at     DATETIME              NOT NULL,
        last_seen_at      DATETIME              NOT NULL,
        PRIMARY KEY (season_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""

SNAPSHOT_DDL = """
    CREATE TABLE IF NOT EXISTS season_snapshot (    -- 追加快照表：记录某次爬取那一刻的各项指标
        season_id         BIGINT UNSIGNED          NOT NULL,
        captured_at       DATETIME                 NOT NULL,
        view_persons      BIGINT UNSIGNED          NULL,
        follow            VARCHAR(50)              NULL,
        score             DECIMAL(3,1) UNSIGNED    NULL,
        state             VARCHAR(100)             NULL,
        PRIMARY KEY (season_id, captured_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
"""

# SQL
SEASON_UPSERT = """
    INSERT INTO season 
        (season_id, title, staff, cv, styles, introduction, state, vip, release_date, score, view_persons, follow, up_name,
         share_url, first_seen_at, last_seen_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new
    ON DUPLICATE KEY UPDATE     -- 冲突时更新
        title        = new.title,
        staff        = new.staff,
        cv           = new.cv,
        styles       = new.styles,
        introduction = new.introduction,
        state        = new.state,
        vip          = new.vip,
        release_date = new.release_date,
        score        = new.score,
        view_persons = new.view_persons,
        follow       = new.follow,
        up_name      = new.up_name,
        share_url    = new.share_url,
        last_seen_at = new.last_seen_at
        -- first_seen_at 不更新，保持首次见到的时间
"""
# 快照是追加型：同一复合主键重复写就是同一时刻，直接忽略
SNAPSHOT_INSERT = """
    INSERT IGNORE INTO season_snapshot   -- 冲突时什么都不做
        (season_id, captured_at, view_persons, follow, score, state)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

# 空值处理
def as_json(value):
    if value is None or value == []:
        return None
    return json.dumps(value, ensure_ascii=False)

def as_text(value):
    if value is None or value == "":
        return None
    text = value  if isinstance(value, str) else str(value)
    return text

def as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def as_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

# 连接与幂等
def connect(cfg):
    return pymysql.connect(
        host=cfg['host'], port=int(cfg.get('port', '3306')),
        user=cfg['user'], passwd=cfg['password'],
        database=cfg['database'],
        charset="utf8mb4",
        autocommit=False,   # 关闭自动提交，按设计写入
        connect_timeout=5, read_timeout=30, write_timeout=30,
    )

def init_db(conn):   # 建表
    with conn.cursor() as cur:  # 创建游标，退出时自动关闭
        cur.execute(SEASON_DDL)
        cur.execute(SNAPSHOT_DDL)
    conn.commit()

def have_tables(conn):
    """校验爬虫需要的表存在。只需要 SELECT 权限。"""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM season LIMIT 1")
        cur.execute("SELECT 1 FROM season_snapshot LIMIT 1")


def season_row(rec, now):
    """item(dict) -> 一行，此为 item 键名到列名的唯一映射点"""
    return (
        as_int(rec.get("season_id")),  # rec.get("season_id")：键不存在返回None
        as_text(rec.get("title")),
        as_json(rec.get("staff")),
        as_json(rec.get("cv")),
        as_json(rec.get("styles")),
        as_text(rec.get("introduction")),
        as_text(rec.get("state")),
        as_json(rec.get("vip")),
        as_text(rec.get("release_date")),
        as_decimal(rec.get("score")),
        as_int(rec.get("view_persons")),
        as_text(rec.get("follow")),
        as_text(rec.get("up_name")),
        as_text(rec.get("share_url")),
        now, now
    )

def save_seasons(conn, records, now=None, with_snapshot=True):
    """一个事务完成主表与追加表的写入与更新，返回写入的数量"""
    now = now or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = [r for r in records if r.get("season_id")]   # 列表推导式，筛掉没有主键的行
    if not records:
        return 0

    with conn.cursor() as cur:
        for rec in records:
            row = season_row(rec, now)
            try:
                cur.execute(SEASON_UPSERT, row)
            except pymysql.Error as err:
                # 带上seaso_id再抛
                raise RuntimeError(f"写入 season_id={row[0]} 失败：{err}") from err

        if with_snapshot:
            for rec in records:
                cur.execute(SNAPSHOT_INSERT, (
                    as_int(rec.get("season_id")),
                    now,
                    as_int(rec.get("view_persons")),
                    as_text(rec.get("follow")),
                    as_decimal(rec.get("score")),
                    as_text(rec.get("state")),
                ))

    conn.commit()
    return len(records)

def stats(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), MAX(last_seen_at) FROM season")
        rows, latest = cur.fetchone()  # fetchone：取一行； fetchall：取所有行
        cur.execute("SELECT COUNT(*) FROM season_snapshot")
        snapshots = cur.fetchone()[0]

    return {"seasons": rows, "latest_seen": latest, "snapshots": snapshots}