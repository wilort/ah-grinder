"""Refresh the item information catalog for WoW Forever."""

import gzip
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests

from download_forever_auctions import create_access_token


PROJECT_DIR = Path(__file__).resolve().parent
API_ROOT = "https://eu.api.blizzard.com/data/wow"
FOREVER_NAMESPACE = "static-forever-eu"
CLASSIC_NAMESPACE = "static-classic1x-eu"
MARKET_KEY = "eu-2-110"
MARKET_URL = f"https://auctionhouse.tk.gg/api/m/{MARKET_KEY}"
LOCALE = "en_US"


def get_item_data(session, route, namespace=FOREVER_NAMESPACE, **params):
    return session.get(
        f"{API_ROOT}/{route}",
        params={"namespace": namespace, "locale": LOCALE, **params},
        timeout=30,
    )


def localized_name(name):
    if isinstance(name, dict):
        return name.get(LOCALE) or name.get("en_GB")
    return name


def item_info(item, source):
    price = item.get("sell" if source == "auctionhouse.tk.gg" else "sell_price")
    return {
        "name": localized_name(item.get("name")),
        "vendor_sell_copper": price,
        "vendor_sell_source": source if price is not None else None,
        "quality": localized_name(item.get("quality", {}).get("name")) or item.get("q"),
        "item_class": localized_name(item.get("item_class", {}).get("name")) or item.get("cls"),
    }


def fill_missing(item, fallback):
    for field, value in fallback.items():
        if item[field] is None:
            item[field] = value


def fetch_search_catalog(session, namespace):
    items = {}
    minimum_id = 1
    while True:
        response = get_item_data(
            session, "search/item", namespace,
            id=f"[{minimum_id},]", orderby="id", _pageSize=1000, _page=1,
        )
        response.raise_for_status()
        page = response.json()

        # Start each search above the highest ID returned to respect the 1,000-result cap.
        for entry in page["results"]:
            item = entry["data"]
            item_id = item["id"]
            if item_id < minimum_id:
                raise ValueError(f"Item search returned IDs out of order for {namespace}")
            minimum_id = item_id + 1
            items[item_id] = item_info(item, namespace)

        if not page.get("resultCountCapped") and page["pageCount"] <= 1:
            return items
        if not page["results"]:
            raise ValueError(f"Item search returned an empty capped page for {namespace}")


def main():
    data_dir = PROJECT_DIR / "data"
    auctions_dir = data_dir / "auctions"
    snapshot_path = max(
        (*auctions_dir.glob("eu-alliance-pvp-*.json"),
         *auctions_dir.glob("eu-alliance-pvp-*.json.gz")),
        default=None,
    )
    observed = set()
    if snapshot_path is not None:
        open_snapshot = gzip.open if snapshot_path.suffix == ".gz" else open
        with open_snapshot(snapshot_path, "rt", encoding="utf-8") as source:
            snapshot = json.load(source)
        observed = {
            row["item"]["id"]
            for group in ("auctions", "commodities")
            for row in snapshot[group]["data"]["auctions"]
        }

    # Fetch market metadata separately so the Blizzard token stays on its own session.
    response = requests.get(MARKET_URL, timeout=30)
    response.raise_for_status()
    market = response.json()
    if market["house"]["key"] != MARKET_KEY:
        raise ValueError("The market feed returned the wrong auction house")
    market_items = {
        row["id"]: item_info(row, "auctionhouse.tk.gg") for row in market["items"]
    }

    with requests.Session() as session:
        session.headers["Authorization"] = f"Bearer {create_access_token()}"
        items = fetch_search_catalog(session, FOREVER_NAMESPACE)
        for item_id in observed | market_items.keys():
            items.setdefault(item_id, item_info({}, FOREVER_NAMESPACE))

        missing_details = {
            item_id for item_id in observed
            if items[item_id]["vendor_sell_copper"] is None
            and market_items.get(item_id, {}).get("vendor_sell_copper") is None
        }
        print(f"Checking {len(missing_details):,} IDs against Forever item details.", flush=True)
        for item_id in sorted(missing_details):
            response = get_item_data(session, f"item/{item_id}")
            if response.status_code == 404:
                continue
            response.raise_for_status()
            fill_missing(items[item_id], item_info(response.json(), FOREVER_NAMESPACE))

        for item_id, info in market_items.items():
            fill_missing(items[item_id], info)

        nameless = {item_id for item_id, info in items.items() if not info["name"]}
        if nameless:
            classic = fetch_search_catalog(session, CLASSIC_NAMESPACE)
            for item_id in nameless & classic.keys():
                items[item_id]["name"] = classic[item_id]["name"]

    catalog = {
        "locale": LOCALE,
        "forever_namespace": FOREVER_NAMESPACE,
        "snapshot_checked": snapshot_path.name if snapshot_path else None,
        "market_source": MARKET_URL,
        "items_by_id": dict(sorted(items.items())),
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "item_info.json"
    output = NamedTemporaryFile(mode="w", encoding="utf-8", dir=data_dir, delete=False)
    staged_path = Path(output.name)
    try:
        with output:
            json.dump(catalog, output, indent=2, ensure_ascii=False)
            output.write("\n")
        staged_path.replace(output_path)
    finally:
        staged_path.unlink(missing_ok=True)

    print(f"Saved {len(items):,} item records to {output_path}")
    if snapshot_path is not None:
        named = sum(bool(items[item_id]["name"]) for item_id in observed)
        priced = sum(items[item_id]["vendor_sell_copper"] is not None for item_id in observed)
        print(f"Snapshot coverage: {named:,} names and {priced:,} vendor prices / {len(observed):,} item IDs")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, KeyError, ValueError, OSError) as error:
        raise SystemExit(f"Catalog refresh failed: {error}") from None
