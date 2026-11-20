import hashlib
import json

from scrapy_redis.dupefilter import RFPDupeFilter
from w3lib.url import url_query_cleaner


class MetaAwareDupeFilter(RFPDupeFilter):
    META_KEYS = ("sign", "page", "begin", "singerMid")

    def request_fingerprint(self, request):
        payload = {
            "method": request.method,
            "url": url_query_cleaner(request.url, ("from_spmid", "spmid", "vd_source", "share_source", "trackid", "spm_id_from",
                              "share_medium", "bbid", "ts", "from_source"), remove=True),
            "meta": {k: request.meta.get(k) for k in self.META_KEYS},
        }

        return hashlib.sha1(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()