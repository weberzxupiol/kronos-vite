#!/usr/bin/env python3
"""Szuka zleceń freelance (strony WWW, WordPress, sklepy, reklamy, SEO) w kanałach RSS.

Użycie:
    python3 szukaj.py            # wszystkie pasujące oferty -> oferty.md
    python3 szukaj.py --nowe     # tylko te, których jeszcze nie widziałeś
"""
import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

KATALOG = Path(__file__).resolve().parent
WIDZIANE = KATALOG / "widziane.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) freelance-oferty/1.0"

# Przybliżone kursy do porównania budżetów
KURSY_USD = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "AUD": 0.66, "CAD": 0.73,
             "NZD": 0.6, "SGD": 0.74, "PLN": 0.25, "INR": 0.012, "HKD": 0.13}


def pobierz(zrodlo):
    try:
        req = urllib.request.Request(zrodlo["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            return zrodlo, r.read(), None
    except Exception as e:  # noqa: BLE001 - chcemy raport, nie crash
        return zrodlo, None, str(e)


def czysc(tekst):
    tekst = re.sub(r"<[^>]+>", " ", html.unescape(tekst or ""))
    return re.sub(r"\s+", " ", tekst).strip()


def budzet(opis):
    """Zwraca (tekst budżetu, maksimum w USD) z opisu Freelancer.com."""
    m = re.search(r"Budget:\s*([^,)]+?)\s+([A-Z]{3})\b", opis)
    if not m:
        return "", None
    liczby = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+(?:\.\d+)?", m.group(1))]
    kurs = KURSY_USD.get(m.group(2))
    maks = max(liczby) * kurs if liczby and kurs else None
    return f"{m.group(1).strip()} {m.group(2)}", maks


def parsuj(zrodlo, dane):
    oferty = []
    for item in ET.fromstring(dane).iter("item"):
        tytul = czysc(item.findtext("title"))
        opis = czysc(item.findtext("description"))
        data = item.findtext("pubDate")
        try:
            data = parsedate_to_datetime(data)
        except (TypeError, ValueError):
            data = None
        oferty.append({
            "id": item.findtext("guid") or item.findtext("link"),
            "tytul": tytul,
            "link": (item.findtext("link") or "").strip(),
            "opis": opis,
            "data": data,
            "zrodlo": zrodlo["nazwa"],
            "tagi": [czysc(c.text) for c in item.findall("category")],
        })
    return oferty


def ocen(oferta, cfg):
    tekst = f"{oferta['tytul']} {oferta['opis']} {' '.join(oferta['tagi'])}".lower()
    if any(w in tekst for w in cfg["wykluczenia"]):
        return 0, []
    trafienia = [k for k in cfg["slowa_kluczowe"] if re.search(rf"\b{re.escape(k)}\b", tekst)]
    wynik = sum(cfg["slowa_kluczowe"][k] for k in trafienia)
    # Słowa w tytule liczą się podwójnie - tytuł mówi, czego naprawdę chcą
    wynik += sum(cfg["slowa_kluczowe"][k] for k in trafienia if k in oferta["tytul"].lower())
    return wynik, trafienia


def zapisz_md(oferty, plik, bledy):
    linie = [f"# Oferty – {datetime.now():%Y-%m-%d %H:%M}", "",
             f"Znaleziono: **{len(oferty)}**", ""]
    if bledy:
        linie += ["Nie udało się pobrać: " + ", ".join(bledy), ""]
    for o in oferty:
        data = o["data"].strftime("%Y-%m-%d %H:%M") if o["data"] else "?"
        linie += [
            f"## [{o['tytul']}]({o['link']})",
            f"- **Wynik:** {o['wynik']} · **Budżet:** {o['budzet'] or 'brak'} · "
            f"**Źródło:** {o['zrodlo']} · **Dodano:** {data}",
            f"- **Pasuje:** {', '.join(o['trafienia'])}",
            "", "> " + o["opis"][:500], "",
        ]
    plik.write_text("\n".join(linie), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nowe", action="store_true", help="pokaż tylko oferty, których jeszcze nie widziałeś")
    ap.add_argument("--config", default=KATALOG / "config.json", type=Path)
    ap.add_argument("--wyjscie", default=KATALOG / "oferty.md", type=Path)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cfg["wykluczenia"] = [w.lower() for w in cfg["wykluczenia"]]
    cfg["slowa_kluczowe"] = {k.lower(): v for k, v in cfg["slowa_kluczowe"].items()}

    with ThreadPoolExecutor(max_workers=8) as ex:
        wyniki = list(ex.map(pobierz, cfg["zrodla"]))

    wszystkie, bledy = {}, []
    for zrodlo, dane, blad in wyniki:
        if blad:
            bledy.append(f"{zrodlo['nazwa']} ({blad})")
            continue
        try:
            for o in parsuj(zrodlo, dane):
                wszystkie.setdefault(o["id"], o)
        except ET.ParseError as e:
            bledy.append(f"{zrodlo['nazwa']} (zły XML: {e})")

    widziane = set(json.loads(WIDZIANE.read_text())) if WIDZIANE.exists() else set()
    pasujace = []
    for o in wszystkie.values():
        o["wynik"], o["trafienia"] = ocen(o, cfg)
        o["budzet"], maks_usd = budzet(o["opis"])
        if o["wynik"] < cfg["min_wynik"]:
            continue
        if maks_usd is not None and maks_usd < cfg["min_budzet_usd"]:
            continue
        if args.nowe and o["id"] in widziane:
            continue
        pasujace.append(o)

    pasujace.sort(key=lambda o: (o["wynik"], o["data"].timestamp() if o["data"] else 0), reverse=True)
    zapisz_md(pasujace, args.wyjscie, bledy)
    WIDZIANE.write_text(json.dumps(sorted(widziane | set(wszystkie))))

    print(f"Pobrano {len(wszystkie)} ofert z {len(cfg['zrodla']) - len(bledy)}/{len(cfg['zrodla'])} źródeł, "
          f"pasuje {len(pasujace)} -> {args.wyjscie.name}")
    for b in bledy:
        print("  BŁĄD:", b, file=sys.stderr)
    for o in pasujace[:15]:
        print(f"  [{o['wynik']:>2}] {o['tytul'][:70]:<70} {o['budzet']}")


if __name__ == "__main__":
    main()
