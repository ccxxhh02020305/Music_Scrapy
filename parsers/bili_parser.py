from __future__ import annotations

import json
from bs4 import BeautifulSoup

def parse_season(resp_html: requests.Response) -> dict:
    soup = BeautifulSoup(resp_html.text, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    data = json.loads(tag.string)
    info = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]

    new_ep = info.get("new_ep") or {}
    payment = info.get("payment") or {}
    publish = info.get("publish") or {}
    rating = info.get("rating") or {}
    stat = info.get("stat") or {}
    up_info = info.get("up_info") or {}

    return {
        "season_id": info.get("season_id"),
        "title": info.get("title", ""),
        "staff": info.get("staff", "").split("\n"),
        "cv": info.get("actors", "").split("\n"),
        "introduction": info.get("evaluate", ""),
        "state": new_ep.get("desc", ""),
        "vip": payment.get("vip_promotion", ""),
        "release_date": publish.get("release_date", ""),
        "score": rating.get("score", ""),
        "view_persons": stat.get("views", ""),
        "follow": stat.get("follow_text", ""),
        "styles": info.get("styles", ""),
        "up_name": up_info.get("uname", ""),
        "share_url": info.get("share_url", "")
    }

def parse_recommend_urls(response:json) -> list[str]:
    season = response["data"]["season"]
    new_url = []
    for i in range(len(season)):
        new_url.append(season[i]["url"])

    return new_url