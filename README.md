# JobFinder Bot

JobFinder to bot na Discorda służący do automatycznego monitorowania ofert pracy na portalu OLX.pl. Bot pozwala użytkownikom na definiowanie Kryteriów wyszukiwania (miasto, stanowisko) oraz filtrów (typ umowy, wymiar etatu, doświadczenie), a następnie powiadamia o nowych ogłoszeniach w dedykowanym kanale.

## 🚀 Funkcje

*   **Automatyczne monitorowanie**: Bot sprawdza nowe oferty co 10 minut.
*   **Zaawansowane filtrowanie**: Możliwość wyboru typu umowy (np. Umowa o Prace), wymiaru etatu, dostępności (praca zdalna/stacjonarna) oraz wymagań dotyczących doświadczenia.
*   **Powiadomienia w czasie rzeczywistym**: Nowe oferty pojawiają się jako czytelne karty (Embed) z najważniejszymi informacjami: ceną/wynagrodzeniem, lokalizacją i typem kontraktu.
*   **Interaktywny kreator**: Konfiguracja wyszukiwania odbywa się poprzez przyjazny interfejs z listami rozwijanymi w Discordzie.
*   **Zarządzanie wyszukiwaniami**: Proste komendy do listowania i usuwania aktywnych powiadomień.

## 🛠️ Wymagania

*   Python 3.8 lub nowszy
*   Konto bota na Discord Developer Portal (oraz token)

## 📦 Instalacja

1.  **Sklonuj repozytorium** (lub pobierz pliki projektu).

2.  **Stwórz wirtualne środowisko** (zalecane):
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  **Zainstaluj zależności**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfiguracja zmiennych środowiskowych**:
    Zmień nazwę pliku `.env.example` na `.env` lub skopiuj go i uzupełnij swój token:
    ```bash
    cp .env.example .env
    ```
    Następnie edytuj plik `.env` i wklej swój token:
    ```env
    DISCORD_TOKEN=twoj_token_bota_tutaj
    ```

## ▶️ Uruchomienie

Aby uruchomić bota, wpisz w terminalu:

```bash
python bot.py
```

## 🤖 Komendy

### Komendy Slash (wpisywane przez `/`)

*   `/findjob [miasto] [zapytanie]` – Uruchamia kreator szukania pracy. 
    *   *Przykład:* `/findjob krakow python`
*   `/listjobs` – Wyświetla listę Twoich aktywnych wyszukiwań wraz z ich ID i ustawionymi filtrami.
*   `/stopjob [search_id]` – Usuwa wyszukiwanie o podanym ID (ID można sprawdzić komendą `/listjobs`).

### Komendy administracyjne (Prefix `!`)

*   `!sync` – Synchronizuje komendy Slash z serwerem. Użyj tej komendy raz po dodaniu bota do serwera, jeśli komendy Slash nie są widoczne.
*   `!check` – Wymusza natychmiastowe sprawdzenie nowych ofert (poza automatycznym harmonogramem).

## 📂 Struktura Projektu

*   `bot.py`: Główny plik z logiką bota Discord (komendy, event loop).
*   `scraper.py`: Moduł odpowiedzialny za budowanie URL-i do OLX oraz parsowanie strony HTML z wynikami wyszukiwania.
*   `database.py`: Warstwa obsługi bazy danych SQLite (Async).
*   `jobfinder.db`: Baza danych przechowująca aktywne wyszukiwania i historię ofert (generowana automatycznie).
*   `requirements.txt`: Lista wymaganych bibliotek Python.
