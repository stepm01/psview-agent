import re, socket, ipaddress
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

def is_url(s: str) -> bool:
    s = s.strip()
    return bool(re.match(r"^https?://", s, re.I)) or bool(re.match(r"^[\w.-]+\.[a-z]{2,}(/|$)", s, re.I))

def _safe_host(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except Exception:
        pass
    return True

def fetch_company_text(url: str, max_chars: int = 1500) -> str:
    if not url.lower().startswith("http"):
        url = "https://" + url
    if urlparse(url).scheme not in ("http", "https") or not _safe_host(url):
        return ""
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0 (compatible; EngagementAgent/1.0)"})
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        parts = []
        if soup.title and soup.title.string:
            parts.append(soup.title.string.strip())
        for name, attrs in [("meta", {"name": "description"}), ("meta", {"property": "og:description"}),
                            ("meta", {"property": "og:title"}), ("meta", {"property": "og:site_name"})]:
            tag = soup.find(name, attrs=attrs)
            if tag and tag.get("content"):
                parts.append(tag["content"].strip())
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        text = " ".join(soup.get_text(" ").split())
        if text:
            parts.append(text[:max_chars])
        return "\n".join(parts).strip()
    except Exception:
        return ""