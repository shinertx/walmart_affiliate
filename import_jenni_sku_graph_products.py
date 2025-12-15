import sys
import os
from pathlib import Path
import time
import ssl
import certifi
from urllib.parse import urljoin
from typing import Any, Optional
from functools import partial

import json

import requests
from dotenv import load_dotenv
import shopify


# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

# Fix SSL Context for Shopify API
ssl_context = ssl.create_default_context(cafile=certifi.where())
import urllib.request

original_urlopen = urllib.request.urlopen


def patched_urlopen(url, data=None, timeout=None, *, cafile=None, capath=None, cadefault=False, context=None):
    return original_urlopen(url, data, timeout, context=ssl_context)


urllib.request.urlopen = patched_urlopen


SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = "2024-01"


def _env_truthy(name: str, default: str = "false") -> bool:
    v = (os.getenv(name, default) or "").strip().lower()
    return v in ("1", "true", "t", "yes", "y", "on")


def _jenni_page_size_from_limit(limit: int) -> int:
    """Jenni API only allows page_size enum values."""
    limit = int(limit)
    if limit <= 10:
        return 10
    if limit <= 20:
        return 20
    if limit <= 50:
        return 50
    return 100


def _shopify_rest_headers() -> dict[str, str]:
    if not SHOPIFY_ACCESS_TOKEN:
        raise ValueError("SHOPIFY_ACCESS_TOKEN missing")
    return {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }


    print = partial(print, flush=True)  # type: ignore[assignment]

def _shopify_rest_base_url() -> str:
    if not SHOPIFY_STORE_URL:
        raise ValueError("SHOPIFY_STORE_URL missing")
    return f"https://{SHOPIFY_STORE_URL}/admin/api/{SHOPIFY_API_VERSION}"


def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in {"1", "true", "yes", "y"}


def _split_shopify_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def _merge_shopify_tags(*, existing: str | None, desired: str) -> str:
    ex = set(_split_shopify_tags(existing))
    want = set(_split_shopify_tags(desired))
    merged = list(ex.union(want))
    merged.sort(key=lambda s: s.lower())
    return ", ".join(merged)


