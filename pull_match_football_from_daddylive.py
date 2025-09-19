# -*- coding: utf-8 -*-
"""
Script to pull specified sports channels from daddylive M3U playlist and save to generalsports.m3u
"""

import os
import re
import requests
from typing import List, Tuple, Optional, Dict
import sys

SOURCE_URL = "https://raw.githubusercontent.com/DisabledAbel/daddylivehd-m3u/f582ae100c91adf8c8db905a8f97beb42f369a0b/daddylive-events.m3u8"

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
    # Örnek: "beIN SPORTS 1 Turkey": [re.compile(r"bein\s*sports\s*1\s*turkey", re.I),],
    # Diğer kanallar da benzer şekilde regexlerle eşleşecek
}

def fetch_text(url: str) -> str:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text

def parse_m3u_pairs(m3u_text: str) -> List[Tuple[str, Optional[str]]]:
    """
    Parses M3U playlist text and returns list of tuples (extinf_line, url)
    """
    lines = m3u_text.splitlines()
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith("#"):
                    pairs.append((line, next_line))
                    i += 2
                    continue
        i += 1
    return pairs

def match_channel(channel_name: str) -> Optional[str]:
    """
    Returns the wanted channel name if the given channel_name matches an alias.
    """
    for wanted in WANTED_CHANNELS:
        if wanted.lower() in channel_name.lower():
            return wanted
    return None

def main():
    print("Fetching source M3U playlist...")
    source_text = fetch_text(SOURCE_URL)

    print("Parsing playlist...")
    pairs = parse_m3u_pairs(source_text)

    print(f"Filtering channels from {len(pairs)} entries...")
    filtered = []
    for extinf, url in pairs:
        # Kanal adını extinf satırından çekiyoruz
        # Örnek: #EXTINF:-1 tvg-id="someid" tvg-name="beIN SPORTS 1 Turkey" group-title="Sports",beIN SPORTS 1 Turkey
        channel_name_match = re.search(r',(.+)$', extinf)
        if channel_name_match:
            channel_name = channel_name_match.group(1).strip()
            if any(alias.lower() in channel_name.lower() for alias in WANTED_CHANNELS):
                filtered.append((extinf, url))

    print(f"Writing {len(filtered)} filtered channels to generalsports.m3u...")
    with open("generalsports.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for extinf, url in filtered:
            f.write(f"{extinf}\n{url}\n")

    print("Done.")

if __name__ == "__main__":
    main()
