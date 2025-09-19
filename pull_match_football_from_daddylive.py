# pull_match_football_from_daddylive.py
# -*- coding: utf-8 -*-
"""
يسحب فقط قنوات محددة من daddylive (M3U)، ويحدّث ملف generalsports.m3u في الريبو بصيغة نظيفة.
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
    "https://raw.githubusercontent.com/a7shk1/m3u-broadcast/refs/heads/main/generalsports.m3u"
)

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO    = os.getenv("GITHUB_REPO", "a7shk1/m3u-broadcast")
GITHUB_BRANCH  = os.getenv("GITHUB_BRANCH", "main")
DEST_REPO_PATH = os.getenv("DEST_REPO_PATH", "generalsports.m3u")
COMMIT_MESSAGE = os.getenv("COMMIT_MESSAGE", "chore: update selected sports channels from daddylive")

OUTPUT_LOCAL_PATH = os.getenv("OUTPUT_LOCAL_PATH", "./out/generalsports.m3u")

TIMEOUT = 25
VERIFY_SSL = True

# ---------- القنوات المطلوبة مع تعابير مرنة (aliases) ----------

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
    "beIN SPORTS 1 Turkey": [re.compile(r"bein\s*sports\s*1\s*turkey", re.I)],
    "beIN SPORTS 2 Turkey": [re.compile(r"bein\s*sports\s*2\s*turkey", re.I)],
    "beIN SPORTS 3 Turkey": [re.compile(r"bein\s*sports\s*3\s*turkey", re.I)],
    "beIN SPORTS 4 Turkey": [re.compile(r"bein\s*sports\s*4\s*turkey", re.I)],
    "Eleven Sports 1 Portugal": [re.compile(r"eleven\s*sports\s*1\s*portugal", re.I)],
    "Eleven Sports 2 Portugal": [re.compile(r"eleven\s*sports\s*2\s*portugal", re.I)],
    "Eleven Sports 3 Portugal": [re.compile(r"eleven\s*sports\s*3\s*portugal", re.I)],
    "Eleven Sports 4 Portugal": [re.compile(r"eleven\s*sports\s*4\s*portugal", re.I)],
    "Eleven Sports 5 Portugal": [re.compile(r"eleven\s*sports\s*5\s*portugal", re.I)],
    "Sport TV1 Portugal": [re.compile(r"sport\s*tv\s*1\s*portugal", re.I), re.compile(r"sport\s*tv1", re.I)],
    "Sport TV2 Portugal": [re.compile(r"sport\s*tv\s*2\s*portugal", re.I), re.compile(r"sport\s*tv2", re.I)],
    "Sport TV3 Portugal": [re.compile(r"sport\s*tv\s*3\s*portugal", re.I), re.compile(r"sport\s*tv3", re.I)],
    "Sport TV4 Portugal": [re.compile(r"sport\s*tv\s*4\s*portugal", re.I), re.compile(r"sport\s*tv4", re.I)],
    "Sport TV5 Portugal": [re.compile(r"sport\s*tv\s*5\s*portugal", re.I), re.compile(r"sport\s*tv5", re.I)],
    "Sport TV6 Portugal": [re.compile(r"sport\s*tv\s*6\s*portugal", re.I), re.compile(r"sport\s*tv6", re.I)],
    "beIN SPORTS 1 France": [re.compile(r"bein\s*sports\s*1\s*france", re.I)],
    "beIN SPORTS 2 France": [re.compile(r"bein\s*sports\s*2\s*france", re.I)],
    "beIN SPORTS 3 France": [re.compile(r"bein\s*sports\s*3\s*france", re.I)],
    "beIN Sports MAX 4 France": [re.compile(r"bein\s*sports\s*max\s*4\s*france", re.I)],
    "beIN Sports MAX 5 France": [re.compile(r"bein\s*sports\s*max\s*5\s*france", re.I)],
    "beIN Sports MAX 6 France": [re.compile(r"bein\s*sports\s*max\s*6\s*france", re.I)],
    "beIN Sports MAX 7 France": [re.compile(r"bein\s*sports\s*max\s*7\s*france", re.I)],
    "beIN Sports MAX 8 France": [re.compile(r"bein\s*sports\s*max\s*8\s*france", re.I)],
    "beIN Sports MAX 9 France": [re.compile(r"bein\s*sports\s*max\s*9\s*france", re.I)],
    "beIN Sports MAX 10 France": [re.compile(r"bein\s*sports\s*max\s*10\s*france", re.I)],
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
    "Sport Klub Serbia": [re.compile(r"sport\s*klub\s*serbia", re.I)],
    "Sport Klub 1 Serbia": [re.compile(r"sport\s*klub\s*1\s*serbia", re.I)],
    "Sport Klub 2 Serbia": [re.compile(r"sport\s*klub\s*2\s*serbia", re.I)],
    "Sport Klub 3 Serbia": [re.compile(r"sport\s*klub\s*3\s*serbia", re.I)],
    "Sport Klub 4 Serbia": [re.compile(r"sport\s*klub\s*4\s*serbia", re.I)],
    "TNT Sports 1 UK": [re.compile(r"tnt\s*sports\s*1", re.I)],
    "TNT Sports 2 UK": [re.compile(r"tnt\s*sports\s*2", re.I)],
    "TNT Sports 3 UK": [re.compile(r"tnt\s*sports\s*3", re.I)],
    "TNT Sports 4 UK": [re.compile(r"tnt\s*sports\s*4", re.I)],
}

# ---------- دوال مساعدة ----------

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

def render_updated(dest_text: str, picked: Dict[str, Tuple[str, Optional[str]]]) -> str:
    lines = [ln.rstrip("\n") for ln in dest_text.splitlines()]
    if not lines or not lines[0].strip().upper().startswith("#EXTM3U"):
        lines = ["#EXTM3U"] + lines

    idx_to_official: Dict[int, str] = {}
    for i, ln in enumerate(lines):
        if not ln.strip().startswith("#EXTINF"):
            continue
        display = ln
        m = re.search(r"#EXTINF[^,]*,(.*)$", ln, flags=re.I)
        if m:
            display = m.group(1).strip()
        for official_name in WANTED_CHANNELS:
            pats = ALIASES.get(official_name, [])
            if any(p.search(display) for p in pats) or any(p.search(ln) for p in pats):
                idx_to_official[i] = official_name
                break

    used = set()
    out: List[str] = []
    i = 0
    while i < len(lines):
        if i in idx_to_official:
            official = idx_to_official[i]
            pair = picked.get(official)
            if pair:
                clean_extinf, url = pair
                out.append(clean_extinf)
                if url:
                    out.append(url)
                used.add(official)
                if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith("#"):
                    i += 2
                else:
                    i += 1
                continue
            out.append(lines[i])
            i += 1
        else:
            out.append(lines[i])
            i += 1

    for name in WANTED_CHANNELS:
        if name in used:
            continue
        pair = picked.get(name)
        if not pair:
            continue
        clean_extinf, url = pair
        if out and out[-1].strip():
            out.append("")
        out.append(f"# --- {name} ---")
        out.append(clean_extinf)
        if url:
            out.append(url)

    while out and not out[-1].strip():
        out.pop()

    return "\n".join(out) + "\n"

# ---------- main ----------

def main():
    print("[i] Fetching source M3U...")
    src_text = fetch_text(SOURCE_URL)

    print("[i] Fetching destination M3U...")
    dest_text = fetch_text(DEST_RAW_URL)

    print("[i] Parsing source M3U entries...")
    pairs = parse_m3u_pairs(src_text)

    print(f"[i] Total entries in source: {len(pairs)}")

    picked = pick_wanted_clean(pairs)

    print("[i] Picked channels:")
    for name in WANTED_CHANNELS:
        print(f" 