def _coerce_price(value) -> str | None:
    """Coerce SKU Graph price-like values into Shopify-compatible strings.

    Shopify expects a string decimal (e.g. "19.99").
    Returns None when value is missing/unparseable.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return f"{float(value):.2f}"
        except Exception:
            return None
    s = str(value).strip()
    if not s:
        return None
    # tolerate "$12.34"-like strings
    if s.startswith("$"):
        s = s[1:].strip()
    try:
        return f"{float(s):.2f}"
    except Exception:
        return None


def _pick_sku_graph_price(p: dict) -> str | None:
    """Select the best price from a normalized SKU Graph product."""
    # Prefer Jenni's price when present; fall back to the generic price.
    return _coerce_price(p.get("jenni_price")) or _coerce_price(p.get("price"))


def _find_shopify_product_by_gtin(*, gtin: str, jenni_tag: str) -> shopify.Product | None:
    """Lookup existing Shopify product by GTIN (variant sku or barcode), scoped to Jenni-tagged products.

    We match any of:
    - variant.sku == gtin
    - variant.barcode == gtin
    - legacy variant.sku == f"JN_{gtin}" (older imports)

    This is intentionally **scoped** so we don't have to scan the whole store.
    We use the REST Admin API because it supports `?tag=` filtering.
    """
    gtin = (gtin or "").strip()
    if not gtin:
        return None

    url = f"{_shopify_rest_base_url()}/products.json"
    params = {"limit": 250, "fields": "id,tags,variants" , "tag": jenni_tag}
    legacy_sku = f"JN_{gtin}"

    while True:
        try:
            r = requests.get(url, headers=_shopify_rest_headers(), params=params, timeout=15)
        except Exception:
            return None
        if r.status_code != 200:
            return None
        data = r.json() or {}
        for p in data.get("products", []) or []:
            for v in p.get("variants", []) or []:
                sku = str(v.get("sku") or "").strip()
                barcode = str(v.get("barcode") or "").strip()
                if sku in {gtin, legacy_sku} or barcode == gtin:
                    try:
                        return shopify.Product.find(p["id"])
                    except Exception:
                        return None

        link = r.headers.get("Link")
        next_url = None
        if link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip("<> ")
                    break
        if not next_url:
            return None
        url = next_url
        params = None  # already encoded in next_url


# Backwards-compatible alias (older call sites used _find_shopify_product_by_sku)
def _find_shopify_product_by_sku(*, product_id: str, jenni_tag: str) -> shopify.Product | None:
    return _find_shopify_product_by_gtin(gtin=product_id, jenni_tag=jenni_tag)


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise ValueError(f"Missing required env var: {name}")
    return val


def _sg_headers() -> dict[str, str]:
    api_key = os.getenv("LOCALSTOCK_CHROME_EXTENSION_API_KEY") or os.getenv("LOCALSTOCK_INGESTION_API_KEY")
    if not api_key:
        raise ValueError(
            "Set LOCALSTOCK_CHROME_EXTENSION_API_KEY (preferred) or LOCALSTOCK_INGESTION_API_KEY so we can call the SKU Graph API."
        )
    # sku_graph_backend/app/api/security.py uses an API key requirement for most endpoints.
    # Historically this is passed as X-API-Key.
    return {"X-API-Key": api_key}


def _sg_get_json(url: str, *, params: dict | None = None, timeout_s: float = 10.0) -> dict:
    r = requests.get(url, headers=_sg_headers(), params=params, timeout=timeout_s)
    r.raise_for_status()
    return r.json()


# ---------------------------
# Production Jenni SKU Graph API (bearer token)
# ---------------------------


def _prod_base_url() -> str:
    # IMPORTANT:
    # The Swagger UI is hosted under:
    #   https://sku-graph.jennipro.net/api/sku-graph/product-availability-service/docs
    # But the actual endpoint paths are rooted at that host/path prefix (e.g. /searchProducts/).
    # We build URLs using this OpenAPI base.
    return os.getenv(
        "JENNI_SKU_GRAPH_PROD_OPENAPI_BASE_URL",
        "https://sku-graph.jennipro.net/api/sku-graph/product-availability-service",
    ).rstrip("/")


def _prod_api_root() -> str:
    """Return the root URL where endpoints like /auth/token and /searchProducts/ live."""
    # Example openapi lives at:
    #   https://sku-graph.jennipro.net/api/sku-graph/product-availability-service/openapi.json
    # And paths are:
    #   /auth/token
    #   /getList/
    #   /searchProducts/
    # which are effectively rooted at:
    #   https://sku-graph.jennipro.net (server) + /api/sku-graph/product-availability-service (prefix)
    base = _prod_base_url()
    return base


def _prod_auth_token() -> str:
    root = _prod_api_root()
    # Support both the "direct importer" env vars and the LocalStock backend naming.
    # This helps when you already have LOCALSTOCK_JENNI_CLIENT_* configured.
    client_id = os.getenv("JENNI_SKU_GRAPH_CLIENT_ID") or os.getenv("LOCALSTOCK_JENNI_CLIENT_ID")
    client_secret = os.getenv("JENNI_SKU_GRAPH_CLIENT_SECRET") or os.getenv("LOCALSTOCK_JENNI_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "Set JENNI_SKU_GRAPH_CLIENT_ID/JENNI_SKU_GRAPH_CLIENT_SECRET (preferred) "
            "or LOCALSTOCK_JENNI_CLIENT_ID/LOCALSTOCK_JENNI_CLIENT_SECRET to use the production SKU Graph API"
        )
    r = requests.post(
    f"{root}/auth/token",
        json={"client_id": str(client_id), "client_secret": str(client_secret)},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json() or {}
    tok = data.get("access_token")
    if not tok:
        raise ValueError("Production SKU Graph auth succeeded but no access_token returned")
    return str(tok)


def _prod_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _checkpoint_path() -> Path:
    # Keep resumable state local to this repo.
    return Path(os.getenv("JENNI_CHECKPOINT_FILE", "logs/jenni_import_checkpoint.json")).expanduser()


def _load_checkpoint() -> dict:
    p = _checkpoint_path()
    try:
        if p.exists():
            return json.loads(p.read_text()) or {}
    except Exception:
        return {}
    return {}


def _save_checkpoint(state: dict) -> None:
    p = _checkpoint_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, indent=2, sort_keys=True))
    except Exception:
        # checkpoint is best-effort
        pass


def _jenni_progress_path() -> Path:
    # Separate from the resume checkpoint; designed for dashboards.
    return Path(os.getenv("JENNI_PROGRESS_FILE", "results/jenni_progress.json")).expanduser()


def _write_jenni_progress(state: dict) -> None:
    """Best-effort progress file for monitoring/dashboards."""
    try:
        p = _jenni_progress_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(state or {})
        payload["updated_at"] = time.time()
        p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def _jenni_lock_path() -> Path:
    return Path(os.getenv("JENNI_LOCK_FILE", "results/jenni_import.lock")).expanduser()


def _acquire_jenni_lock() -> None:
    """Prevent multiple concurrent importer instances.

    Best-effort safety: if the lock exists and the PID is alive, we exit.
    """
    p = _jenni_lock_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()

    if p.exists():
        try:
            old_pid_s = (p.read_text(encoding="utf-8") or "").strip()
            old_pid = int(old_pid_s) if old_pid_s.isdigit() else None
        except Exception:
            old_pid = None

        if old_pid:
            try:
                os.kill(old_pid, 0)
                print(f"Error: Jenni importer already running (pid={old_pid}). Lock: {p}")
                raise SystemExit(2)
            except ProcessLookupError:
                # stale lock
                pass
            except PermissionError:
                # Can't verify; play it safe.
                print(f"Error: Jenni importer lock exists but can't verify pid. Lock: {p}")
                raise SystemExit(2)
            except Exception:
                # Unknown; play it safe.
                print(f"Error: Jenni importer lock exists. Lock: {p}")
                raise SystemExit(2)

    p.write_text(str(pid), encoding="utf-8")


def _release_jenni_lock() -> None:
    try:
        p = _jenni_lock_path()
        if p.exists():
            p.unlink()
    except Exception:
        pass


def _is_shopify_rate_limited(exc: Exception) -> bool:
    msg = str(exc)
    return (
        "Response(code=429" in msg
        or "HTTP Error 429" in msg
        or "Too Many Requests" in msg
        or "Daily variant creation limit reached" in msg
    )


def _shopify_save_with_backoff(resource, *, max_attempts: int, base_sleep_s: float, max_sleep_s: float, description: str) -> bool:
    """Save a Shopify resource with exponential backoff on 429s.

    We specifically handle Shopify's API call limit and the 'Daily variant creation limit reached' error.
    """
    attempt = 1
    sleep_s = base_sleep_s
    while True:
        try:
            return bool(resource.save())
        except Exception as e:
            if not _is_shopify_rate_limited(e):
                raise
            if attempt >= max_attempts:
                print(f"❌ Shopify rate limited too long while saving {description}. Giving up after {attempt} attempts.")
                return False

            print(f"⏳ Shopify rate limited while saving {description}. Sleeping {sleep_s:.1f}s then retrying (attempt {attempt}/{max_attempts})")
            time.sleep(sleep_s)
            sleep_s = min(max_sleep_s, sleep_s * 2)
            attempt += 1


def prod_list_categories() -> list[str]:
    root = _prod_api_root()
    token = _prod_auth_token()
    r = requests.get(f"{root}/getList/?type=category", headers=_prod_headers(token), timeout=20)
    r.raise_for_status()
    data = r.json() or {}
    cats = data.get("categories")
    if not isinstance(cats, list):
        return []
    return [str(c).strip() for c in cats if str(c).strip()]


def prod_list_brands() -> list[str]:
    root = _prod_api_root()
    token = _prod_auth_token()
    r = requests.get(f"{root}/getList/?type=brand", headers=_prod_headers(token), timeout=30)
    r.raise_for_status()
    data = r.json() or {}
    brands = data.get("brands")
    if not isinstance(brands, list):
        return []
    return [str(b).strip() for b in brands if str(b).strip()]


def prod_search_products_by_brand(*, brand: str, limit: int, page: int) -> dict:
    """Return raw response for a brand search.

    Response shape (observed):
      { total_products: int, total_pages: int, products: [...] }
    """
    root = _prod_api_root()
    token = _prod_auth_token()
    # Jenni is zip-sensitive. Use env override when provided; otherwise default to a known-working TX zip.
    zip_code = (os.getenv("JENNI_ZIP") or "75034").strip()
    page_size = _jenni_page_size_from_limit(limit)

    payload: dict = {
        "brand": brand,
        "zip": zip_code,
        "category": "",
        "gtin": "",
        "max_price": int(os.getenv("JENNI_MAX_PRICE", "0")),
        "page": page,
        "page_size": page_size,
        "source": (os.getenv("JENNI_SOURCE_FLAG", "no") or "no").strip(),
    }

    r = requests.post(f"{root}/searchProducts/", json=payload, headers=_prod_headers(token), timeout=45)
    if r.status_code == 404:
        return {"total_products": 0, "products": []}
    r.raise_for_status()
    data = r.json() or {}
    # Always return the raw response dict so callers can access total_products/total_pages.
    if not isinstance(data, dict):
        return {"total_products": 0, "products": []}
    return data


def prod_extract_products(resp: dict) -> list[dict]:
    """Best-effort: extract product list from a prod search response."""
    products = resp.get("products") if isinstance(resp, dict) else None
    if isinstance(products, list):
        return [p for p in products if isinstance(p, dict)]
    return []


def prod_search_products_v2(
    *,
    zip_code: Optional[str] = None,
    brand: str = "",
    category: str = "",
    gtin: str = "",
    max_price: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
    source_flag: Optional[str] = None,
) -> dict:
    """Prod search via `searchProducts_v2`.

    Key capability: supports paging with *no brand/category filters*, which lets us enumerate
    the full prod catalog for a given zip.
    """
    root = _prod_api_root()
    token = _prod_auth_token()

    zip_code = (zip_code or os.getenv("JENNI_ZIP") or "75034").strip()
    source = (source_flag or os.getenv("JENNI_SOURCE_FLAG") or "no").strip()

    page_size = _jenni_page_size_from_limit(limit)

    payload: dict = {
        "brand": brand or "",
        "zip": zip_code,
        "category": category or "",
        "gtin": gtin or "",
        "max_price": int(max_price or os.getenv("JENNI_MAX_PRICE", "0")),
        "page": int(page),
        "page_size": page_size,
        "source": source,
    }

    r = requests.post(f"{root}/searchProducts_v2/", json=payload, headers=_prod_headers(token), timeout=45)
    if r.status_code == 404:
        return {"total_products": 0, "products": []}
    r.raise_for_status()
    data = r.json() or {}
    if not isinstance(data, dict):
        return {"total_products": 0, "products": []}
    return data


def prod_iter_catalog_v2(
    *,
    zips: list[str],
    limit: int = 50,
    max_items: Optional[int] = None,
    checkpoint_path: Optional[str] = None,
    brand: str = "",
    category: str = "",
) -> list[dict]:
    """Enumerate Jenni prod catalog via `searchProducts_v2`.

    This is the main workaround to get "100%" of products: since availability varies by zip,
    we iterate over a *set* of zips and de-dupe by `jenni_parent_id`.

    Checkpoint format (json): {"zip": "75034", "page": 12}
    """
    zips = [str(z).strip() for z in (zips or []) if str(z).strip()]
    if not zips:
        zips = [(os.getenv("JENNI_ZIP") or "75034").strip()]

    checkpoint_path = checkpoint_path or os.getenv("JENNI_CHECKPOINT_PATH")
    start_zip = zips[0]
    start_page = 1
    if checkpoint_path:
        try:
            if os.path.exists(checkpoint_path):
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    ck = json.load(f)
                if isinstance(ck, dict):
                    start_zip = str(ck.get("zip") or start_zip)
                    start_page = int(ck.get("page") or 1)
        except Exception:
            # checkpoint is a convenience; never block enumeration
            start_zip, start_page = zips[0], 1

    seen_parent_ids: set[str] = set()
    out: list[dict] = []

    for z in zips:
        page = start_page if z == start_zip else 1
        while True:
            resp = prod_search_products_v2(zip_code=z, brand=brand, category=category, page=page, limit=limit)
            total_pages = resp.get("total_pages") if isinstance(resp, dict) else None
            products = prod_extract_products(resp)

            if not products:
                break

            for p in products:
                pid = p.get("jenni_parent_id") or p.get("jenni_product_id")
                pid = str(pid) if pid is not None else ""
                if pid and pid in seen_parent_ids:
                    continue
                if pid:
                    seen_parent_ids.add(pid)
                # attach which zip we saw it in (useful for debugging/availability)
                p["_seen_zip"] = z
                out.append(p)
                if max_items and len(out) >= int(max_items):
                    return out

            # checkpoint after each successful page
            if checkpoint_path:
                try:
                    os.makedirs(os.path.dirname(checkpoint_path) or ".", exist_ok=True)
                    with open(checkpoint_path, "w", encoding="utf-8") as f:
                        json.dump({"zip": z, "page": page + 1}, f)
                except Exception:
                    pass

            if isinstance(total_pages, int) and page >= total_pages:
                break
            page += 1

        # reset start_page after first zip is completed
        start_page = 1

    return out


def build_gtin_index(
    products: list[dict],
    *,
    include_seen_zips: bool = True,
) -> dict[str, dict]:
    """Build a global GTIN index from prod products.

    Jenni's true SKU identity is GTIN (variant-level). This collapses variants across zips
    into a single record per GTIN while preserving parent grouping metadata.
    """
    gtins: dict[str, dict] = {}

    for p in products:
        if not isinstance(p, dict):
            continue
        parent_id = p.get("jenni_parent_id") or p.get("jenni_product_id")
        parent_id = str(parent_id) if parent_id is not None else ""
        seen_zip = str(p.get("_seen_zip") or "").strip()

        for v in (p.get("variants") or []):
            if not isinstance(v, dict):
                continue
            gtin = v.get("gtin")
            if gtin is None:
                continue
            gtin_s = str(gtin).strip()
            if not gtin_s:
                continue

            rec = gtins.get(gtin_s)
            if rec is None:
                rec = {
                    "gtin": gtin_s,
                    "jenni_parent_id": parent_id,
                    "title": p.get("title"),
                    "brand": p.get("brand"),
                    "category": p.get("category"),
                    "image_urls": p.get("image_urls") or p.get("images") or [],
                    "variant": v,
                    "seen_in_zips": [],
                }
                gtins[gtin_s] = rec

            # Prefer a record that has richer fields (title/images) if current one is sparse
            if not rec.get("title") and p.get("title"):
                rec["title"] = p.get("title")
            if not rec.get("brand") and p.get("brand"):
                rec["brand"] = p.get("brand")
            if not rec.get("category") and p.get("category"):
                rec["category"] = p.get("category")
            if (not rec.get("image_urls")) and (p.get("image_urls") or p.get("images")):
                rec["image_urls"] = p.get("image_urls") or p.get("images")
            if not rec.get("jenni_parent_id") and parent_id:
                rec["jenni_parent_id"] = parent_id

            if include_seen_zips and seen_zip:
                zlist = rec.get("seen_in_zips")
                if isinstance(zlist, list) and seen_zip not in zlist:
                    zlist.append(seen_zip)

    return gtins


def write_gtin_index_json(
    *,
    products: list[dict],
    out_path: str,
    zips: Optional[list[str]] = None,
) -> None:
    """Write a GTIN-keyed export to disk for deterministic imports."""
    idx = build_gtin_index(products)
    payload = {
        "zips": zips or [],
        "counts": {
            "unique_gtins": len(idx),
        },
        "gtins": idx,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _normalize_prod_product(p: dict, category: str) -> dict:
    """Map remote SKU Graph product to our internal minimal shape."""
    title = p.get("title") or p.get("name") or p.get("product_name")
    brand = p.get("brand") or p.get("manufacturer")
    # Production response nests real sellable items under variants.
    variants = p.get("variants") if isinstance(p.get("variants"), list) else []
    v0 = variants[0] if variants else {}
    gtin = v0.get("gtin") or p.get("gtin") or p.get("upc") or p.get("barcode")
    url = p.get("url") or p.get("product_url") or p.get("link")
    # Prefer jenni_product_id if present.
    product_id = v0.get("jenni_product_id") or p.get("jenni_parent_id") or p.get("product_id") or p.get("id")
    # Images can appear at product-level and/or on each variant. Union + de-dupe.
    images_set: set[str] = set()
    if isinstance(p.get("images"), list):
        for u in p.get("images"):
            if u and str(u).strip():
                images_set.add(str(u).strip())
    for v in variants:
        if isinstance(v, dict) and isinstance(v.get("images"), list):
            for u in v.get("images"):
                if u and str(u).strip():
                    images_set.add(str(u).strip())
    images = sorted(images_set)
    price = v0.get("price") or p.get("price")
    jenni_price = v0.get("jenni_price") or p.get("jenni_price")
    return {
        "product_id": str(product_id) if product_id else "",
        "title": str(title) if title else "",
        "brand": str(brand) if brand else None,
        "gtin": str(gtin) if gtin else "",
        "url": str(url) if url else "",
        "category": category,
        "images": images,
        "description": str(p.get("description") or "") if p.get("description") else "",
        "html_description": str(p.get("html_description") or "") if p.get("html_description") else "",
        "price": price,
        "jenni_price": jenni_price,
    }


def list_categories(base_url: str) -> list[str]:
    url = urljoin(base_url.rstrip("/") + "/", "api/catalog/categories")
    payload = _sg_get_json(url)
    cats = payload.get("categories")
    if not isinstance(cats, list):
        return []
    return [str(c).strip() for c in cats if str(c).strip()]


def iter_products(base_url: str, *, category: str | None, limit: int, max_items: int | None) -> list[dict]:
    url = urljoin(base_url.rstrip("/") + "/", "api/catalog/products")
    offset = 0
    out: list[dict] = []

    while True:
        params = {"limit": limit, "offset": offset, "include_attrs": "false"}
        if category:
            params["category"] = category

        payload = _sg_get_json(url, params=params)
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return out

        for it in items:
            if not isinstance(it, dict):
                continue
            out.append(it)
            if max_items is not None and len(out) >= max_items:
                return out

        offset += limit


def create_jenni_product(*, p: dict, tags: str, product_type: str, vendor: str, inventory: int, dry_run: bool) -> bool:
    title = (p.get("title") or "").strip()
    if not title:
        return False

    # Jenni SKU identity is GTIN (variant-level). We still store the Jenni parent/product id
    # in metafields for lookup/debugging, but SKU + barcode should be the raw GTIN.
    product_id = (p.get("product_id") or "").strip()
    gtin = (p.get("gtin") or "").strip()
    source_url = (p.get("url") or "").strip()
    category = (p.get("category") or "").strip()
    sku_graph_price = _pick_sku_graph_price(p)

    # Content fields (Jenni v2 provides these; we map them into Shopify).
    html_description = (p.get("html_description") or "").strip()
    plain_description = (p.get("description") or "").strip()
    body_html = html_description or (plain_description.replace("\n", "<br>") if plain_description else "")

    images: list[str] = []
    raw_images = p.get("images")
    if isinstance(raw_images, list):
        # De-dupe while preserving order.
        seen: set[str] = set()
        for u in raw_images:
            su = str(u).strip() if u else ""
            if not su or su in seen:
                continue
            seen.add(su)
            images.append(su)

    # Always add a normalized Jenni category tag, so Smart Collections can route cleanly.
    # This stays stable even if product_type changes later.
    normalized_category = " ".join(category.split())
    if normalized_category:
        category_tag = f"JenniCategory:{normalized_category}"
        tags = _merge_shopify_tags(existing=tags, desired=category_tag)

        # Walmart importer also includes the category name directly in tags; keep that parity.
        tags = _merge_shopify_tags(existing=tags, desired=normalized_category)

    if dry_run:
        # Don't touch Shopify at all in dry-run mode.
        print(
            f"[DRY RUN] Would import Jenni: {title[:60]}... "
            f"sku={gtin} barcode={gtin} product_type={normalized_category or product_type} "
            f"tags={tags} price={sku_graph_price or '0.00'} inv={inventory}"
        )
        return True

    # Upsert is nice for re-runs, but it can be slow on huge stores.
    # Allow disabling lookups for fastest initial push.
    enable_upsert = _bool_env("JENNI_UPSERT", "true")

    # Use the source tag as the scoping tag for lookup.
    # Keep it stable even if user adds additional tags.
    jenni_tag = "Source:JenniSKUGraph"
    existing = None
    if enable_upsert and gtin:
        existing = _find_shopify_product_by_sku(product_id=gtin, jenni_tag=jenni_tag)

    # Backoff settings for the Shopify Admin API.
    # Note: Shopify has both per-minute call limits AND per-day variant creation limits on some plans.
    # We handle both by backing off and retrying, rather than crashing.
    max_save_attempts = int(os.getenv("SHOPIFY_SAVE_MAX_ATTEMPTS", "12"))
    base_sleep_s = float(os.getenv("SHOPIFY_SAVE_BACKOFF_SECONDS", "2"))
    max_sleep_s = float(os.getenv("SHOPIFY_SAVE_BACKOFF_MAX_SECONDS", "900"))

    if existing is not None:
        # Update in-place (idempotent): tags + inventory + metafields
        product = existing
        product.tags = _merge_shopify_tags(existing=getattr(product, "tags", None), desired=tags)
        # Keep title/vendor/product_type consistent
        product.title = title
        product.vendor = vendor
        # Ensure product_type is set (Smart Collections often rely on this).
        product.product_type = normalized_category or product_type
        product.status = "active"

        # Backfill content if missing (avoid clobbering merchant-edited content).
        existing_body = (getattr(product, "body_html", None) or "").strip()
        if not existing_body and body_html:
            product.body_html = body_html

        # Backfill images only if the product currently has none.
        try:
            existing_images = getattr(product, "images", None) or []
        except Exception:
            existing_images = []
        if (not existing_images) and images:
            product.images = [{"src": u} for u in images]

        # Update the first variant (we create single-variant products)
        try:
            variant = (getattr(product, "variants", None) or [None])[0]
        except Exception:
            variant = None
        if variant is None:
            variant = shopify.Variant()
            product.variants = [variant]

        # Don't overwrite price if it was set later (leave as-is if present).
        if sku_graph_price:
            variant.price = sku_graph_price
        elif getattr(variant, "price", None) in (None, ""):
            variant.price = "0.00"
        if gtin:
            variant.sku = gtin
            variant.barcode = gtin
        variant.inventory_management = "shopify"
        variant.inventory_policy = "deny"
        variant.inventory_quantity = int(inventory)

        if _shopify_save_with_backoff(
            product,
            max_attempts=max_save_attempts,
            base_sleep_s=base_sleep_s,
            max_sleep_s=max_sleep_s,
            description=f"update sku={gtin}",
        ):
            print(f"✅ Updated Jenni: {title[:60]}... sku={gtin} inv={inventory}")
            return True

        print(f"❌ Failed to update Jenni product: {title[:60]}...")
        return False

    # Create new
    product = shopify.Product()
    product.title = title
    product.body_html = body_html
    product.vendor = vendor
    product.product_type = normalized_category or product_type
    product.tags = tags
    product.status = "active"

    if images:
        product.images = [{"src": u} for u in images]

    variant = shopify.Variant()
    # Shopify requires a price; use SKU Graph price when available.
    variant.price = sku_graph_price or "0.00"
    if gtin:
        variant.sku = gtin
        variant.barcode = gtin
    variant.inventory_management = "shopify"
    variant.inventory_policy = "deny"
    variant.inventory_quantity = int(inventory)
    product.variants = [variant]

    metafields = []
    if product_id:
        metafields.append(
            {
                "namespace": "jenni",
                "key": "product_id",
                "value": product_id,
                "type": "single_line_text_field",
            }
        )
    if gtin:
        metafields.append(
            {
                "namespace": "jenni",
                "key": "gtin",
                "value": gtin,
                "type": "single_line_text_field",
            }
        )
    if source_url:
        metafields.append(
            {
                "namespace": "jenni",
                "key": "product_url",
                "value": source_url,
                "type": "single_line_text_field",
            }
        )
    if category:
        metafields.append(
            {
                "namespace": "jenni",
                "key": "category",
                "value": category,
                "type": "single_line_text_field",
            }
        )
    if metafields:
        product.metafields = metafields

    if _shopify_save_with_backoff(
        product,
        max_attempts=max_save_attempts,
        base_sleep_s=base_sleep_s,
        max_sleep_s=max_sleep_s,
        description=f"create sku={variant.sku}",
    ):
        print(f"✅ Imported Jenni: {title[:60]}... sku={variant.sku} barcode={variant.barcode} inv={inventory}")
        return True

    print(f"❌ Failed to save Jenni product: {title[:60]}...")
    return False


def main() -> int:
    _acquire_jenni_lock()
    try:
        if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
            print("Error: Shopify credentials missing.")
            return 1

        # NOTE:
        # This importer supports two modes:
        #   - JENNI_SOURCE_MODE=prod (recommended): calls the public Jenni SKU Graph API
        #   - JENNI_SOURCE_MODE=local: calls a locally-running sku_graph_backend instance
        #
        # Historically we defaulted SKU_GRAPH_BASE_URL to localhost:8000, which is easy to
        # accidentally hit. We now require an explicit base URL for local mode.
        sku_graph_base_url = (os.getenv("SKU_GRAPH_BASE_URL") or "").strip()
        dry_run = _bool_env("DRY_RUN", "true")
        inventory = int(os.getenv("JENNI_INVENTORY", "50"))
        limit = int(os.getenv("JENNI_PAGE_SIZE", "100"))
        max_items = os.getenv("JENNI_MAX_ITEMS")
        max_items_n = int(max_items) if max_items and max_items.strip().isdigit() else None

        category_filter = (os.getenv("JENNI_CATEGORY") or "").strip() or None
        import_all_categories = _bool_env("JENNI_IMPORT_ALL_CATEGORIES", "true")

    # Choose source mode:
    # - local: uses our local sku_graph_backend /api/catalog/* endpoints
    # - prod: uses jennipro.net product-availability-service endpoints
        source_mode = (os.getenv("JENNI_SOURCE_MODE", "prod") or "prod").strip().lower()

        if source_mode == "local" and not sku_graph_base_url:
            print(
                "Error: JENNI_SOURCE_MODE=local requires SKU_GRAPH_BASE_URL to be set (e.g. http://localhost:8080).\n"
                "If you're trying to use the public Jenni site, set JENNI_SOURCE_MODE=prod instead."
            )
            return 1

    # Resume support (best-effort): we checkpoint the last processed brand/page and a rolling set of processed product_ids.
        resume_enabled = _bool_env("JENNI_RESUME", "true")
        checkpoint = _load_checkpoint() if resume_enabled else {}

        vendor = os.getenv("JENNI_VENDOR", "Jenni SKU Graph")
        product_type_default = os.getenv("JENNI_PRODUCT_TYPE", "Jenni")
        tags = os.getenv("JENNI_TAGS", "Source:JenniSKUGraph, Jenni-SKU-Graph")

    # Initialize Shopify session
        session = shopify.Session(SHOPIFY_STORE_URL, SHOPIFY_API_VERSION, SHOPIFY_ACCESS_TOKEN)
        shopify.ShopifyResource.activate_session(session)

        categories: list[str] = []
        if category_filter:
            categories = [category_filter]
        elif import_all_categories:
            if source_mode == "prod":
                categories = prod_list_categories()
            else:
                categories = list_categories(sku_graph_base_url)
            if not categories:
                # If category extraction isn't populated yet, still import "uncategorized" items.
                categories = [None]  # type: ignore[list-item]
        else:
            categories = [None]  # type: ignore[list-item]

        imported = 0

        if source_mode == "prod":
            # Production API is availability-by-zip. For "100%" coverage we must union across zips.
            # Strategy:
            #   1) enumerate via searchProducts_v2 with brand/category empty (paged)
            #   2) iterate a ZIP coverage set (Dallas/Houston/San Antonio/Austin anchors)
            #   3) de-dupe at GTIN level (Jenni SKU = GTIN)
            #
            # Configure coverage zips:
            #   - JENNI_ZIPS="78216,75034,..." (comma-separated)
            #   - default: a proven TX metro anchor set
            zips_env = (os.getenv("JENNI_ZIPS") or "").strip()
            if zips_env:
                zips = [z.strip() for z in zips_env.split(",") if z.strip()]
            else:
                zips = [
                "78216",
                "75034",
                "76051",
                "77024",
                "78746",
                "77040",
                "78701",
                "75080",
                "78745",
                "78257",
                "75024",
                "78704",
                "78230",
                "77057",
                "75093",
                "77027",
                "75230",
                "78759",
                "77007",
                "77063",
                ]

            # We checkpoint paging at the product-level enumerator; keep a lightweight GTIN seen set here.
            seen_gtins: set[str] = set(checkpoint.get("seen_gtins", []) or [])
            processed = 0

            # Enumerate raw prod products (parents). prod_iter_catalog_v2 already de-dupes by parent.
            raw_products = prod_iter_catalog_v2(
                zips=zips,
                limit=limit,
                max_items=max_items_n,
                checkpoint_path=os.getenv("JENNI_CHECKPOINT_PATH")
                or str(Path(__file__).with_suffix(".jenni_prod_ckpt.json")),
            )

            for raw in raw_products:
                if not isinstance(raw, dict):
                    continue
                cat = (raw.get("category") or "").strip() or "Uncategorized"
                if category_filter and cat.lower() != category_filter.lower():
                    continue

                # Deduplicate at GTIN level (Jenni SKU identity)
                variants = raw.get("variants") if isinstance(raw.get("variants"), list) else []
                keep = False
                for v in variants:
                    if not isinstance(v, dict):
                        continue
                    gtin = str(v.get("gtin") or "").strip()
                    if not gtin:
                        continue
                    if gtin in seen_gtins:
                        continue
                    seen_gtins.add(gtin)
                    keep = True
                if not keep:
                    continue

                p = _normalize_prod_product(raw, cat)
                if create_jenni_product(
                    p=p,
                    tags=tags,
                    product_type=product_type_default,
                    vendor=vendor,
                    inventory=inventory,
                    dry_run=dry_run,
                ):
                    imported += 1
                    last_heartbeat_s = time.time()

            processed += 1
            # Periodically checkpoint progress so the run can resume.
            if resume_enabled:
                checkpoint_state = {
                    "source_mode": source_mode,
                    "seen_gtins": list(seen_gtins)[-50000:],
                    "imported": imported,
                    "processed": processed,
                    "zips": zips,
                }
                _save_checkpoint(checkpoint_state)
                _write_jenni_progress(
                    {
                        "source_mode": source_mode,
                        "imported": imported,
                        "processed": processed,
                        "unique_gtins": len(seen_gtins),
                        "zips": zips,
                    }
                )

            # Heartbeat so long runs are observable even if upstream is slow.
            hb_every_s = float(os.getenv("JENNI_LOG_EVERY_SECONDS", "30"))
            now = time.time()
            if now - last_heartbeat_s >= hb_every_s:
                print(f"[jenni] progress imported={imported} processed={processed} unique_gtins={len(seen_gtins)}")
                _write_jenni_progress(
                    {
                        "source_mode": source_mode,
                        "imported": imported,
                        "processed": processed,
                        "unique_gtins": len(seen_gtins),
                        "zips": zips,
                    }
                )
                last_heartbeat_s = now
                time.sleep(0.25)

        else:
            for cat in categories:
                cat_name = cat if isinstance(cat, str) else None
                products = iter_products(
                    sku_graph_base_url,
                    category=cat_name,
                    limit=limit,
                    max_items=max_items_n,
                )
                if not products:
                    continue
                for p in products:
                    if create_jenni_product(
                        p=p,
                        tags=tags,
                        product_type=product_type_default,
                        vendor=vendor,
                        inventory=inventory,
                        dry_run=dry_run,
                    ):
                        imported += 1
                    time.sleep(0.25)

        print(f"\nDone. Imported {imported} Jenni product(s). Dry run: {dry_run}")
        return 0

    finally:
        _release_jenni_lock()


if __name__ == "__main__":
    raise SystemExit(main())
