from __future__ import annotations

import json
from bs4 import BeautifulSoup
import requests

url = "https://y.qq.com/n/ryqq_v2/toplist/62"
resp = requests.get(url)
print(resp.json())