# ah-grinder

Download WoW Forever auction listings and build an English item catalog
for the EU Alliance PvP market.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Add your Battle.net API credentials to `.env` in the repo root.

```dotenv
client_id=your-client-id
client_secret=your-client-secret
```

## Fetch data

```bash
.venv/bin/python download_forever_auctions.py
.venv/bin/python fetch_forever_item_names.py
```

The first script saves timestamped, gzip-compressed JSON snapshots of auctions and commodities to
`data/auctions/`. The second rebuilds `data/item_info.json` and reports name and vendor price
coverage for the latest saved snapshot. Records in `items_by_id` contain the
item name, quality, class, vendor payout per item in copper, and vendor price
source. Unknown prices are `null` and explicit zero prices are preserved.
Prices come from Blizzard’s Forever API or the
[public EU Alliance PvP market feed](https://auctionhouse.tk.gg/data/).
The Classic Era catalog supplies fallback names.

## Extract a snapshot

From the repo root, replace the example filename with your snapshot filename.
This command keeps the compressed original.

```bash
gzip -dc data/auctions/eu-alliance-pvp-TIMESTAMP.json.gz > snapshot.json
```

The extracted JSON contains the original listings and values in compact form.
The catalog script can read both `.json.gz` and older `.json` snapshots directly.
