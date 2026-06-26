#!/usr/bin/env python3
"""
Refresh the industry CMA benchmark snapshot used by the comparison feature.

Downloads the latest public Capital Market Assumptions from three providers,
maps each to the tool's 10 asset-class buckets, and writes web/lib/benchmarks.json.

Providers (all public, no auth):
  - BlackRock Investment Institute  -> single .xlsx workbook  (quarterly)
  - J.P. Morgan Asset Management    -> per-currency matrix PDFs (annual)
  - State Street (SSGA)             -> Long-Term Asset Class Forecasts PDF (quarterly)

Why these three: they are the smoothest to extract (structured file or clean
tabular PDF) AND cover all 10 buckets in USD (+ EUR where noted). Research
Affiliates is the closest methodological twin to our engine but its data API is
auth-gated (needs a headless browser), so it is intentionally excluded here and
kept as an offline sanity-check instead.

Usage:
  python scripts/refresh_benchmarks.py                 # download fresh, write JSON
  python scripts/refresh_benchmarks.py --dry-run       # parse + print, do not write
  python scripts/refresh_benchmarks.py --source-dir DIR # use already-downloaded files
  python scripts/refresh_benchmarks.py --force          # re-download even if cached

Dependencies: openpyxl (xlsx), pdftotext on PATH (poppler) for the PDF parsers.

NOTE ON COMPARABILITY (surface these in the UI, do not silently mix):
  - BlackRock & JPM returns are GEOMETRIC (compound); SSGA returns are ARITHMETIC
    (~0.5*sigma^2 higher for equities). JPM horizon is 10-15y, the others ~10y.
  - All figures are NOMINAL. Non-base-currency bonds are currency-hedged at JPM
    and BlackRock; SSGA equities are LOCAL-currency (no FX translation).
  - Mapping uses the closest provider proxy per bucket (see *_MAP dicts below).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from datetime import date, timezone, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "web" / "lib" / "benchmarks.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ParkviewCMA-benchmark-refresh/1.0"

# Bucket order mirrors web/lib/types.ts ASSET_DISPLAY_INFO
BUCKETS = [
    "liquidity", "bonds_global", "bonds_hy", "bonds_em", "inflation_linked",
    "equity_us", "equity_europe", "equity_japan", "equity_em", "absolute_return",
]

# BlackRock publishes one evergreen workbook URL (always the latest quarter).
BLACKROCK_URL = (
    "https://www.blackrock.com/blk-inst-c-assets/images/tools/"
    "blackrock-investment-institute/cma/blackrock-capital-market-assumptions.xlsx"
)


def _quarter(month: int) -> int:
    return (month - 1) // 3 + 1


def ssga_urls(today) -> list[str]:
    """SSGA publishes quarterly at /{year}/...-q{n}.pdf. Newest first, walking back a
    few quarters so an early-in-quarter run still finds the most recent edition."""
    y, q = today.year, _quarter(today.month)
    out = []
    for _ in range(4):
        out.append(
            "https://www.ssga.com/library-content/assets/pdf/global/multi-asset/"
            f"{y}/long-term-asset-class-forecasts-q{q}.pdf"
        )
        q -= 1
        if q == 0:
            q, y = 4, y - 1
    return out


def jpm_urls(today, ccy: str) -> list[str]:
    """JPM publishes the next-year edition around October, so try the newest year
    first (e.g. the '2026' edition shipped Oct 2025)."""
    return [
        "https://am.jpmorgan.com/content/dam/jpm-am-aem/global/en/insights/"
        f"ltcma-{yr}-us-matrix_{ccy}.pdf"
        for yr in (today.year + 1, today.year, today.year - 1)
    ]


# Each source resolves to a date-derived list of candidate URLs (newest first);
# get_file() downloads the first that returns a valid file.
SOURCES = {
    "blackrock": {"cache": "blackrock-cma.xlsx", "urls": lambda d: [BLACKROCK_URL]},
    "jpm_usd": {"cache": "jpm-ltcma-usd.pdf", "urls": lambda d: jpm_urls(d, "usd")},
    "jpm_eur": {"cache": "jpm-ltcma-eur.pdf", "urls": lambda d: jpm_urls(d, "eur")},
    "ssga": {"cache": "ssga-ltacf.pdf", "urls": lambda d: ssga_urls(d)},
}

# Magic bytes to reject HTML error pages served with a 200.
MAGIC = {".xlsx": b"PK\x03\x04", ".pdf": b"%PDF"}

# ---- bucket -> provider proxy maps -----------------------------------------

# BlackRock: match (currency, exact asset name in 'Starting point' sheet col C)
BLACKROCK_MAP = {
    "usd": {
        "liquidity": "US cash",
        "bonds_global": "US government (all maturities)",
        "bonds_hy": "US high yield",
        "bonds_em": "USD EM debt",
        "inflation_linked": "US inflation-linked government",
        "equity_us": "US large cap equities",
        "equity_europe": "Europe large cap equities",
        "equity_japan": "Japan large cap equities",
        "equity_em": "Emerging large cap equities",
        "absolute_return": "Hedge funds (global)",
    },
    "eur": {
        "liquidity": "EMU cash",
        "bonds_global": "EMU treasury bonds",
        "bonds_hy": "Global high yield bonds",
        "bonds_em": "USD EM debt",
        "inflation_linked": "EMU index-linked treasuries",
        "equity_us": "US large cap equities",
        "equity_europe": "Europe large cap equities",
        "equity_japan": "Japan large cap equities",
        "equity_em": "Emerging large cap equities",
        "absolute_return": "Hedge funds (global)",
    },
}

# J.P. Morgan: exact row label; we take the 4th number (Compound Return 2026)
JPM_MAP = {
    "usd": {
        "liquidity": "U.S. Cash",
        "bonds_global": "U.S. Aggregate Bonds",
        "bonds_hy": "U.S. High Yield Bonds",
        "bonds_em": "Emerging Markets Sovereign Debt",
        "inflation_linked": "TIPS",
        "equity_us": "U.S. Large Cap",
        "equity_europe": "Euro Area Large Cap",
        "equity_japan": "Japanese Equity",
        "equity_em": "Emerging Markets Equity",
        "absolute_return": "Diversified Hedge Funds",
    },
    "eur": {
        "liquidity": "Euro Cash",
        "bonds_global": "Euro Government Bonds",
        "bonds_hy": "U.S. High Yield Bonds hedged",
        "bonds_em": "Emerging Markets Sovereign Debt hedged",
        "inflation_linked": "Euro Govt Inflation-Linked Bonds",
        "equity_us": "U.S. Large Cap",
        "equity_europe": "Euro Area Large Cap",
        "equity_japan": "Japanese Equity",
        "equity_em": "Emerging Markets Equity",
        "absolute_return": "Diversified Hedge Funds hedged",
    },
}

# SSGA: anchor on the row's asset-class LABEL (or unambiguous benchmark) as an exact
# consecutive-word run, then read the 3rd numeric column (Long term, 10+ years) by
# coordinate. Label anchors disambiguate (e.g. "MSCI Euro" != "MSCI Europe").
# null entries = bucket has no clean native line in that currency.
SSGA_MAP = {
    "usd": {
        "liquidity": "US Cash",
        "bonds_global": "US Government Bond",
        "bonds_hy": "US High Yield Bond",
        "bonds_em": "Emerging Markets Bonds",
        "inflation_linked": "US TIPS Bond",
        "equity_us": "US Large Cap",
        "equity_europe": "MSCI Euro",        # MSCI Europe row is blank in the PDF; MSCI Euro is the clean proxy
        "equity_japan": None,                # no standalone Japan equity (MSCI Pacific only)
        "equity_em": "Emerging Markets (EM)",
        "absolute_return": "Hedge Funds",
    },
    "eur": {
        "liquidity": "EMU Cash",
        "bonds_global": "Euro Government Bonds",
        "bonds_hy": "Euro High Yield Bonds",
        "bonds_em": None,                    # EMBI is USD only; no native-EUR EM HC line
        "inflation_linked": None,
        "equity_us": None,                   # local-ccy only; would need FX
        "equity_europe": "MSCI Euro",        # EUR-denominated -> valid for EUR base
        "equity_japan": None,
        "equity_em": None,
        "absolute_return": None,             # HFRI FoF is USD only
    },
}

PROVIDER_META = {
    "blackrock": {
        "name": "BlackRock Investment Institute",
        "publication": "Capital Market Assumptions",
        "horizon": "10y",
        "return_basis": "geometric",
        "fees": "gross",
        "source_url": BLACKROCK_URL,
        "notes": "Nominal. Non-USD bond figures are currency-hedged; equities unhedged. "
                 "Uses the 'Starting point' base-case tab (ignores scenario tabs).",
    },
    "jpmorgan": {
        "name": "J.P. Morgan Asset Management",
        "publication": "2026 Long-Term Capital Market Assumptions (30th edition)",
        "horizon": "10-15y",
        "return_basis": "geometric",
        "fees": "gross (alternatives net of manager fees)",
        "source_url": "https://am.jpmorgan.com/us/en/asset-management/institutional/insights/portfolio-insights/ltcma/",
        "notes": "Nominal compound (2026) returns. Horizon is 10-15y (longer than our 10y). "
                 "Non-base-currency assets are currency-hedged in the EUR matrix.",
    },
    "ssga": {
        "name": "State Street Investment Management",
        "publication": "Long-Term Asset Class Forecasts (Q2 2026)",
        "horizon": "10y+",
        "return_basis": "arithmetic",
        "fees": "gross",
        "source_url": "https://www.ssga.com/us/en/institutional/capabilities/multi-asset-solutions/asset-class-forecasts",
        "notes": "ARITHMETIC averages (~0.5*sigma^2 above geometric for equities), gross of fees, "
                 "LOCAL-currency (no FX translation). No standalone Japan equity. EUR coverage partial.",
    },
}

VALID_RANGE = (-15.0, 25.0)  # plausible % p.a. expected return; outside => parse error

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def get_file(key: str, source_dir: Path | None, cache_dir: Path, force: bool, today) -> Path:
    cache_name = SOURCES[key]["cache"]
    if source_dir is not None:
        p = source_dir / cache_name
        if p.exists():
            return p
        raise FileNotFoundError(f"--source-dir given but {p} not found")
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / cache_name
    if dest.exists() and not force:
        return dest
    magic = MAGIC[dest.suffix]
    errors = []
    for url in SOURCES[key]["urls"](today):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if not data.startswith(magic):
                errors.append(f"{url} -> not a {dest.suffix} ({data[:8]!r})")
                continue
            dest.write_bytes(data)
            print(f"  {key}: fetched {url}")
            return dest
        except Exception as e:  # HTTPError / URLError / timeout -> try next candidate
            errors.append(f"{url} -> {e}")
    raise RuntimeError(f"{key}: no candidate URL worked:\n    " + "\n    ".join(errors))


def pdf_text(path: Path) -> str:
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"pdftotext failed on {path}: {out.stderr}")
    return out.stdout


def find_date(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Parsers  -> {currency: {bucket: {"value": float|None, "proxy": str}}}
# ---------------------------------------------------------------------------

def parse_blackrock(path: Path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = next((w for w in wb.worksheets if w.title.strip().startswith("Starting point")), None)
    if ws is None:
        raise RuntimeError("BlackRock: 'Starting point' sheet not found")
    # build {(currency, asset): 10yr value}  -- col A=currency, C=asset, G=10yr return
    table = {}
    as_of = None
    for r in ws.iter_rows(min_row=1, values_only=True):
        if as_of is None and r and isinstance(r[0], str) and "data as of" in r[0].lower():
            m = re.search(r"data as of (.+)$", r[0], re.I)
            if m:
                as_of = m.group(1).strip()
        if not r or len(r) < 7:
            continue
        cur, asset, g = r[0], r[2], r[6]
        if isinstance(cur, str) and isinstance(asset, str) and isinstance(g, (int, float)):
            table[(cur.strip(), asset.strip())] = round(g * 100, 2)
    result = {}
    for cur, m in BLACKROCK_MAP.items():
        result[cur] = {}
        cur_label = cur.upper()
        for bucket, asset in m.items():
            val = table.get((cur_label, asset))
            result[cur][bucket] = {"value": val, "proxy": asset}
    return result, _norm_date(as_of)


def parse_jpm(usd_path: Path, eur_path: Path):
    texts = {"usd": pdf_text(usd_path), "eur": pdf_text(eur_path)}
    as_of = find_date(texts["usd"], [r"data as of ([A-Za-z]+ \d{1,2}, \d{4})"])
    # Each return row is: [section?] LABEL  Compound2025 Arithmetic2026 Volatility Compound2026 ...corr
    # We want the 4th number (Compound 2026). The same labels reappear as
    # correlation-matrix column headers indented ~250 chars with only corr values
    # after them, so we require the label near the line start (idx<=30) and
    # immediately preceded by a space (rejects 'World ex-Euro...' for 'Euro...').
    tail4 = re.compile(r" +(-?\d+\.\d+) +(-?\d+\.\d+) +(-?\d+\.\d+) +(-?\d+\.\d+)")
    result = {}
    for cur, mp in JPM_MAP.items():
        lines = texts[cur].splitlines()
        result[cur] = {}
        for bucket, label in mp.items():
            val = None
            for ln in lines:
                idx = ln.find(label)
                if idx == -1 or idx > 30 or (idx > 0 and ln[idx - 1] != " "):
                    continue
                m = tail4.match(ln[idx + len(label):])
                if m:
                    val = float(m.group(4))
                    break
            result[cur][bucket] = {"value": val, "proxy": label}
    return result, _norm_date(as_of)


def parse_ssga(path: Path):
    # Coordinate-based: anchor on the row label, then read the 3rd numeric column
    # (Long term, 10+ years) by y-row. Robust across PDF text-tool versions, unlike
    # a -layout line heuristic (poppler vs xpdf serialize the equity rows differently).
    import fitz

    doc = fitz.open(path)
    full_text = "".join(p.get_text() for p in doc)
    as_of = find_date(full_text, [r"As of (March \d{1,2}, \d{4})", r"as of (\w+ \d{1,2}, \d{4})"])
    floatre = re.compile(r"^-?\d+\.\d+$")
    pages_words = [p.get_text("words") for p in doc]  # (x0,y0,x1,y1,text,block,line,word)

    def row_value(anchor: str):
        toks = anchor.split()
        n = len(toks)
        for words in pages_words:
            for i in range(len(words) - n + 1):
                if all(words[i + k][4] == toks[k] for k in range(n)):
                    yc = (words[i][1] + words[i][3]) / 2
                    floats = sorted(
                        (w[0], float(w[4]))
                        for w in words
                        if floatre.match(w[4]) and abs((w[1] + w[3]) / 2 - yc) <= 3.0
                    )
                    vals = [v for _, v in floats]
                    if len(vals) >= 3:
                        return vals[2]  # Long term, 10+ years
        return None

    result = {}
    for cur, mp in SSGA_MAP.items():
        result[cur] = {}
        for bucket, anchor in mp.items():
            if anchor is None:
                result[cur][bucket] = {"value": None, "proxy": "no native line in this currency"}
            else:
                result[cur][bucket] = {"value": row_value(anchor), "proxy": anchor}
    return result, _norm_date(as_of)


_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def _norm_date(raw: str | None) -> str | None:
    """Normalise '31 March 2026' / 'March 31, 2026' -> '2026-03-31'."""
    if not raw:
        return None
    raw = raw.strip().rstrip(".")
    m = re.search(r"(\d{1,2}) ([A-Za-z]+) (\d{4})", raw)          # 31 March 2026
    if m:
        d, mon, y = m.groups()
    else:
        m = re.search(r"([A-Za-z]+) (\d{1,2}),? (\d{4})", raw)    # March 31, 2026
        if not m:
            return raw
        mon, d, y = m.groups()
    mi = _MONTHS.get(mon.lower())
    return f"{y}-{mi:02d}-{int(d):02d}" if mi else raw


# ---------------------------------------------------------------------------
# Assemble + validate
# ---------------------------------------------------------------------------

def validate(provider: str, returns: dict) -> list[str]:
    warnings = []
    for cur, buckets in returns.items():
        for b in BUCKETS:
            cell = buckets.get(b)
            if cell is None:
                warnings.append(f"{provider}.{cur}.{b}: MISSING bucket")
                continue
            v = cell["value"]
            if v is None:
                # SSGA legitimately has nulls; flag only USD gaps that aren't expected
                if provider == "ssga" and (cur == "eur" or b == "equity_japan"):
                    continue
                warnings.append(f"{provider}.{cur}.{b}: null (proxy='{cell['proxy']}')")
            elif not (VALID_RANGE[0] <= v <= VALID_RANGE[1]):
                warnings.append(f"{provider}.{cur}.{b}: {v} out of range {VALID_RANGE}")
    return warnings


def main():
    ap = argparse.ArgumentParser(description="Refresh CMA benchmark snapshot")
    ap.add_argument("--source-dir", type=Path, help="use pre-downloaded files instead of fetching")
    ap.add_argument("--cache-dir", type=Path, default=REPO_ROOT / ".cache" / "benchmarks")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    ap.add_argument("--dry-run", action="store_true", help="print summary, do not write")
    ap.add_argument("--today", help="ISO date stamp for 'generated' (default: today)")
    args = ap.parse_args()

    today = (
        datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    )

    print("Fetching sources...")
    f = {k: get_file(k, args.source_dir, args.cache_dir, args.force, today) for k in SOURCES}

    print("Parsing...")
    bl, bl_date = parse_blackrock(f["blackrock"])
    jp, jp_date = parse_jpm(f["jpm_usd"], f["jpm_eur"])
    ss, ss_date = parse_ssga(f["ssga"])

    providers = {}
    for key, returns, as_of in [("blackrock", bl, bl_date), ("jpmorgan", jp, jp_date), ("ssga", ss, ss_date)]:
        meta = dict(PROVIDER_META[key])
        meta["as_of"] = as_of or "unknown"
        meta["returns"] = returns
        providers[key] = meta

    # validate
    all_warnings = []
    for key in providers:
        all_warnings += validate(key, providers[key]["returns"])

    # print summary table
    print("\n  bucket             | " + " | ".join(f"{k:>9}" for k in providers))
    print("  " + "-" * 56)
    for b in BUCKETS:
        cells = []
        for k in providers:
            v = providers[k]["returns"]["usd"][b]["value"]
            cells.append(f"{v:>9.2f}" if v is not None else f"{'--':>9}")
        print(f"  {b:18s} | " + " | ".join(cells))
    print(f"\n  as_of: blackrock={providers['blackrock']['as_of']}  "
          f"jpmorgan={providers['jpmorgan']['as_of']}  ssga={providers['ssga']['as_of']}")

    if all_warnings:
        print("\n  WARNINGS:")
        for w in all_warnings:
            print("   -", w)

    doc = {
        "schema_version": 1,
        "generated": today.isoformat(),
        "disclaimer": "Public CMAs mapped to Parkview's 10 buckets via the closest provider proxy. "
                      "Bases differ (geometric vs arithmetic, 10y vs 10-15y, nominal, hedging, FX) "
                      "- see each provider's notes/return_basis before comparing.",
        "buckets": BUCKETS,
        "providers": providers,
    }

    if args.dry_run:
        print("\n[dry-run] not writing.")
        return 1 if any("out of range" in w or "MISSING" in w for w in all_warnings) else 0

    # Avoid a no-op PR: if only the 'generated' timestamp would change, keep the
    # previous one so the file stays byte-identical and CI opens no pull request.
    if args.out.exists():
        try:
            prev = json.loads(args.out.read_text(encoding="utf-8"))
            if {k: v for k, v in doc.items() if k != "generated"} == {
                k: v for k, v in prev.items() if k != "generated"
            }:
                doc["generated"] = prev.get("generated", doc["generated"])
                print("No data change (only timestamp) - preserving 'generated'.")
        except (json.JSONDecodeError, OSError):
            pass

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nWrote {args.out.relative_to(REPO_ROOT)}")
    return 1 if any("out of range" in w or "MISSING" in w for w in all_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
