"""Refresh the English item-name catalog for WoW Forever."""

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


def english_name(item):
    name = item.get("name")
    if isinstance(name, dict):
        return name.get(LOCALE) or name.get("en_GB")
    return name


def fetch_search_catalog(session, namespace):
    names = {}
    nameless = set()
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
            name = english_name(item)
            if name:
                names[item_id] = name
            else:
                nameless.add(item_id)

        if not page.get("resultCountCapped") and page["pageCount"] <= 1:
            return names, nameless
        if not page["results"]:
            raise ValueError(f"Item search returned an empty capped page for {namespace}")


def main():
    data_dir = PROJECT_DIR / "data"
    snapshots = (data_dir / "auctions").glob("eu-alliance-pvp-*.json")
    snapshot_path = max(snapshots, default=None)
    observed = set()
    if snapshot_path is not None:
        with snapshot_path.open(encoding="utf-8") as source:
            snapshot = json.load(source)
        observed = {
            row["item"]["id"]
            for group in ("auctions", "commodities")
            for row in snapshot[group]["data"]["auctions"]
        }

    with requests.Session() as session:
        session.headers["Authorization"] = f"Bearer {create_access_token()}"
        names, nameless = fetch_search_catalog(session, FOREVER_NAMESPACE)
        classic_ids = set()
        if (observed | nameless) - names.keys():
            classic_names, _ = fetch_search_catalog(session, CLASSIC_NAMESPACE)
            classic_ids = ((observed | nameless) - names.keys()) & classic_names.keys()
            names.update({item_id: classic_names[item_id] for item_id in classic_ids})

        missing = (observed | nameless) - names.keys()
        print(f"Checking {len(missing):,} remaining IDs against Forever item details.", flush=True)
        for item_id in sorted(missing):
            response = get_item_data(session, f"item/{item_id}")
            if response.status_code == 404:
                continue
            response.raise_for_status()
            name = english_name(response.json())
            if name:
                names[item_id] = name

    market_ids = set()
    missing_snapshot = observed - names.keys()
    if missing_snapshot:
        # Keep the Blizzard bearer token on the Blizzard session.
        response = requests.get(MARKET_URL, timeout=30)
        response.raise_for_status()
        market = response.json()
        if market["house"]["key"] != MARKET_KEY:
            raise ValueError("The market fallback returned the wrong auction house")
        for item in market["items"]:
            item_id = item["id"]
            name = english_name(item)
            if item_id in missing_snapshot and name:
                names[item_id] = name
                market_ids.add(item_id)

    catalog = {
        "locale": LOCALE,
        "forever_namespace": FOREVER_NAMESPACE,
        "snapshot_checked": snapshot_path.name if snapshot_path else None,
        "classic_era_fallback_ids": sorted(classic_ids),
        "market_fallback_source": MARKET_URL,
        "market_fallback_ids": sorted(market_ids),
        "unresolved_forever_search_ids": sorted(nameless - names.keys()),
        "unresolved_snapshot_ids": sorted(observed - names.keys()),
        "names_by_id": dict(sorted(names.items())),
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "forever_item_names.json"
    output = NamedTemporaryFile(mode="w", encoding="utf-8", dir=data_dir, delete=False)
    staged_path = Path(output.name)
    try:
        with output:
            json.dump(catalog, output, indent=2, ensure_ascii=False)
            output.write("\n")
        staged_path.replace(output_path)
    finally:
        staged_path.unlink(missing_ok=True)

    print(f"Saved {len(names):,} names to {output_path}")
    if snapshot_path is not None:
        print(f"Snapshot coverage: {len(observed & names.keys()):,} / {len(observed):,} item IDs")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, KeyError, ValueError, OSError) as error:
        raise SystemExit(f"Catalog refresh failed: {error}") from None
