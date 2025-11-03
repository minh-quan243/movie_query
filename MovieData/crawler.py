#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMDb range crawler (educational). v10
"""

import argparse
import csv
import html
import json
import random
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE = "https://www.imdb.com"
UA = "Mozilla/5.0 (compatible; Deon-SE-Project/1.0; +https://example.com/)"

# -------------------- small helpers --------------------

def jitter(a=1.0, b=2.2):
    time.sleep(random.uniform(a, b))

def wait_css(driver, selector, timeout=15):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

def get_texts(driver, selector) -> List[str]:
    try:
        return [e.text.strip() for e in driver.find_elements(By.CSS_SELECTOR, selector) if e.text.strip()]
    except NoSuchElementException:
        return []

def get_attr(driver, selector, attr) -> Optional[str]:
    try:
        el = driver.find_element(By.CSS_SELECTOR, selector)
        val = el.get_attribute(attr)
        return val.strip() if val else None
    except NoSuchElementException:
        return None

def extract_year(s: Optional[str]) -> Optional[int]:
    if not s: return None
    m = re.search(r"(19|20|21)\d{2}", s)
    return int(m.group()) if m else None

def parse_iso8601_duration(dur: Optional[str]) -> Optional[int]:
    if not dur: return None
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur)
    if not m: return None
    h = int(m.group(1) or 0)
    m_ = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h*60 + m_ + (1 if s >= 30 else 0)

def parse_runtime_text(txt: Optional[str]) -> Optional[int]:
    if not txt: return None
    t = txt.replace("\xa0", " ").lower()
    m = re.search(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)", t)
    if m:
        h = int(m.group(1) or 0); mm = int(m.group(2) or 0)
        return h*60 + mm
    m2 = re.search(r"(\d+)\s*min", t)
    return int(m2.group(1)) if m2 else None

def extract_int(s: Optional[str]) -> Optional[int]:
    if not s: return None
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits.isdigit() else None

def safe_float(x) -> Optional[float]:
    try: return float(x)
    except Exception: return None

def retry(fn, tries=2, fallback=None, backoff=2.0):
    for i in range(tries):
        try:
            return fn()
        except (TimeoutException, WebDriverException, StaleElementReferenceException):
            time.sleep(backoff * (i + 1))
    return fallback

def scroll_to_bottom(driver, steps=4, pause=0.6):
    height = 0
    for _ in range(steps):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_h = driver.execute_script("return document.body.scrollHeight;")
        if new_h == height: break
        height = new_h

def scroll_into_view(driver, css):
    try:
        el = driver.find_element(By.CSS_SELECTOR, css)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
    except Exception:
        pass

def clean_text(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    # Decode HTML entities like &apos; to '
    s = html.unescape(str(s))
    return re.sub(r"\s+", " ", s).strip()

def serialize_field(val):
    if isinstance(val, list):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, str):
        return clean_text(val)
    return val

def uniq_keep_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# -------------------- WebDriver --------------------

def build_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,1200")
    opts.add_argument(f"--user-agent={UA}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(40)
    return driver

# -------------------- consent banner --------------------

def dismiss_consent(driver):
    """Close cookie/privacy banners; safe no-op if absent."""
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
        if btns:
            driver.execute_script("arguments[0].click();", btns[0]); time.sleep(0.3); return
        for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
            label = (el.text or "").strip().lower()
            if any(k in label for k in ["accept", "agree", "got it", "continue"]):
                try:
                    driver.execute_script("arguments[0].click();", el); time.sleep(0.3); return
                except Exception:
                    continue
    except Exception:
        pass

# -------------------- Monthly Date Range Generator --------------------

def generate_monthly_ranges(start_month: str, end_month: str) -> List[Tuple[str, str]]:
    """
    Generate list of (date_from, date_to) tuples for each complete month.
    Format: YYYY-MM-DD
    
    Args:
        start_month: YYYY-MM format
        end_month: YYYY-MM format
    
    Returns:
        List of tuples: [(from_date, to_date), ...]
    
    Raises:
        ValueError: If end_month is incomplete (current month)
    """
    start_date = datetime.strptime(start_month, "%Y-%m")
    end_date = datetime.strptime(end_month, "%Y-%m")
    
    # Check if end month is complete (not the current month)
    today = datetime.now()
    current_month = datetime(today.year, today.month, 1)
    
    if end_date >= current_month:
        raise ValueError(
            f"End month {end_month} is not complete yet. "
            f"Current month is {today.strftime('%Y-%m')}. "
            f"Please use a previous complete month."
        )
    
    if start_date > end_date:
        raise ValueError(f"Start month {start_month} is after end month {end_month}")
    
    ranges = []
    current = start_date
    
    while current <= end_date:
        # First day of month
        from_date = current.strftime("%Y-%m-01")
        
        # Last day of month
        if current.month == 12:
            next_month = datetime(current.year + 1, 1, 1)
        else:
            next_month = datetime(current.year, current.month + 1, 1)
        
        to_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
        
        ranges.append((from_date, to_date))
        
        # Move to next month
        current = next_month
    
    return ranges

# -------------------- discovery (Advanced Title Search) --------------------


def build_search_url(date_from: str, date_to: str, title_types: str, rating_range: Optional[str] = None) -> str:
    url = (f"{BASE}/search/title/"
           f"?title_type={title_types}"
           f"&release_date={date_from},{date_to}")
    if rating_range:
        # Convert format from "7:10" to "7,10" for IMDb URL
        rating_formatted = rating_range.replace(":", ",")
        url += f"&user_rating={rating_formatted}"
    return url

def find_load_more(driver):
    candidates = driver.find_elements(By.CSS_SELECTOR, "button, a")
    for el in candidates:
        label = (el.text or "").strip().lower()
        if not label: continue
        if "more" in label and any(tok in label for tok in ["50", "load", "see"]):
            return el
    return None

def parse_ids_from_new_cards(driver) -> List[str]:
    ids = []
    cards = driver.find_elements(By.CSS_SELECTOR, "div.ipc-metadata-list-summary-item, li.ipc-metadata-list-summary-item")
    for c in cards:
        links = c.find_elements(By.CSS_SELECTOR, 'a[href^="/title/tt"]')
        for a in links:
            href = a.get_attribute("href") or ""
            m = re.search(r"/title/(tt\d{7,8})", href)
            if m:
                ids.append(m.group(1))
                break
    return uniq_keep_order(ids)

def parse_ids_from_classic_lister(driver) -> List[str]:
    ids = []
    cards = driver.find_elements(By.CSS_SELECTOR, "div.lister-item, div.lister-item.mode-advanced")
    for c in cards:
        links = c.find_elements(By.CSS_SELECTOR, 'a[href^="/title/tt"]')
        for a in links:
            href = a.get_attribute("href") or ""
            m = re.search(r"/title/(tt\d{7,8})", href)
            if m:
                ids.append(m.group(1))
                break
    return uniq_keep_order(ids)

def discover_ids_new_ui(driver, max_titles: int, page_delay: float) -> List[str]:
    try:
        wait_css(driver, "div.ipc-metadata-list-summary-item, li.ipc-metadata-list-summary-item", timeout=10)
    except TimeoutException:
        return []

    last = -1
    while True:
        scroll_to_bottom(driver, steps=2, pause=0.7)
        ids = parse_ids_from_new_cards(driver)
        if max_titles and len(ids) >= max_titles:
            break
        if len(ids) == last:
            btn = find_load_more(driver)
            if not btn:
                break
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.25)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(page_delay + random.uniform(0.3, 0.8))
            except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
                break
        last = len(ids)

    ids = parse_ids_from_new_cards(driver)
    if max_titles and len(ids) > max_titles:
        ids = ids[:max_titles]
    return ids

def discover_ids_classic_paged(driver, base_url: str, max_titles: int, page_delay: float) -> List[str]:
    collected: List[str] = []
    start = 1
    while True:
        url = f"{base_url}&start={start}"
        driver.get(url)
        dismiss_consent(driver)
        try:
            wait_css(driver, "div.lister-item, div.lister-item.mode-advanced", timeout=10)
        except TimeoutException:
            break
        ids = parse_ids_from_classic_lister(driver)
        if not ids:
            break
        for t in ids:
            if t not in collected:
                collected.append(t)
        if max_titles and len(collected) >= max_titles:
            collected = collected[:max_titles]
            break
        start += 50
        time.sleep(page_delay + random.uniform(0.2, 0.5))
    return collected

def discover_ids(driver, date_from: str, date_to: str, title_types: str,
                 max_titles: int, page_delay: float, rating_range: Optional[str] = None) -> List[str]:
    base_url = build_search_url(date_from, date_to, title_types, rating_range)
    driver.get(base_url)
    dismiss_consent(driver)

    ids = discover_ids_new_ui(driver, max_titles=max_titles, page_delay=page_delay)
    if not ids:
        ids = discover_ids_classic_paged(driver, base_url=base_url, max_titles=max_titles, page_delay=page_delay)
    return ids

# -------------------- title scraping --------------------

@dataclass
class MovieDoc:
    id: str
    title: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    runtime: Optional[int] = None
    poster_url: Optional[str] = None

    director: List[str] = None
    writer: List[str] = None
    cast: List[str] = None
    production_country: List[str] = None
    production_companies: List[str] = None

    genre: List[str] = None
    tag: List[str] = None
    keyword: List[str] = None
    plot: Optional[str] = None

    rating: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[int] = None

    language: List[str] = None
    mprating: Optional[str] = None
    mprated_reason: Optional[str] = None
    awards: Optional[str] = None
    trailer_url: Optional[str] = None

    def as_dict(self) -> Dict:
        d = asdict(self)
        for k in ["director","writer","cast","production_country","production_companies","genre","tag","keyword","language"]:
            if d.get(k) is None:
                d[k] = []
        for k in ["plot","awards"]:
            d[k] = clean_text(d.get(k))
        # belt-and-suspenders: strip labels again before output
        d["production_country"] = strip_label_tokens(d.get("production_country", []))
        d["language"] = strip_label_tokens(d.get("language", []))
        d["production_companies"] = strip_label_tokens(d.get("production_companies", []))
        return d

def parse_title_jsonld(driver) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for s in driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]'):
        txt = s.get_attribute("textContent") or ""
        if not txt.strip(): continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for d in items:
            if d.get("@type") not in ("Movie", "TVSeries", "TVMiniSeries"):
                continue
            
            # Handle title vs original_title intelligently
            # IMDb's JSON-LD can have name/alternateName in either order
            # We want: title=International/English, original_title=Native language
            name = d.get("name")
            alternate = d.get("alternateName")
            
            if alternate and name != alternate:
                # Check if name contains mostly non-Latin characters (CJK, etc.)
                # If so, it's likely the original language title
                def is_non_latin(text):
                    if not text:
                        return False
                    non_latin = sum(1 for c in text if ord(c) > 127)
                    return non_latin > len(text) * 0.3  # >30% non-ASCII
                
                if is_non_latin(name) and not is_non_latin(alternate):
                    # name is original (e.g., Japanese), alternate is international (English)
                    out["title"] = alternate
                    out["original_title"] = name
                elif is_non_latin(alternate) and not is_non_latin(name):
                    # alternate is original, name is international
                    out["title"] = name
                    out["original_title"] = alternate
                else:
                    # Both or neither are non-Latin, use as-is
                    out["title"] = name
                    out["original_title"] = alternate
            else:
                # No alternate or they're the same
                out["title"] = name
                out["original_title"] = alternate or name
            
            out["plot"] = clean_text(d.get("description"))
            out["poster_url"] = d.get("image")

            g = d.get("genre")
            if isinstance(g, list): out["genre"] = g
            elif isinstance(g, str): out["genre"] = [g]

            out["runtime"] = parse_iso8601_duration(d.get("duration"))
            out["year"] = extract_year(d.get("datePublished"))

            ar = d.get("aggregateRating") or {}
            out["rating"] = safe_float(ar.get("ratingValue"))
            out["vote_count"] = extract_int(str(ar.get("ratingCount"))) if ar.get("ratingCount") is not None else None

            directors = d.get("director") or []
            if isinstance(directors, dict): directors = [directors]
            out["director"] = [p.get("name") for p in directors if isinstance(p, dict) and p.get("name")]

            writers = []
            for key in ("author", "creator"):
                val = d.get(key) or []
                if isinstance(val, dict): val = [val]
                for v in val:
                    if isinstance(v, dict) and v.get("@type") == "Person" and v.get("name"):
                        writers.append(v["name"])
            out["writer"] = uniq_keep_order(writers)

            actors = d.get("actor") or []
            if isinstance(actors, dict): actors = [actors]
            out["cast"] = [p.get("name") for p in actors if isinstance(p, dict) and p.get("name")]

            comps = d.get("productionCompany") or []
            if isinstance(comps, dict): comps = [comps]
            out["production_companies"] = [c.get("name") for c in comps if isinstance(c, dict) and c.get("name")]

            countries = d.get("countryOfOrigin") or d.get("countryOfOriginList") or []
            if isinstance(countries, dict): countries = [countries]
            vals = []
            for c in (countries if isinstance(countries, list) else []):
                if isinstance(c, dict) and c.get("name"): vals.append(c["name"])
                elif isinstance(c, str): vals.append(c)
            out["production_country"] = vals

            lang = d.get("inLanguage") or d.get("language") or []
            if isinstance(lang, str): lang = [lang]
            out["language"] = lang

            tr = d.get("trailer")
            if isinstance(tr, dict):
                out["trailer_url"] = tr.get("embedUrl") or tr.get("url")

            return out
    return out

def details_values(driver, label_substring: str) -> List[str]:
    # values inside the same <li> as the label
    items = driver.find_elements(
        By.XPATH,
        f"//li[.//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{label_substring.lower()}')]]//a | "
        f"//li[.//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{label_substring.lower()}')]]//span"
    )
    texts = [e.text.strip() for e in items if e.text.strip()]
    return uniq_keep_order(texts)

def strip_label_tokens(values: List[str]) -> List[str]:
    # remove labels even with colon/whitespace variants
    # Match full label strings or labels at the start of a string (with optional colon)
    bad = re.compile(
        r"(?i)^\s*(production compan(?:y|ies)|languages?|awards?|countr(?:y|ies)\s+of\s+origin)\s*:?\s*$"
    )
    # Also remove if it's just the label text (for cases where the label appears as a separate item)
    filtered = []
    for v in values:
        v_stripped = v.strip()
        if not v_stripped:
            continue
        # Skip if entire value is just a label
        if bad.match(v_stripped):
            continue
        # Skip common label-only strings
        if v_stripped.lower() in ('country of origin', 'countries of origin', 'production company', 
                                   'production companies', 'language', 'languages', 'awards', 'award'):
            continue
        filtered.append(v)
    return filtered

def extract_mpa_rating(values: List[str]) -> tuple[Optional[str], Optional[str], List[str]]:
    """
    Extract MPA rating info from a list of values (usually from language field).
    Returns: (mprating, mprated_reason, cleaned_values)
    """
    mprating = None
    mprated_reason = None
    cleaned = []
    
    for v in values:
        v_stripped = v.strip()
        if not v_stripped:
            continue
            
        # Skip "Motion Picture Rating (MPA)" label
        if re.search(r"(?i)motion\s+picture\s+rating\s*\(?\s*mpa\s*\)?", v_stripped):
            continue
            
        # Check if this is a rating string like "Rated R for..." or "- Rated R for..."
        rating_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s+for\s+(.+)$", v_stripped)
        if rating_match:
            mprating = rating_match.group(1).strip()
            mprated_reason = rating_match.group(2).strip()
            continue
            
        # Check for rating without reason like "Rated PG-13"
        rating_only_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s*\.?$", v_stripped)
        if rating_only_match:
            mprating = rating_only_match.group(1).strip()
            continue
        
        # If it's an actual language, keep it
        cleaned.append(v)
    
    return mprating, mprated_reason, cleaned

def scrape_top_cast(driver) -> List[str]:
    try:
        items = driver.find_elements(By.CSS_SELECTOR, '[data-testid="title-cast"] [data-testid="title-cast-item"] a[href^="/name/"]')
        cast_names = [a.text.strip() for a in items if a.text.strip()]
    except NoSuchElementException:
        cast_names = []
    return uniq_keep_order(cast_names)

def scrape_interest_tags(driver) -> List[str]:
    """Extract interest/tag chips from the main page."""
    try:
        # Find the interests section
        interests_div = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="interests"]')
        
        # Extract all chip texts
        chip_elements = interests_div.find_elements(By.CSS_SELECTOR, 'span.ipc-chip__text')
        tags = [chip.text.strip() for chip in chip_elements if chip.text.strip()]
        
        return uniq_keep_order(tags)
    except NoSuchElementException:
        return []

def scroll_into_view_xpath(driver, xpath):
    try:
        el = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
    except Exception:
        pass

def collect_all_genres(driver) -> List[str]:
    """Return the genres shown inside Storyline → Genres."""

    # First, scroll down to trigger lazy-loaded content
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(0.5)
    except Exception:
        pass

    # Wait for the Storyline section to load (client-side rendering)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='Storyline']"))
        )
    except TimeoutException:
        return []

    # Wait specifically for the genres list item
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-testid='storyline-genres']"))
        )
        time.sleep(0.3)  # Small wait for content to stabilize
    except TimeoutException:
        pass

    # Try multiple selectors to find the genres list item
    li_selectors = [
        (By.CSS_SELECTOR, "li[data-testid='storyline-genres']"),
        (By.XPATH, "//section[@data-testid='Storyline']//li[@data-testid='storyline-genres']"),
        (By.XPATH, "//li[@data-testid='storyline-genres']"),
        (By.XPATH, "//li[.//span[contains(@class,'ipc-metadata-list-item__label') and contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'genre')]]"),
    ]

    def extract_from_li(li) -> List[str]:
        # Try multiple selectors for genre links
        genre_link_selectors = [
            (By.CSS_SELECTOR, "a.ipc-metadata-list-item__list-content-item--link"),
            (By.CSS_SELECTOR, "a[href*='genres=']"),
            (By.XPATH, ".//a[contains(@href,'genres=')]"),
            (By.XPATH, ".//a[contains(@class,'ipc-metadata-list-item__list-content-item')]"),
        ]
        
        for by, selector in genre_link_selectors:
            try:
                anchors = li.find_elements(by, selector)
                if anchors:
                    texts = [a.text.strip() for a in anchors if a.text and a.text.strip()]
                    # Filter out non-genre text
                    texts = [t for t in texts if t and t.lower() not in ("see all", "genre", "genres")]
                    if texts:
                        return uniq_keep_order(texts)
            except Exception:
                continue

        # Fallback: parse text content
        full = (li.text or "").strip()
        if not full:
            return []
        full = re.sub(r"(?i)^genres?:?", "", full).strip()
        if not full:
            return []
        parts = [clean_text(p) for p in re.split(r"[\n\r•·]+", full)]
        parts = [p for p in parts if p and p.lower() not in ("see all", "genre", "genres")]
        return uniq_keep_order(parts)

    # Try each selector
    for by, selector in li_selectors:
        try:
            containers = driver.find_elements(by, selector)
            for li in containers:
                vals = extract_from_li(li)
                if vals:
                    return vals
        except Exception:
            continue

    return []

def scrape_certificate_from_storyline(driver) -> tuple[Optional[str], Optional[str]]:
    """
    Extract MPA rating from Storyline section's certificate field.
    Returns: (mprating, mprated_reason)
    """
    mprating = None
    mprated_reason = None
    
    try:
        # Wait for Storyline section to be present (should already be loaded for genres)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='Storyline']"))
        )
        
        # Find the certificate list item
        cert_li = driver.find_element(By.CSS_SELECTOR, "li[data-testid='storyline-certificate']")
        
        # Get all text from the certificate item
        cert_text = cert_li.text.strip()
        
        # Try to extract rating from the text
        # Pattern 1: "- Rated R for ..."
        rating_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s+for\s+(.+)$", cert_text, re.MULTILINE)
        if rating_match:
            mprating = rating_match.group(1).strip()
            mprated_reason = rating_match.group(2).strip()
            return mprating, mprated_reason
        
        # Pattern 2: Just "Rated PG-13" without reason
        rating_only_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s*\.?$", cert_text, re.MULTILINE)
        if rating_only_match:
            mprating = rating_only_match.group(1).strip()
            return mprating, mprated_reason
        
        # Pattern 3: Multi-line - label on one line, rating on another
        lines = [line.strip() for line in cert_text.split('\n') if line.strip()]
        for line in lines:
            if re.search(r"(?i)motion\s+picture\s+rating", line):
                continue  # Skip the label line
            
            # Check if this line has a rating
            rating_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s+for\s+(.+)$", line)
            if rating_match:
                mprating = rating_match.group(1).strip()
                mprated_reason = rating_match.group(2).strip()
                return mprating, mprated_reason
            
            rating_only_match = re.search(r"(?i)^-?\s*rated\s+([A-Z][A-Z0-9\-]*)\s*\.?$", line)
            if rating_only_match:
                mprating = rating_only_match.group(1).strip()
                return mprating, mprated_reason
    
    except (NoSuchElementException, TimeoutException):
        pass
    
    return mprating, mprated_reason

def scrape_title_main(driver, imdb_id) -> Dict:
    url = f"{BASE}/title/{imdb_id}/"
    driver.get(url)
    try:
        wait_css(driver, "body")
    except TimeoutException:
        pass
    jitter(0.6, 1.2)

    data = parse_title_jsonld(driver)

    # Extract titles from DOM (more reliable than JSON-LD)
    # Structure: 
    # - span.hero__primary-text contains the international/English title
    # - Following div.baseAlt may contain "Original title: [native title]"
    
    # Get the primary title (international/English)
    primary_title = get_attr(driver, 'span.hero__primary-text[data-testid="hero__primary-text"]', "textContent")
    
    # Try to find the original title from the div that follows the h1
    original_title_text = None
    try:
        # Look for div with class containing 'baseAlt' that has "Original title:" text
        divs = driver.find_elements(By.CSS_SELECTOR, 'div.baseAlt')
        for div in divs:
            text = div.text.strip()
            if text.startswith("Original title:"):
                original_title_text = text
                break
    except Exception:
        pass
    
    if primary_title:
        data["title"] = primary_title.strip()
        
        # Check if there's an "Original title: ..." text
        if original_title_text:
            # Remove "Original title: " prefix
            original_cleaned = re.sub(r"^Original title:\s*", "", original_title_text.strip(), flags=re.IGNORECASE)
            data["original_title"] = original_cleaned
        else:
            # No separate original title shown, use primary as both
            data["original_title"] = primary_title.strip()
    else:
        # Fallback to JSON-LD or h1 tag
        if not data.get("title"):
            fallback = get_attr(driver, "h1", "textContent")
            data["title"] = fallback.strip() if fallback else ""
        if not data.get("original_title"):
            data["original_title"] = data.get("title", "")

    # Year
    if not data.get("year"):
        ytxt = get_attr(driver, 'a[href*="releaseinfo"]', "textContent")
        data["year"] = extract_year(ytxt)

    # Runtime
    if data.get("runtime") is None:
        chip = get_attr(driver, '[data-testid="hero-title-block__metadata"] li:nth-child(3)', "textContent")
        rt = parse_runtime_text(chip)
        if rt is None:
            rowtxt = get_attr(driver, 'li[data-testid*="runtime"]', "textContent")
            rt = parse_runtime_text(rowtxt)
        data["runtime"] = rt

    # Genres: Get from Storyline section (more complete than JSON-LD)
    # Don't scroll manually here - collect_all_genres will handle it
    dom_genres = collect_all_genres(driver)
    if dom_genres:
        # Use DOM genres as they are more complete
        data["genre"] = dom_genres
    # Keep JSON-LD genres as fallback if DOM extraction fails
    elif not data.get("genre"):
        data["genre"] = []

    # Tags: Extract interest chips from main page
    tags = scrape_interest_tags(driver)
    if tags:
        data["tag"] = tags
    else:
        data["tag"] = []

    # MPA Rating: Try to get from Storyline section first (most reliable)
    mprating_storyline, mprated_reason_storyline = scrape_certificate_from_storyline(driver)
    if mprating_storyline:
        data["mprating"] = mprating_storyline
        data["mprated_reason"] = mprated_reason_storyline

    # Rating & votes
    if data.get("rating") is None:
        r = get_attr(driver, '[data-testid="hero-rating-bar__aggregate-rating__score"] span', "textContent")
        data["rating"] = safe_float(r)
    if data.get("vote_count") is None:
        for s in driver.find_elements(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__aggregate-rating__score"] ~ div span'):
            num = extract_int(s.text)
            if num:
                data["vote_count"] = num
                break

    # Popularity best-effort
    if data.get("popularity") is None:
        # Try to get the popularity rank directly from the score element
        try:
            # First try: Use the specific data-testid for the popularity score
            score_el = driver.find_element(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__popularity__score"]')
            score_text = score_el.text.strip()
            if score_text:
                data["popularity"] = int(score_text)
        except (NoSuchElementException, ValueError):
            # Fallback: Try alternative selectors
            try:
                selectors = [
                    'div[data-testid="hero-rating-bar__popularity"]',
                    'div[data-testid="hero-title-block__popularity"]',
                    'li[data-testid*="popularity"]',
                ]
                
                for sel in selectors:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        # Try to find the score child element within this container
                        try:
                            score_el = el.find_element(By.CSS_SELECTOR, '[data-testid*="__score"]')
                            score_text = score_el.text.strip()
                            if score_text:
                                data["popularity"] = int(score_text)
                                break
                        except NoSuchElementException:
                            # Fall back to parsing the full text
                            txt = el.get_attribute("textContent") or el.text or ""
                            if txt.strip():
                                # Remove "POPULARITY" prefix
                                txt_clean = re.sub(r"(?i)^POPULARITY\s*", "", txt.strip())
                                # Try to extract just the first number (the rank)
                                rank_match = re.match(r"^(\d+)", txt_clean)
                                if rank_match:
                                    data["popularity"] = int(rank_match.group(1))
                                    break
                    except NoSuchElementException:
                        continue
            except Exception:
                pass

    # Top cast (from main grid)
    top_cast = scrape_top_cast(driver)
    if top_cast:
        data["cast"] = top_cast

    # Director, Writer, and Stars from principal credits section
    # IMDb changed: JSON-LD no longer has director/writer, must extract from DOM
    if not data.get("director") or not data.get("writer"):
        principal_creds = scrape_principal_credits_from_main_page(driver)
        if not data.get("director"):
            data["director"] = principal_creds.get("director", [])
        if not data.get("writer"):
            data["writer"] = principal_creds.get("writer", [])
        # Also use stars if we don't have cast yet
        if not data.get("cast") and principal_creds.get("cast"):
            data["cast"] = principal_creds.get("cast", [])

    # --- Details section ---
    scroll_into_view(driver, 'section[data-testid="Details"], div[data-testid="Details"]')

    if not data.get("production_country"):
        countries = details_values(driver, "countries of origin") or details_values(driver, "country of origin")
        data["production_country"] = strip_label_tokens(countries)

    if not data.get("language"):
        langs = details_values(driver, "language")
        # Try to extract MPA rating from language if not already found in Storyline
        if not data.get("mprating"):
            mprating, mprated_reason, cleaned_langs = extract_mpa_rating(langs)
            data["mprating"] = mprating
            data["mprated_reason"] = mprated_reason
            data["language"] = strip_label_tokens(cleaned_langs)
        else:
            # Already have MPA rating from Storyline, just clean language array
            _, _, cleaned_langs = extract_mpa_rating(langs)
            data["language"] = strip_label_tokens(cleaned_langs)

    if not data.get("production_companies"):
        pcs = details_values(driver, "production compan")
        data["production_companies"] = strip_label_tokens(pcs)

    if not data.get("awards"):
        try:
            li = driver.find_element(By.XPATH, "//li[.//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'award')]]")
            raw = li.text.strip()
            data["awards"] = re.sub(r"(?i)^\s*awards?\s*:?\s*", "", raw).strip()
        except NoSuchElementException:
            data["awards"] = None

    return data

def scrape_principal_credits_from_main_page(driver) -> Dict:
    """
    Extract director, writer, and stars from the main title page.
    IMDb changed structure - JSON-LD no longer has director/writer, and fullcredits page changed.
    Now we extract from li[data-testid='title-pc-principal-credit'] on main page.
    """
    out = {"director": [], "writer": [], "cast": []}
    
    try:
        # Find all principal credit items (Director, Writers, Stars)
        credit_items = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="title-pc-principal-credit"]')
        
        for item in credit_items:
            # Get the label (Director, Writers, Stars, etc.)
            label_text = ""
            try:
                label_el = item.find_element(By.CSS_SELECTOR, 'span.ipc-metadata-list-item__label')
                label_text = label_el.text.strip().lower()
            except NoSuchElementException:
                continue
            
            # Get all the person names (links)
            names = []
            try:
                name_links = item.find_elements(By.CSS_SELECTOR, 'a[href*="/name/"]')
                names = [a.text.strip() for a in name_links if a.text.strip()]
            except NoSuchElementException:
                pass
            
            # Map to output based on label
            if "director" in label_text:
                out["director"] = names
            elif "writer" in label_text:
                out["writer"] = uniq_keep_order(names)
            elif "star" in label_text:
                out["cast"] = names[:10]  # Limit to 10 stars
    
    except Exception as e:
        # If extraction fails, return empty
        pass
    
    return out

def scrape_awards_details(driver, imdb_id) -> Optional[str]:
    url = f"{BASE}/title/{imdb_id}/awards/"
    driver.get(url)
    try:
        wait_css(driver, "body")
    except TimeoutException:
        pass
    jitter(0.5, 0.9)
    try:
        for sel in ["div.article h3", "h1", "h2", "h3"]:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in els:
                t = e.text.strip()
                if t: return t
    except Exception:
        return None
    return None

def scrape_trailer(driver, imdb_id) -> Optional[str]:
    url = f"{BASE}/title/{imdb_id}/videos/"
    driver.get(url)
    try:
        wait_css(driver, "body")
    except TimeoutException:
        pass
    jitter(0.5, 0.9)
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/']")
    preferred = []
    for a in links:
        href = a.get_attribute("href") or ""
        label = (a.text or "").lower()
        if "/video/" in href and ("trailer" in label or "official trailer" in label):
            preferred.append(href.split("?")[0])
    if preferred:
        return preferred[0]
    for a in links:
        href = a.get_attribute("href") or ""
        if "/video/" in href:
            return href.split("?")[0]
    return None

def scrape_keywords(driver, imdb_id) -> List[str]:
    """
    Scrape keywords from the keywords page.
    Clicks "See all" button if present to load all keywords.
    """
    url = f"{BASE}/title/{imdb_id}/keywords/"
    driver.get(url)
    try:
        wait_css(driver, "body")
    except TimeoutException:
        return []
    jitter(0.5, 0.9)
    
    # Try to click "See all" or "See more" button to expand all keywords
    try:
        # Look for various "See all" or "See more" button patterns
        see_all_selectors = [
            "button:has-text('See all')",
            "button:has-text('See more')",
            "a:has-text('See all')",
            "a:has-text('See more')",
            "button[aria-label*='See']",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'see all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'see more')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'see all')]",
        ]
        
        for selector in see_all_selectors:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    # Try to find button by text content
                    all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, a")
                    buttons = [btn for btn in all_buttons 
                              if 'see all' in (btn.text or "").lower() or 'see more' in (btn.text or "").lower()]
                
                if buttons:
                    button = buttons[0]
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)  # Wait for keywords to load
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"   Note: Could not click 'See all' button: {e}")
    
    # Extract all keywords from the page
    keywords = []
    try:
        # Keywords are in li[data-testid="list-summary-item"] a.ipc-metadata-list-summary-item__t
        keyword_links = driver.find_elements(
            By.CSS_SELECTOR, 
            'li[data-testid="list-summary-item"] a.ipc-metadata-list-summary-item__t'
        )
        keywords = [link.text.strip() for link in keyword_links if link.text.strip()]
    except NoSuchElementException:
        pass
    
    return uniq_keep_order(keywords)

def scrape_one(driver, imdb_id) -> Dict:
    main = retry(lambda: scrape_title_main(driver, imdb_id), tries=2, fallback={})
    
    # Awards fallback
    if not main.get("awards"):
        awards2 = retry(lambda: scrape_awards_details(driver, imdb_id), tries=1, fallback=None)
    else:
        awards2 = None

    # Trailer fallback
    trailer = main.get("trailer_url") or retry(lambda: scrape_trailer(driver, imdb_id), tries=1, fallback=None)
    
    # Keywords
    keywords = retry(lambda: scrape_keywords(driver, imdb_id), tries=1, fallback=[])

    doc = MovieDoc(
        id=imdb_id,
        title=main.get("title"),
        original_title=main.get("original_title"),
        year=main.get("year"),
        runtime=main.get("runtime"),
        poster_url=main.get("poster_url"),
        director=main.get("director", []),
        writer=main.get("writer", []),
        cast=main.get("cast", []),
        production_country=strip_label_tokens(main.get("production_country", [])),
        production_companies=strip_label_tokens(main.get("production_companies", [])),
        genre=main.get("genre", []),
        tag=main.get("tag", []),
        keyword=keywords,
        plot=main.get("plot"),
        rating=main.get("rating"),
        vote_count=main.get("vote_count"),
        popularity=main.get("popularity"),
        language=strip_label_tokens(main.get("language", [])),
        mprating=main.get("mprating"),
        mprated_reason=main.get("mprated_reason"),
        awards=re.sub(r"(?i)^\s*awards?\s*:?\s*", "", main.get("awards") or (awards2 or "")).strip() or None,
        trailer_url=trailer
    )
    return doc.as_dict()

# -------------------- outputs --------------------

# -------------------- Output --------------------

def validate_record(rec: Dict) -> bool:
    """
    Validate that all required fields are present and non-empty.
    
    Required fields:
    - id, title, original_title, year, runtime, poster_url
    - director, writer, cast
    - production_country, production_companies, genre, tag, keyword, plot
    - rating, vote_count, language
    
    Returns: (is_valid, list of missing fields)
    """
    required_fields = [
        'id', 'title', 'original_title', 'year', 'runtime', 'poster_url',
        'director', 'writer', 'cast',
        'production_country', 'production_companies', 'genre', 'tag', 'keyword', 'plot',
        'rating', 'vote_count', 'language'
    ]
    
    missing_fields = []
    
    for field in required_fields:
        if field not in rec:
            missing_fields.append(field)
            continue
        
        value = rec[field]
        
        # Check if value is None or empty
        if value is None:
            missing_fields.append(field)
            continue
        
        # For lists, check if empty
        if isinstance(value, list) and len(value) == 0:
            missing_fields.append(field)
            continue
        
        # For strings, check if empty after stripping
        if isinstance(value, str) and not value.strip():
            missing_fields.append(field)
            continue
    
    return (len(missing_fields) == 0, missing_fields)

def load_existing_data(out_prefix: Path) -> tuple[List[Dict], set]:
    """
    Load existing data from output files if they exist.
    Returns: (list of records, set of already-scraped IDs)
    """
    csv_path = out_prefix.with_suffix(".csv")
    existing_records = []
    existing_ids = set()
    
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            existing_records = df.to_dict('records')
            existing_ids = set(df['id'].astype(str))
            print(f"Loaded {len(existing_records)} existing records from {csv_path}")
            print(f"Found {len(existing_ids)} existing IDs to skip")
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")
    
    return existing_records, existing_ids

def append_outputs(new_records: List[Dict], out_prefix: Path, existing_records: List[Dict] = None):
    """
    Append new records to existing data files.
    If existing_records is provided, merge with them. Otherwise, append to files.
    """
    if not new_records:
        return
    
    # Combine with existing records if provided
    all_records = (existing_records or []) + new_records
    safe_records = [{k: serialize_field(v) for k, v in r.items()} for r in all_records]
    
    # Save JSONL (append mode if no existing_records, write mode if merging)
    jl = out_prefix.with_suffix(".jsonl")
    mode = "w" if existing_records is not None else "a"
    with jl.open(mode, encoding="utf-8") as f:
        records_to_write = safe_records if existing_records is not None else [{k: serialize_field(v) for k, v in r.items()} for r in new_records]
        for r in records_to_write:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    # Save CSV (always full write to maintain header and proper format)
    df = pd.DataFrame.from_records(safe_records)
    df.to_csv(
        out_prefix.with_suffix(".csv"),
        index=False,
        quoting=csv.QUOTE_NONNUMERIC,
        lineterminator="\n",
        encoding="utf-8"
    )
    
    total = len(all_records)
    new_count = len(new_records)
    print(f"💾 Saved {new_count} new records (total: {total}) to:")
    print(f"     {jl}")
    print(f"     {out_prefix.with_suffix('.csv')}")

def save_outputs(records: List[Dict], out_prefix: Path):
    """Legacy function - now uses append_outputs with no existing records"""
    append_outputs(records, out_prefix, existing_records=[])

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser(description="IMDb Advanced Search range crawler (Selenium + JSON-LD). v9")
    
    # Date arguments (mutually exclusive with --monthly)
    ap.add_argument("--from", dest="date_from", help="Start date YYYY-MM-DD")
    ap.add_argument("--to", dest="date_to", help="End date YYYY-MM-DD")
    
    # Monthly crawl mode
    ap.add_argument("--monthly", help="Monthly crawl mode: YYYY-MM:YYYY-MM (e.g., 2024-01:2024-09)")
    ap.add_argument("--monthly-limit", type=int, default=50, help="Max titles per month in monthly mode (default: 50)")
    
    # Filters
    ap.add_argument("--rating-range", help="IMDb rating range: min:max (e.g., 6:10)")
    ap.add_argument("--title-types", default="feature,tv_series,tv_miniseries",
                    help="Comma-separated types, e.g. feature,tv_series,tv_miniseries")
    
    # Limits and delays
    ap.add_argument("--max-titles", type=int, default=0, help="Stop after N titles (0 = all)")
    ap.add_argument("--delay", type=float, default=2, help="Delay between title scrapes")
    ap.add_argument("--page-delay", type=float, default=2, help="Delay after clicking '50 more' / page turns")
    ap.add_argument("--batch-size", type=int, default=50, help="Save progress every N titles (default: 50)")
    
    # Quality control
    ap.add_argument("--no-retry", action="store_true", help="Disable automatic rescrape validation")
    
    # Other options
    ap.add_argument("--headless", action="store_true", help="Run headless")
    ap.add_argument("--out", default="movies_out", help="Output prefix (no extension)")
    ap.add_argument("--resume", action="store_true", help="Resume from existing output file")
    
    args = ap.parse_args()
    
    # Validate arguments
    if args.monthly:
        if args.date_from or args.date_to:
            print("❌ Error: Cannot use --from/--to with --monthly mode")
            return
        try:
            # Parse and validate monthly range
            start_month, end_month = args.monthly.split(":")
            date_ranges = generate_monthly_ranges(start_month, end_month)
            print(f"📅 Monthly mode: {len(date_ranges)} months to crawl ({start_month} to {end_month})")
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
    else:
        if not args.date_from or not args.date_to:
            print("❌ Error: Must provide --from and --to, or use --monthly mode")
            return
        date_ranges = [(args.date_from, args.date_to)]
    
    # Validate rating range format
    if args.rating_range:
        try:
            min_rating, max_rating = args.rating_range.split(":")
            float(min_rating)
            float(max_rating)
        except (ValueError, AttributeError):
            print(f"❌ Error: Invalid rating range format. Use min:max (e.g., 6:10)")
            return
    
    out_prefix = Path(args.out)
    
    # Load existing data if resuming
    existing_records = []
    existing_ids = set()
    if args.resume:
        existing_records, existing_ids = load_existing_data(out_prefix)
    
    driver = build_driver(headless=args.headless)
    batch_results: List[Dict] = []
    total_scraped = 0
    max_consecutive_scrape_failures = 2
    max_validation_retries = 1
    
    try:
        # Process each date range (single range or multiple months)
        for range_idx, (date_from, date_to) in enumerate(date_ranges, 1):
            if args.monthly:
                # Extract month name for display
                month_name = datetime.strptime(date_from, "%Y-%m-%d").strftime("%B %Y")
                print(f"\n{'='*60}")
                print(f"📅 Month {range_idx}/{len(date_ranges)}: {month_name}")
                print(f"   Date range: {date_from} to {date_to}")
                print(f"{'='*60}")
                target_titles = args.monthly_limit
            else:
                target_titles = args.max_titles
            
            # Discover 30% more IDs to compensate for validation failures
            # Only apply buffer if a limit is set (not 0 = unlimited)
            if target_titles > 0:
                discovery_limit = int(target_titles * 1.5)
                print(f"\n🔍 Discovering IDs for {date_from} to {date_to} (target: {target_titles}, discovering: {discovery_limit})...")
            else:
                discovery_limit = 0
                print(f"\n🔍 Discovering IDs for {date_from} to {date_to}...")
            
            all_ids = discover_ids(
                driver, date_from, date_to, args.title_types,
                max_titles=discovery_limit,
                page_delay=args.page_delay,
                rating_range=args.rating_range
            )
            
            # Filter out already-scraped IDs
            new_ids = [tid for tid in all_ids if tid not in existing_ids]
            
            # Show discovery results with target/backup breakdown
            if target_titles > 0 and len(new_ids) > target_titles:
                backup_count = len(new_ids) - target_titles
                print(f"   Found {len(new_ids)} new IDs ({target_titles} target + {backup_count} backup)")
            elif existing_ids and len(all_ids) > len(new_ids):
                print(f"   Found {len(all_ids)} total IDs, {len(all_ids) - len(new_ids)} already scraped, {len(new_ids)} new")
            else:
                print(f"   Found {len(new_ids)} new IDs")
            
            if not new_ids:
                print("   ⏭️  No new IDs to scrape in this range")
                continue
            
            # Scrape each title
            consecutive_scrape_failures = 0
            
            # Calculate max width for alignment (account for full [i/total] string)
            max_index_str = f"[{len(new_ids)}/{len(new_ids)}]"
            max_index_width = len(max_index_str)
            
            for i, tid in enumerate(new_ids, 1):
                # Format: [1/75]  tt1234567  ✓
                index_str = f"[{i}/{len(new_ids)}]"
                print(f"{index_str:<{max_index_width + 2}} {tid:<15}", end=" ")
                
                retry_count = 0
                success = False
                rec = None
                validation_errors = []
                
                # Try scraping with validation retries
                while retry_count <= (max_validation_retries if not args.no_retry else 0):
                    try:
                        rec = scrape_one(driver, tid)
                        
                        # Validate record if retry is enabled
                        if not args.no_retry:
                            is_valid, missing_fields = validate_record(rec)
                            if is_valid:
                                success = True
                                break
                            else:
                                retry_count += 1
                                validation_errors = missing_fields
                                if retry_count > max_validation_retries:
                                    # Final failure - show error
                                    missing_str = ", ".join(missing_fields)
                                    print(f"✗  (validation failed after {max_validation_retries} retries: missing {missing_str})")
                                    consecutive_scrape_failures += 1
                                else:
                                    time.sleep(1)  # Brief pause before retry
                        else:
                            success = True
                            break
                            
                    except Exception as e:
                        retry_count += 1
                        if retry_count > (max_validation_retries if not args.no_retry else 0):
                            print(f"✗  (scraping failed after {retry_count} attempts)")
                            print(f"{' ' * (max_index_width + 4 + 16)}   Error: {e}")
                            consecutive_scrape_failures += 1
                        else:
                            time.sleep(1)
                
                if success and rec:
                    batch_results.append(rec)
                    existing_ids.add(tid)  # Mark as scraped
                    total_scraped += 1
                    consecutive_scrape_failures = 0
                    print("✓")
                    
                    # Save batch
                    if len(batch_results) >= args.batch_size:
                        print(f"\n📦 Batch complete ({args.batch_size} titles), saving...")
                        append_outputs(batch_results, out_prefix, existing_records)
                        existing_records.extend(batch_results)
                        batch_results = []
                        print()  # Empty line after saving
                
                time.sleep(args.delay + random.uniform(0.5, 1.2))
        
        # Save any remaining records
        if batch_results:
            print(f"\n💾 Saving final batch ({len(batch_results)} titles)...")
            append_outputs(batch_results, out_prefix, existing_records)
        
        print(f"\n✅ Crawling complete! Total scraped: {total_scraped} titles")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user!")
        if batch_results:
            print(f"   Saving {len(batch_results)} titles from current batch...")
            append_outputs(batch_results, out_prefix, existing_records)
        print("   Progress saved. You can resume with --resume flag.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()