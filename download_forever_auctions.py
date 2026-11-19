"""Download the WoW Forever EU Alliance PvP auction house as JSON."""

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from dotenv import dotenv_values


PROJECT_DIR = Path(__file__).resolve().parent
TOKEN_URL = "https://oauth.battle.net/token"
# House 110 is the community-mapped EU Alliance PvP market.
AUCTIONS_URL = "https://eu.api.blizzard.com/data/wow/ruleset/2/auctions/110"


def create_access_token() -> str:
    credentials = dotenv_values(PROJECT_DIR / ".env", interpolate=False)
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    if not client_id or not client_secret:
        raise SystemExit("Set client_id and client_secret in the project's .env file.")

    response = requests.post(
        TOKEN_URL,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main():
    with requests.Session() as session:
        session.headers["Authorization"] = f"Bearer {create_access_token()}"
        params = {"namespace": "dynamic-forever-eu", "locale": "en_US"}

        auctions = session.get(AUCTIONS_URL, params=params, timeout=60)
        auctions.raise_for_status()
        commodities = session.get(f"{AUCTIONS_URL}/commodities", params=params, timeout=60)
        commodities.raise_for_status()

    snapshot = {}
    for name, response in (("auctions", auctions), ("commodities", commodities)):
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("auctions"), list):
            raise ValueError(f"Blizzard returned an unexpected {name} response")
        snapshot[name] = {
            "last_modified": response.headers.get("Last-Modified"),
            "data": payload,
        }

    output_dir = PROJECT_DIR / "data" / "auctions"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_dir / f"eu-alliance-pvp-{timestamp}.json"
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=output_dir) as output:
        json.dump(snapshot, output, indent=2)
        output.write("\n")
        output.flush()
        output_path.hardlink_to(output.name)

    print(f"Saved {len(snapshot['auctions']['data']['auctions']):,} auctions and "
          f"{len(snapshot['commodities']['data']['auctions']):,} commodity listings to {output_path}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, KeyError, ValueError, OSError) as error:
        raise SystemExit(f"Download failed: {error}") from None
