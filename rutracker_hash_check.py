#!/usr/bin/env python3
import argparse
import base64
import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests


def btih_to_hex(btih: str) -> str:
    v = btih.strip()
    if re.fullmatch(r"[A-Fa-f0-9]{40}", v):
        return v.lower()
    if re.fullmatch(r"[A-Z2-7]{32}", v.upper()):
        raw = base64.b32decode(v.upper())
        return raw.hex()
    raise ValueError(f"Unsupported BTIH format: {v}")


def extract_hash_from_page(html: str) -> str:
    magnets = re.findall(r"magnet:\?[^\"'\s<>]+", html, flags=re.IGNORECASE)
    if not magnets:
        raise RuntimeError("Magnet link not found on page")

    for magnet in magnets:
        parsed = urlparse(magnet)
        qs = parse_qs(parsed.query)
        xt_list = qs.get("xt", [])
        for xt in xt_list:
            m = re.search(r"urn:btih:([^&]+)", xt, flags=re.IGNORECASE)
            if m:
                return btih_to_hex(m.group(1))
        m = re.search(r"btih:([A-Fa-f0-9]{40}|[A-Z2-7]{32})", magnet, flags=re.IGNORECASE)
        if m:
            return btih_to_hex(m.group(1))

    raise RuntimeError("BTIH hash not found in magnet link")


def extract_title_from_page(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return "(title not found)"
    title = unescape(m.group(1))
    title = re.sub(r"\s+", " ", title).strip()
    return title or "(empty title)"


def read_links_from_file(path: Path) -> list[str]:
    links: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        links.append(line)
    if not links:
        raise RuntimeError(f"No links found in file: {path}")
    return links


def load_previous_hashes(hash_path: Path, links: list[str]) -> dict[str, str]:
    if not hash_path.exists():
        return {}

    raw = hash_path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}

    # New format: JSON map {url: hash}
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if isinstance(k, str) and isinstance(v, str):
                    out[k] = v.lower()
            return out
    except json.JSONDecodeError:
        pass

    # Backward compatibility with old single-hash plain text format
    # If exactly one link is tracked, map old hash to that link.
    if len(links) == 1 and re.fullmatch(r"[A-Fa-f0-9]{40}", raw):
        return {links[0]: raw.lower()}

    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BTIH hashes on RuTracker pages")
    parser.add_argument("--url", help="Single forum topic URL (legacy mode)")
    parser.add_argument("--links-file", help="Path to file with URLs (one URL per line)")
    parser.add_argument("--hash-file", required=True, help="Path to stored hash file (JSON map)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON result")
    args = parser.parse_args()

    if bool(args.url) == bool(args.links_file):
        msg = "Use exactly one source: --url OR --links-file"
        if args.as_json:
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False))
        else:
            print(f"error: {msg}")
        return 2

    if args.links_file:
        links_path = Path(args.links_file)
        if not links_path.exists():
            msg = f"Links file not found: {links_path}"
            if args.as_json:
                print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False))
            else:
                print(f"error: {msg}")
            return 2
        links = read_links_from_file(links_path)
    else:
        links = [args.url.strip()]

    hash_path = Path(args.hash_file)
    hash_path.parent.mkdir(parents=True, exist_ok=True)

    previous_hashes = load_previous_hashes(hash_path, links)
    had_previous = bool(previous_hashes)

    current_hashes: dict[str, str] = {}
    per_link: list[dict[str, str | None]] = []
    changed_items: list[dict[str, str]] = []

    try:
        for url in links:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            html = resp.text
            current_hash = extract_hash_from_page(html)
            page_title = extract_title_from_page(html)
            prev_hash = previous_hashes.get(url)

            if prev_hash is None:
                link_status = "new"
            elif prev_hash == current_hash:
                link_status = "same"
            else:
                link_status = "changed"
                changed_items.append({"url": url, "title": page_title})

            current_hashes[url] = current_hash
            per_link.append(
                {
                    "url": url,
                    "status": link_status,
                    "title": page_title,
                    "current_hash": current_hash,
                    "previous_hash": prev_hash,
                }
            )
    except Exception as e:
        msg = f"error: {e}"
        if args.as_json:
            print(json.dumps({"status": "error", "message": msg}, ensure_ascii=False))
        else:
            print(msg)
        return 2

    hash_path.write_text(json.dumps(current_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not had_previous:
        status = "initialized"
        text = "хеш прежний"
    elif changed_items:
        status = "changed"
        lines = ["хеш изменился"]
        for item in changed_items:
            lines.append(f"title: {item['title']}")
        text = "\n".join(lines)
    else:
        status = "same"
        text = "хеш прежний"

    if args.as_json:
        print(
            json.dumps(
                {
                    "status": status,
                    "message": text,
                    "changed_count": len(changed_items),
                    "changed_items": changed_items,
                    "links_total": len(links),
                    "results": per_link,
                    "hash_file": str(hash_path),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
