# freelance-oferty

Skrypt wyszukuje zlecenia na strony WWW, WordPress, sklepy (Shopify, WooCommerce), landing page, reklamy Meta i Google Ads oraz SEO. Bierze je z kanałów RSS, odrzuca śmieci, ocenia dopasowanie i zapisuje wyniki do `oferty.md`.

```bash
python3 szukaj.py          # wszystkie pasujące oferty -> oferty.md
python3 szukaj.py --nowe   # tylko nowe od ostatniego uruchomienia
```

Wymaga tylko Pythona 3.9+, bez dodatkowych bibliotek.

## Konfiguracja (`config.json`)
- `zrodla`: kanały RSS.
- `slowa_kluczowe`: słowo i jego waga. Słowo w tytule liczy się podwójnie.
- `wykluczenia`: oferta z takim słowem wypada od razu.
- `min_wynik`: minimalna ocena dopasowania.
- `min_budzet_usd`: odrzuca oferty z budżetem maksymalnym niższym niż ta kwota.

## Źródła
| Źródło | Status |
|---|---|
| Freelancer.com (RSS kategorii) | działa |
| WeWorkRemotely | działa, ale to głównie etaty i kontrakty, nie zlecenia |
| Useme | blokuje boty (Cloudflare), sprawdzaj ręcznie |
| Oferia (teraz majsteria.pl) | sprawdzaj ręcznie |

Do przeglądania ręcznie: Useme, Oferia/Majsteria, Fixly, Upwork, Fiverr, grupy na Facebooku („Zlecenia IT”, „Freelancerzy”), lokalne firmy bez strony w Google Maps.

## Szablon wiadomości (EN, Freelancer)
```
Hi! I read your brief – you need {co dokładnie, 1 zdanie własnymi słowami}.

I build fast, mobile-first websites and stores (WordPress/WooCommerce, Shopify,
React). For your project I'd:
1. {krok 1, konkretnie}
2. {krok 2}
3. {krok 3}

Similar work: {link do portfolio/realizacji}
Timeline: {X} days. Price: {kwota}, fixed.

Quick question: {jedno pytanie o szczegół z briefu – pokazuje, że przeczytałeś}
```

## Szablon (PL, Useme/Oferia)
```
Dzień dobry, przeczytałem opis: potrzebujecie {co}.
Zrobię {zakres} w {X} dni za {kwota} zł netto. W cenie: responsywność,
podstawowe SEO, podpięcie Google Analytics, 30 dni poprawek.
Przykładowe realizacje: {link}
Pytanie: {konkretne pytanie}
Pozdrawiam, {imię}, {telefon}
```
