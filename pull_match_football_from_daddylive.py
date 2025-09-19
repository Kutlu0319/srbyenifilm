# -*- coding: utf-8 -*-
"""
يسحب فقط قنوات محددة من مصدر daddylive (M3U)، ويحدث ملف generalsports.m3u بصيغة نظيفة.
"""

import os
import re
import sys
import base64
from typing import List, Tuple, Dict, Optional
import requests

# ---------- إعدادات ----------

SOURCE_URL = os.getenv(
    "SOURCE_URL",
    "https://raw.githubusercontent.com/DisabledAbel/daddylivehd-m3u/f582ae100c91adf8c8db905a8f97beb42f369a0b/daddylive-events.m3u8"
)

DEST_RAW_URL = os.getenv(
    "DEST_RAW_URL",
    "https://raw.githubusercontent.com/a7shk1/m3u-broadcast/main/generalsports.m3u"
)

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO    = os.getenv("GITHUB_REPO", "a7shk1/m3u-broadcast")
GITHUB_BRANCH  = os.getenv("GITHUB_BRANCH", "main")
DEST_REPO_PATH = os.getenv("DEST_REPO_PATH", "generalsports.m3u")
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE", "chore: update sports channels from daddylive")

OUTPUT_LOCAL_PATH = os.getenv("OUTPUT_LOCAL_PATH", "./out/generalsports.m3u")

TIMEOUT = 25
VERIFY_SSL = True

# ---------- القنوات المطلوبة وأنماط المطابقة ----------

WANTED_CHANNELS = [
    "beIN SPORTS 1 Turkey",
    "beIN SPORTS 2 Turkey",
    "beIN SPORTS 3 Turkey",
    "beIN SPORTS 4 Turkey",
    "Eleven Sports 1 Portugal",
    "Eleven Sports 2 Portugal",
    "Eleven Sports 3 Portugal",
    "Eleven Sports 4 Portugal",
    "Eleven Sports 5 Portugal",
    "Sport TV1 Portugal",
    "Sport TV2 Portugal",
    "Sport TV3 Portugal",
    "Sport TV4 Portugal",
    "Sport TV5 Portugal",
    "Sport TV6 Portugal",
    "beIN SPORTS 1 France",
    "beIN SPORTS 2 France",
    "beIN SPORTS 3 France",
    "beIN Sports MAX 4 France",
    "beIN Sports MAX 5 France",
    "beIN Sports MAX 6 France",
    "beIN Sports MAX 7 France",
    "beIN Sports MAX 8 France",
    "beIN Sports MAX 9 France",
    "beIN Sports MAX 10 France",
    "MATCH! FOOTBALL 1 RUSSIA",
    "MATCH! FOOTBALL 2 RUSSIA",
    "MATCH! FOOTBALL 3 RUSSIA",
    "Sport Klub Serbia",
    "Sport Klub 1 Serbia",
    "Sport Klub 2 Serbia",
    "Sport Klub 3 Serbia",
    "Sport Klub 4 Serbia",
    "TNT Sports 1 UK",
    "TNT Sports 2 UK",
    "TNT Sports 3 UK",
    "TNT Sports 4 UK",
]

