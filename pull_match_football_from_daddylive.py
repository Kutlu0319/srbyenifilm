# scripts/pull_match_football_from_daddylive.py
# -*- coding: utf-8 -*-
"""
Güncellenmiş versiyon: Çoklu kanal desteği.
Çeker:
- beIN SPORTS Turkey, France, MAX
- Eleven Sports Portugal
- Sport TV Portugal
- Sport Klub Serbia
- TNT Sports UK
- MATCH! FOOTBALL Russia

Kaynak: daddylive M3U.
"""

import os
import re
import sys
import base64
from typing import List, Tuple, Dict, Optional
import requests

SOURCE_URL = os.getenv(
    "SOURCE_URL",
    "https://raw.githubusercontent.com/DisabledAbel/daddylivehd-m3u/f582ae100c91adf8c8db905a8f97beb42f369a0b/daddylive-events.m3u8"
)

DEST_RAW_URL = os.getenv(
    "DEST_RAW_URL",
    "https://raw.githubusercontent.com/a7shk1/m3u-broadcast/refs/heads/main/generalsports.m3u"
)

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO    = os.getenv("GITHUB_REPO", "a7shk1/m3u-broadcast")
GITHUB_BRANCH  = os.getenv("GITHUB_BRANCH", "main")
DEST_REPO_PATH = os.getenv("DEST_REPO_PATH", "generalsports.m3u")
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE", "chore: update sports channels from daddylive")

OUTPUT_LOCAL_PATH = os.getenv("OUTPUT_LOCAL_PATH", "./out/generalsports.m3u")

TIMEOUT = 25
VERIFY_SSL = True

# ---------- KANALLAR ----------

WANTED_CHANNELS = [
    "beIN SPORTS 1 Turkey", "beIN SPORTS 2 Turkey", "beIN SPORTS 3 Turkey", "beIN SPORTS 4 Turkey",
    "Eleven Sports 1 Portugal", "Eleven Sports 2 Portugal", "Eleven Sports 3 Portugal",
    "Eleven Sports 4 Portugal", "Eleven Sports 5 Portugal",
    "Sport TV1 Portugal", "Sport TV2 Portugal", "Sport TV3 Portugal",
    "Sport TV4 Portugal", "Sport TV5 Portugal", "Sport TV6 Portugal",
    "beIN SPORTS 1 France", "beIN SPORTS 2 France", "beIN SPORTS 3 France",
    "beIN Sports MAX 4 France", "beIN Sports MAX 5 France", "beIN Sports MAX 6 France",
    "beIN Sports MAX 7 France", "beIN Sports MAX 8 France", "beIN Sports MAX 9 France",
    "beIN Sports MAX 10 France",
    "MATCH! FOOTBALL 1 RUSSIA", "MATCH! FOOTBALL 2 RUSSIA", "MATCH! FOOTBALL 3 RUSSIA",
    "Sport Klub Serbia", "Sport Klub 1 Serbia", "Sport Klub 2 Serbia",
    "Sport Klub 3 Serbia", "Sport Klub 4 Serbia",
    "TNT Sports 1 UK", "TNT Sports 2 UK", "TNT Sports 3 UK", "TNT Sports 4 UK",
]

ALIASES: Dict[str, List[re.Pattern]] = {
    **{f"beIN SPORTS {i} Turkey": [re.compile(fr"bein\s*sports\s*{i}\s*turkey", re.I)] for i in range(1, 5)},
    **{f"Eleven Sports {i} Portugal": [re.compile(fr"eleven\s*sports\s*{i}\s*portugal", re.I)] for i in range(1, 6)},
    **{f"Sport TV{i} Portugal": [re.compile(fr"sport\s*tv\s*{i}\s*portugal", re.I)] for i in range(1, 7)},
    **{f"beIN SPORTS {i} France": [re.compile(fr"bein\s*sports\s*{i}\s*france", re.I)] for i in range(1, 4)},
    **{f"beIN Sports MAX {i} France": [re.compile(fr"bein\s*sports\s*max\s*{i}\s*france", re.I)] for i in range(4, 11)},
    **{f"TNT Sports {i} UK": [re.compile(fr"tnt\s*sports\s*{i}\s*uk", re.I)] for i in range(1, 5)},
    **{f"Sport Klub {i} Serbia": [re.compile(fr"sport\s*klub\s*{i}\s*serbia", re.I)] for i in range(1, 5)},
    "Sport Klub Serbia": [re.compile(r"sport\s*klub\s*$", re.I)],
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
}

# ---------- YARDIMCI FONKSİYONLAR ----------

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
                if nxt and not nxt.startswith("#"):
                    url = nxt
            out.append((ln, url))
            i += 2
            continue
        i += 1
    return out

def find_first_match(extinf: str, patterns: List[re.Pattern]) -> bool:
    txt = extinf
    m = re.search(r"#EXTINF[^,]*,(.*)$", extinf, flags=re.I)
    if m:
        txt = m.group(1)
    for p in patterns:
        if p.search(txt):
            return True
    return False

def pick_wanted_clean(source_pairs: List[Tuple[str, Optional[str]]]) -> Dict[str, Tuple[str, Optional[str]]]:
    picked: Dict[str, Tuple[str, Optional[str]]] = {}
    for extinf, url in source_pairs:
        if not url:
            continue
        for official_name in WANTED_CHANNELS:
            if official_name in picked:
                continue
            pats = ALIASES.get(official_name, [])
            if find_first_match(extinf, pats):
                clean_line = f"#EXTINF:-1,{official_name}"
                picked[official_name] = (clean_line, url)
    return picked

def upsert_github_file(repo: str, branch: str, path_in_repo: str, content_bytes: bytes, message: str, token: str):
    base = "https://api.github.com"
    url = f"{base}/repos/{repo}/contents/{path_in_repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    sha = None
    get_res = requests.get(url, headers=headers, params={"ref": branch}, timeout=TIMEOUT)
    if get_res.status_code == 200:
        sha = get_res.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload, timeout=TIMEOUT)
    if put_res.status_code not in (200, 201):
        raise RuntimeError(f"GitHub PUT failed: {put_res.status_code} {put_res.text}")
    return put_res.json()

def render_updated
