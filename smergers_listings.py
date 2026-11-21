#!/usr/bin/env python3
"""Scrape SMERGERS listing pages (not detail pages) into a CSV.

Usage:
    pip install requests beautifulsoup4
    python smergers_listings.py --max-pages 20 --out all.csv
    python smergers_listings.py --url https://www.smergers.com/technology-businesses-for-sale-and-investment/s1412b/
"""
import argparse
import csv
import random
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin, urlencode, urlparse, parse_qsl, urlunparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.smergers.com"
DEFAULT_URL = BASE + "/businesses-for-sale/t2b/"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
FIELDS = ["title", "url", "tagline", "description", "rating", "location",
          "run_rate_sales", "ebitda_margin", "deal_type", "price"]


def clean(text):
    return " ".join(text.split()) if text else ""


def page_url(url, page):
    if page == 1:
        return url
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query))
    q["page"] = str(page)
    return urlunparse(parts._replace(query=urlencode(q)))


def parse_card(card):
    row = dict.fromkeys(FIELDS, "")
    link = card.select_one("h2 a[href]")
    href = card.get("data-url") or (link["href"] if link else "")
    if not href or "/business/" not in href:
        return None  # promo cards (e.g. "list your business") are not listings
    row["url"] = urljoin(BASE, href)
    if link:
        row["title"] = clean(link.get_text())

    tag = card.select_one('[itemprop="name"]')
    row["tagline"] = clean(tag.get_text()) if tag else clean(card.get("title"))

    desc = card.select_one('[itemprop="description"]')
    row["description"] = clean(desc.get_text()) if desc else ""

    rating = card.select_one('[itemprop="ratingValue"]')
    if rating is not None:
        row["rating"] = rating.get("content", "")
    else:
        r = card.select_one("span.rating")
        row["rating"] = clean(r.get_text()) if r else ""

    loc = card.select_one("span.location")
    if loc:
        row["location"] = loc.get("data-title") or clean(loc.get_text())

    # Metric rows are label/value pairs of col-xs-6 divs.
    cells = card.select("div.bg-grey-100 > div.col-xs-6")
    for label_div, value_div in zip(cells[0::2], cells[1::2]):
        label = clean(label_div.get_text()).lower()
        value = clean(value_div.get_text())
        if "sales" in label:
            row["run_rate_sales"] = value
        elif "ebitda" in label:
            row["ebitda_margin"] = value

    contact = card.select_one("div.listing-contact-button")
    if contact:
        deal = contact.select_one(".sme-v3-smalltext")
        row["deal_type"] = clean(deal.get_text()) if deal else ""
        price = contact.select_one(".sme-v3-bolder")
        if price:
            row["price"] = clean(price.get_text())
    return row


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    return [r for r in (parse_card(c) for c in soup.select("div.listing-card")) if r]


def robots_delay(session, url):
    rp = urllib.robotparser.RobotFileParser()
    try:
        resp = session.get(urljoin(BASE, "/robots.txt"), timeout=30)
        rp.parse(resp.text.splitlines())
    except requests.RequestException:
        return True, None
    return rp.can_fetch(UA, url), rp.crawl_delay(UA)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=DEFAULT_URL, help="listing page to start from")
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--out", default="smergers_listings.csv")
    ap.add_argument("--delay", type=float, default=15.0,
                    help="seconds between pages (robots.txt asks for 15)")
    args = ap.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "en"})

    allowed, crawl_delay = robots_delay(session, args.url)
    if not allowed:
        sys.exit(f"robots.txt disallows {args.url}")
    delay = max(args.delay, crawl_delay or 0)

    seen, total = set(), 0
    # utf-8-sig so Excel detects the encoding; rows are flushed after each page.
    f = open(args.out, "w", newline="", encoding="utf-8-sig")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for page in range(1, args.max_pages + 1):
        url = page_url(args.url, page)
        if page > 1:
            time.sleep(delay + random.uniform(0, 2))
        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"page {page}: request failed ({e}), stopping", file=sys.stderr)
            break
        if resp.status_code != 200:
            print(f"page {page}: HTTP {resp.status_code}, stopping", file=sys.stderr)
            break
        new = [r for r in parse_page(resp.text) if r["url"] not in seen]
        for r in new:
            seen.add(r["url"])
        w.writerows(new)
        f.flush()
        total += len(new)
        print(f"page {page}: {len(new)} new listings (total {total})", file=sys.stderr, flush=True)
        if not new:
            break

    f.close()
    print(f"wrote {total} listings to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