ALIASES: Dict[str, List[re.Pattern]] = {
    "beIN SPORTS 1 Turkey": [
        re.compile(r"bein\s*sports\s*1\s*turkey", re.I),
    ],
    "beIN SPORTS 2 Turkey": [
        re.compile(r"bein\s*sports\s*2\s*turkey", re.I),
    ],
    "beIN SPORTS 3 Turkey": [
        re.compile(r"bein\s*sports\s*3\s*turkey", re.I),
    ],
    "beIN SPORTS 4 Turkey": [
        re.compile(r"bein\s*sports\s*4\s*turkey", re.I),
    ],
    "Eleven Sports 1 Portugal": [
        re.compile(r"eleven\s*sports\s*1", re.I),
    ],
    "Eleven Sports 2 Portugal": [
        re.compile(r"eleven\s*sports\s*2", re.I),
    ],
    "Eleven Sports 3 Portugal": [
        re.compile(r"eleven\s*sports\s*3", re.I),
    ],
    "Eleven Sports 4 Portugal": [
        re.compile(r"eleven\s*sports\s*4", re.I),
    ],
    "Eleven Sports 5 Portugal": [
        re.compile(r"eleven\s*sports\s*5", re.I),
    ],
    "Sport TV1 Portugal": [
        re.compile(r"sport\s*tv\s*1", re.I),
    ],
    "Sport TV2 Portugal": [
        re.compile(r"sport\s*tv\s*2", re.I),
    ],
    "Sport TV3 Portugal": [
        re.compile(r"sport\s*tv\s*3", re.I),
    ],
    "Sport TV4 Portugal": [
        re.compile(r"sport\s*tv\s*4", re.I),
    ],
    "Sport TV5 Portugal": [
        re.compile(r"sport\s*tv\s*5", re.I),
    ],
    "Sport TV6 Portugal": [
        re.compile(r"sport\s*tv\s*6", re.I),
    ],
    "beIN SPORTS 1 France": [
        re.compile(r"bein\s*sports\s*1\s*france", re.I),
    ],
    "beIN SPORTS 2 France": [
        re.compile(r"bein\s*sports\s*2\s*france", re.I),
    ],
    "beIN SPORTS 3 France": [
        re.compile(r"bein\s*sports\s*3\s*france", re.I),
    ],
    "beIN Sports MAX 4 France": [
        re.compile(r"bein\s*sports\s*max\s*4", re.I),
    ],
    "beIN Sports MAX 5 France": [
        re.compile(r"bein\s*sports\s*max\s*5", re.I),
    ],
    "beIN Sports MAX 6 France": [
        re.compile(r"bein\s*sports\s*max\s*6", re.I),
    ],
    "beIN Sports MAX 7 France": [
        re.compile(r"bein\s*sports\s*max\s*7", re.I),
    ],
    "beIN Sports MAX 8 France": [
        re.compile(r"bein\s*sports\s*max\s*8", re.I),
    ],
    "beIN Sports MAX 9 France": [
        re.compile(r"bein\s*sports\s*max\s*9", re.I),
    ],
    "beIN Sports MAX 10 France": [
        re.compile(r"bein\s*sports\s*max\s*10", re.I),
    ],
    "MATCH! FOOTBALL 1 RUSSIA": [
        re.compile(r"match!?\.?\s*football\s*1\s*russia", re.I),
        re.compile(r"match!?\.?\s*futbol\s*1", re.I),
    ],
    "MATCH! FOOTBALL 2 RUSSIA": [
        re.compile(r"match!?\.?\s*football\s*2\s*russia", re.I),
        re.compile(r"match!?\.?\s*futbol\s*2", re.I),
    ],
    "MATCH! FOOTBALL 3 RUSSIA": [
        re.compile(r"match!?\.?\s*football\s*3\s*russia", re.I),
        re.compile(r"match!?\.?\s*futbol\s*3", re.I),
    ],
    "Sport Klub Serbia": [
        re.compile(r"sport\s*klub\s*serbia", re.I),
    ],
    "Sport Klub 1 Serbia": [
        re.compile(r"sport\s*klub\s*1", re.I),
    ],
    "Sport Klub 2 Serbia": [
        re.compile(r"sport\s*klub\s*2", re.I),
    ],
    "Sport Klub 3 Serbia": [
        re.compile(r"sport\s*klub\s*3", re.I),
    ],
    "Sport Klub 4 Serbia": [
        re.compile(r"sport\s*klub\s*4", re.I),
    ],
    "TNT Sports 1 UK": [
        re.compile(r"tnt\s*sports\s*1", re.I),
    ],
    "TNT Sports 2 UK": [
        re.compile(r"tnt\s*sports\s*2", re.I),
    ],
    "TNT Sports 3 UK": [
        re.compile(r"tnt\s*sports\s*3", re.I),
    ],
    "TNT Sports 4 UK": [
        re.compile(r"tnt\s*sports\s*4", re.I),
    ],
}

# ---------- وظائف مساعدة ----------

def fetch_text(url: str) -> str:
    r = requests.get(url, timeout=TIMEOUT, verify=VERIFY_SSL)
    r.raise_for_status()
    return r.text

def parse_m3u_pairs(m3u_text: str) -> List[Tuple[str, Optional[str]]]:
    lines = [ln.rstrip("\n") for ln in m3u_text.splitlines()]
    out: List[Tuple[str, Optional[str]]] = []
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("#EXTINF"):
            url = None
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt and not
