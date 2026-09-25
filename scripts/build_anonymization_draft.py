#!/usr/bin/env python3
"""Draft the per-firm anonymization alias dictionary (Freeze Document §4).

Candidates per firm come from the Wikipedia infobox, Wikidata CEO/chair
history (P169/P488) and well-known 2019–2026 names. A candidate is KEPT only
if it appears in that firm's pinned Wikipedia article (revision recorded);
the rest are reported as dropped. Common English words are kept apart under
`ambiguous` for the author to decide. Output: configs/anonymization_aliases.yaml
(status DRAFT until the author freezes it).

Inputs (local, fetched 2026-09-25): data/raw/anonymization/wikipedia_profiles.json
Usage: python scripts/build_anonymization_draft.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "data/raw/anonymization/wikipedia_profiles.json"
OUT = ROOT / "configs/anonymization_aliases.yaml"

# ticker: {category: [candidates]}; tickers themselves are exact symbols, not verified
C = {
    "AAPL": {"names": ["Apple Inc.", "Apple Computer", "Apple"], "tickers": ["AAPL"],
             "products": ["iPhone", "iPad", "MacBook", "iMac", "Apple Watch", "AirPods", "Apple Vision Pro", "Vision Pro",
                          "HomePod", "Apple TV", "App Store", "Apple Music", "Apple Pay", "Apple Card", "iCloud", "iOS", "macOS", "Beats"],
             "executives": ["Tim Cook", "John Ternus", "Arthur Levinson", "Luca Maestri", "Kevan Parekh", "Jeff Williams", "Steve Jobs", "Steve Wozniak"],
             "hq": ["Cupertino", "Apple Park"], "ambiguous": ["Mac"]},
    "MSFT": {"names": ["Microsoft Corporation", "Microsoft"], "tickers": ["MSFT"],
             "products": ["Azure", "Xbox", "Microsoft 365", "Bing", "LinkedIn", "GitHub", "Dynamics 365", "OneDrive", "Outlook",
                          "Game Pass", "Copilot", "Activision Blizzard", "Nuance"],
             "executives": ["Satya Nadella", "Brad Smith", "Amy Hood", "Bill Gates", "Paul Allen"],
             "hq": ["Redmond"], "ambiguous": ["Windows", "Office", "Teams", "Surface"]},
    "GOOGL": {"names": ["Alphabet Inc.", "Alphabet", "Google LLC", "Google"], "tickers": ["GOOGL", "GOOG"],
              "products": ["YouTube", "Android", "Gmail", "Google Cloud", "Waymo", "DeepMind", "Gemini", "Bard", "Fitbit", "Verily", "Googleplex"],
              "executives": ["Sundar Pichai", "Larry Page", "Sergey Brin", "Ruth Porat", "Anat Ashkenazi", "Eric Schmidt"],
              "hq": ["Mountain View"], "ambiguous": ["Chrome", "Pixel", "Nest"]},
    "AMZN": {"names": ["Amazon.com, Inc.", "Amazon.com", "Amazon"], "tickers": ["AMZN"],
             "products": ["Amazon Web Services", "AWS", "Alexa", "Kindle", "Fire TV", "Prime Video", "Amazon Prime", "Whole Foods Market",
                          "Whole Foods", "Zappos", "Twitch", "Audible", "Amazon MGM Studios", "One Medical", "Zoox", "IMDb", "PillPack"],
             "executives": ["Jeff Bezos", "Andy Jassy", "Brian Olsavsky"],
             "hq": ["Seattle", "Arlington County"], "ambiguous": ["Echo", "Ring", "Prime", "Blink"]},
    "TSLA": {"names": ["Tesla, Inc.", "Tesla Motors", "Tesla"], "tickers": ["TSLA"],
             "products": ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck", "Cybercab", "Powerwall", "Megapack", "Solar Roof",
                          "Autopilot", "Full Self-Driving", "Gigafactory", "Supercharger", "Tesla Energy"],
             "executives": ["Elon Musk", "Robyn Denholm", "Zachary Kirkhorn", "Vaibhav Taneja", "Martin Eberhard", "Marc Tarpenning"],
             "hq": ["Austin", "Palo Alto"], "ambiguous": ["Semi"]},
    "META": {"names": ["Meta Platforms, Inc.", "Meta Platforms", "Meta", "Facebook, Inc.", "Facebook", "TheFacebook"], "tickers": ["META", "FB"],
             "products": ["Instagram", "WhatsApp", "Oculus", "Reality Labs", "Horizon Worlds", "Llama"],
             "executives": ["Mark Zuckerberg", "Sheryl Sandberg", "Javier Oliván", "Andrew Bosworth", "Chris Cox", "Susan Li",
                            "David Wehner", "Dina Powell", "Eduardo Saverin", "Dustin Moskovitz"],
             "hq": ["Menlo Park"], "ambiguous": ["Messenger", "Threads", "Quest"]},
    "NVDA": {"names": ["Nvidia Corporation", "Nvidia"], "tickers": ["NVDA"],
             "products": ["GeForce", "Quadro", "CUDA", "DGX", "BlueField", "Tegra", "H100", "A100", "Blackwell", "Omniverse", "Mellanox"],
             "executives": ["Jensen Huang", "Colette Kress", "Bill Dally", "Chris Malachowsky", "Curtis Priem"],
             "hq": ["Santa Clara"], "ambiguous": ["RTX", "Grace", "Hopper"]},
    "BRK-B": {"names": ["Berkshire Hathaway Inc.", "Berkshire Hathaway", "Berkshire"], "tickers": ["BRK-B", "BRK.B", "BRK.A", "BRK-A", "BRK/B", "BRK"],
              "products": ["GEICO", "BNSF", "Berkshire Hathaway Energy", "Dairy Queen", "Duracell", "See's Candies", "Precision Castparts",
                           "Fruit of the Loom", "NetJets", "Clayton Homes", "Lubrizol", "Pilot Travel Centers"],
              "executives": ["Warren Buffett", "Charlie Munger", "Greg Abel", "Ajit Jain", "Howard Graham Buffett", "Howard Buffett",
                             "Todd Combs", "Ted Weschler"],
              "hq": ["Omaha"], "ambiguous": ["Pilot"]},
    "UNH": {"names": ["UnitedHealth Group Incorporated", "UnitedHealth Group", "UnitedHealth", "UnitedHealthcare"], "tickers": ["UNH"],
            "products": ["Optum", "OptumRx", "Optum Health", "Change Healthcare"],
            "executives": ["Stephen J. Hemsley", "Stephen Hemsley", "Andrew Witty", "David Wichmann", "Brian Thompson", "Tim Noel",
                           "Wayne DeVeydt", "John Rex", "Richard T. Burke"],
            "hq": ["Minnetonka", "Eden Prairie"], "ambiguous": []},
    "V": {"names": ["Visa Inc.", "Visa"], "tickers": ["V"],
          "products": ["Visa Direct", "BankAmericard", "Visa Electron", "Plaid"],
          "executives": ["Ryan McInerney", "Alfred F. Kelly", "Al Kelly", "John F. Lundgren", "Dee Hock", "Vasant Prabhu", "Chris Suh"],
          "hq": ["San Francisco", "Foster City"], "ambiguous": []},
    "JPM": {"names": ["JPMorgan Chase & Co.", "JPMorgan Chase", "JPMorgan", "J.P. Morgan", "JP Morgan", "J. P. Morgan"], "tickers": ["JPM"],
            "products": ["Chase Bank", "Chase Sapphire", "First Republic", "One Equity Partners"],
            "executives": ["Jamie Dimon", "Jennifer Piepszak", "Daniel Pinto", "Marianne Lake", "Jeremy Barnum", "Mary Erdoes"],
            "hq": ["270 Park Avenue", "New York City"], "ambiguous": ["Chase"]},
    "JNJ": {"names": ["Johnson & Johnson", "J&J", "Johnson and Johnson"], "tickers": ["JNJ"],
            "products": ["Janssen", "Kenvue", "Tylenol", "Neutrogena", "Band-Aid", "Listerine", "Stelara", "Darzalex", "Abiomed"],
            "executives": ["Joaquin Duato", "Alex Gorsky", "John C. Reed", "Joseph Wolk", "Robert Wood Johnson"],
            "hq": ["New Brunswick"], "ambiguous": []},
    "HD": {"names": ["The Home Depot, Inc.", "The Home Depot", "Home Depot"], "tickers": ["HD"],
           "products": ["HD Supply", "SRS Distribution", "Home Depot Pro"],
           "executives": ["Ted Decker", "Craig Menear", "Richard McPhail", "Bernard Marcus", "Arthur Blank", "Ken Langone"],
           "hq": ["Atlanta"], "ambiguous": []},
    "WMT": {"names": ["Walmart Inc.", "Walmart", "Wal-Mart Stores", "Wal-Mart"], "tickers": ["WMT"],
            "products": ["Sam's Club", "Walmart+", "Flipkart", "Asda", "Jet.com", "Walmart Connect"],
            "executives": ["Doug McMillon", "John Furner", "Greg Penner", "S. Robson Walton", "Rob Walton", "Sam Walton", "John David Rainey", "Brett Biggs"],
            "hq": ["Bentonville"], "ambiguous": []},
    "PG": {"names": ["The Procter & Gamble Company", "Procter & Gamble", "P&G", "Procter and Gamble"], "tickers": ["PG"],
           "products": ["Pampers", "Ariel", "Gillette", "Pantene", "Head & Shoulders", "Olay", "Oral-B", "Downy", "Charmin", "Febreze",
                        "Vicks", "Old Spice", "Braun", "Swiffer"],
           "executives": ["Shailesh Jejurikar", "Jon Moeller", "David S. Taylor", "Andre Schulten", "William Procter", "James Gamble"],
           "hq": ["Cincinnati"], "ambiguous": ["Tide", "Crest", "Always", "Dawn", "Bounty", "Cascade"]},
    "BAC": {"names": ["Bank of America Corporation", "Bank of America", "BofA", "BofA Securities"], "tickers": ["BAC"],
            "products": ["Merrill Lynch", "Merrill", "Bank of America Securities"],
            "executives": ["Brian Moynihan", "Bruce Thompson", "Alastair Borthwick", "Paul Donofrio"],
            "hq": ["Charlotte", "Bank of America Corporate Center", "Bank of America Tower"], "ambiguous": ["Erica"]},
    "MA": {"names": ["Mastercard Incorporated", "Mastercard Inc.", "Mastercard"], "tickers": ["MA"],
           "products": ["Maestro", "Cirrus", "Mondex", "Masterpass"],
           "executives": ["Michael Miebach", "Merit Janow", "Ajay Banga", "Sachin Mehra"],
           "hq": ["Purchase, New York", "2000 Purchase Street"], "ambiguous": []},
    "PFE": {"names": ["Pfizer Inc.", "Pfizer"], "tickers": ["PFE"],
            "products": ["Comirnaty", "Paxlovid", "Seagen", "Viagra", "Lipitor", "Eliquis", "Prevnar", "Xeljanz"],
            "executives": ["Albert Bourla", "Ian Read", "David Denton", "Frank D'Amelio", "Charles Pfizer", "Charles F. Erhart"],
            "hq": ["The Spiral", "New York City"], "ambiguous": []},
    "DIS": {"names": ["The Walt Disney Company", "Walt Disney Company", "Walt Disney", "Disney"], "tickers": ["DIS"],
            "products": ["Disney+", "ESPN", "Hulu", "Marvel", "Pixar", "Lucasfilm", "Disneyland", "Walt Disney World", "20th Century Studios", "ABC"],
            "executives": ["Bob Iger", "Bob Chapek", "Josh D'Amaro", "Dana Walden", "Susan Arnold", "James P. Gorman", "Christine McCarthy",
                           "Hugh Johnston", "Roy O. Disney"],
            "hq": ["Burbank"], "ambiguous": []},
    "AVGO": {"names": ["Broadcom Inc.", "Broadcom"], "tickers": ["AVGO"],
             "products": ["VMware", "Symantec", "CA Technologies", "Brocade", "LSI Corporation"],
             "executives": ["Hock Tan", "Henry Samueli", "Kirsten Spears", "Tom Krause"],
             "hq": ["Palo Alto", "San Jose"], "ambiguous": []},
}
PAGES = {"GOOGL": ["GOOGL", "GOOGL+"]}  # Alphabet's names/products live on the Google article too
SHARED_CITIES = {"New York City", "San Francisco", "Seattle", "Atlanta", "Charlotte", "Austin", "Palo Alto", "San Jose"}


def main():
    prof = json.loads(PROFILES.read_text())
    out = {"status": "DRAFT — author review required; frozen only when status is FROZEN",
           "sources": {"wikipedia": {t: {"title": p["title"], "revid": p["revid"]} for t, p in prof.items()},
                       "wikidata": "CEO (P169) and chair (P488) statements; query in data/raw/anonymization/wikidata_executives.json"},
           "rule": "a candidate is kept only if it appears (case-insensitive, word boundary) in the firm's pinned article",
           "shared_cities": sorted(SHARED_CITIES),
           "firms": {}}
    dropped = {}
    for t, cats in C.items():
        text = " ".join(prof[k]["wikitext"] for k in PAGES.get(t, [t]))
        entry = {}
        for cat, cands in cats.items():
            if cat == "tickers":
                entry[cat] = cands
                continue
            kept = [c for c in cands if re.search(rf"(?<!\w){re.escape(c)}(?!\w)", text, re.I)]
            entry[cat] = kept
            dropped.update({f"{t}:{c}": cat for c in cands if c not in kept})
        out["firms"][t] = entry
    OUT.write_text("# Anonymization alias dictionary (Freeze Document §4). Built by\n"
                   "# scripts/build_anonymization_draft.py; edit only via review, then freeze.\n"
                   + yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=120))
    n = sum(len(v) for f in out["firms"].values() for k, v in f.items() if k != "ambiguous")
    print(f"kept {n} aliases (+ {sum(len(f['ambiguous']) for f in out['firms'].values())} ambiguous) for {len(C)} firms")
    print(f"dropped (not in the pinned article): {len(dropped)}")
    for k, cat in dropped.items():
        print(f"  {k} ({cat})")


if __name__ == "__main__":
    main()
