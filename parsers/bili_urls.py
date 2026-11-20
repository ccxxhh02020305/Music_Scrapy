RECOMMEND_API = "https://api.bilibili.com/pgc/season/web/related/recommend"

def recommend_api(season_id) -> tuple[str, dict]:
    return RECOMMEND_API, {
        "x-bili-locale-json": "{'c_locale':{'language':'zh-Hans'},'always_translate':false}",
        "x-bili-device-req-json": "{'platform':'web','device':'pc','mobi_app':web_cn}",
        "season_id": season_id
    }