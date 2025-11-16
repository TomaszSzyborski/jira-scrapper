# Jira Scraper & Analytics + Bitbucket Commit Analyzer

Zestaw narzędzi opartych na Pythonie do:
- **Jira Analyzer**: Scrapowanie danych projektów z Jira i generowanie kompleksowych raportów HTML z interaktywnymi wizualizacjami i szczegółową analizą przepływu zadań
- **Bitbucket Analyzer**: Analiza statystyk commitów i pull requestów z Bitbucket Server (On-Premise) dla zespołów deweloperskich

## Funkcje Jira Analyzer

- **Ekstrakcja Danych Projektu**: Scraping pełnej historii projektu z Jira według nazwy projektu
- **Analiza Przepływu Zadań**: Śledzenie przejść między statusami z interaktywnymi drilldown'ami
- **Trendy Czasowe**: Analiza metryk zadań dzień po dniu lub tydzień po tygodniu między określonymi datami
- **Interaktywne Wizualizacje**: Generowanie raportów HTML z wykresami Plotly i NVD3.js
- **Śledzenie Błędów**: ⭐ Nowy wykres dziennego tworzenia i zamykania błędów z trendami
- **Postęp Testów**: ⭐ Kumulatywny wykres wykonania testów z podziałem na statusy (Passed/Failed/Executing)
- **Status Otwartych Zadań**: ⭐ Śledzenie otwartych zadań według kategorii (In Progress/Open/Blocked)
- **Kompleksowe Raporty**: Wiele typów wizualizacji z możliwością drilldown do konkretnych zadań

## Instalacja

### Wymagania

- Python 3.13 lub wyższy
- Konto Jira z dostępem do API
- Token API Jira

### Zależności

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
jira>=3.5.0
polars>=0.20.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0
python-dateutil>=2.8.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## Konfiguracja

### Zmienne Środowiskowe

Narzędzie obsługuje zarówno **Jira Cloud** (API token) jak i **Jira On-Premise** (username/password).

#### Opcja 1: Jira Cloud (Atlassian)

Utwórz plik `.env`:

```env
JIRA_URL=https://twoja-firma.atlassian.net
JIRA_EMAIL=twoj-email@firma.com
JIRA_API_TOKEN=twoj_token_api_tutaj
```

Wygeneruj token API:
1. Zaloguj się na https://id.atlassian.com/manage/api-tokens
2. Kliknij "Create API token"
3. Skopiuj token i dodaj do pliku `.env`

#### Opcja 2: Jira On-Premise (Server/Data Center)

Utwórz plik `.env`:

```env
JIRA_URL=http://jira.twoja-firma.com
JIRA_USERNAME=twoja_nazwa_uzytkownika
JIRA_PASSWORD=twoje_haslo
```

### Auto-detekcja

Narzędzie automatycznie wykrywa metodę uwierzytelniania:
- Jeśli ustawione są `JIRA_EMAIL` i `JIRA_API_TOKEN` → używa API token (Cloud)
- Jeśli ustawione są `JIRA_USERNAME` i `JIRA_PASSWORD` → używa username/password (On-Premise)

**📖 Zobacz [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) dla szczegółowych instrukcji uwierzytelniania.**

## Użycie

### Podstawowe Użycie

```python
from jira_scraper import JiraScraper

# Inicjalizacja scrapera
scraper = JiraScraper()

# Wygeneruj raport dla projektu
scraper.generate_report(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23",
    output_file="jira_report.html"
)
```

### Interfejs Wiersza Poleceń

```bash
# Generowanie raportu z dziennymi trendami
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --granularity daily

# Generowanie raportu z tygodniowymi trendami
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --granularity weekly

# Określenie własnego pliku wyjściowego
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --output wlasny_raport.html

# Filtrowanie wykonań testów według etykiety
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --test-label "Sprint-1"
```

### Zaawansowana Konfiguracja

```python
from jira_scraper import JiraScraper, ReportConfig

config = ReportConfig(
    granularity="daily",  # lub "weekly"
    include_changelog=True,
    track_custom_fields=["Story Points", "Sprint"],
    status_categories={
        "in_progress": ["In Progress", "In Development"],
        "testing": ["To Test", "In Testing", "QA"],
        "blocked": ["Blocked", "On Hold"],
        "done": ["Done", "Closed", "Resolved"]
    }
)

scraper = JiraScraper(config=config)
scraper.generate_report(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23"
)
```

## Funkcje Raportu

### 1. Nowe Wykresy (⭐ Najnowsze Funkcje)

#### Śledzenie Błędów
- Dzienne wykresy słupkowe tworzenia vs zamykania błędów
- Linie trendów dla obu metryk
- Interaktywny drilldown pokazujący szczegóły błędów według daty
- Statystyki podsumowujące (całkowita, średnia, obecnie otwarte)

#### Postęp Wykonania Testów
- Kumulatywny wykres warstwowy pokazujący postęp testów w czasie
- Podział statusów: Passed, Failed, Executing, To Do, Aborted
- Filtrowanie według etykiety (np. "Sprint-1")
- Procent pokrycia testami
- Drilldown z linkami do wykonań testów

#### Status Otwartych Zadań
- Wykres warstwowy otwartych zadań według kategorii statusu
- Kategorie: In Progress, Open, Blocked
- Linia trendu dla całkowitej liczby otwartych zadań
- Statystyki (średnia, maksimum, obecnie otwarte)

**📖 Zobacz [NEW_CHARTS_DOCUMENTATION.md](NEW_CHARTS_DOCUMENTATION.md) dla szczegółowej dokumentacji nowych wykresów.**

### 2. Analiza Przepływu Zadań

Scraper śledzi każde przejście statusu dla każdego zadania i dostarcza:

- **Diagramy Przepływu**: Wizualna reprezentacja przemieszczania się zadań między statusami
- **Wskaźnik Odbić**: Procent zadań, które wróciły do poprzednich statusów
- **Średni Czas w Statusie**: Czas spędzany przez zadania w każdym statusie
- **Wspólne Wzorce**: Identyfikacja często występujących ścieżek przejść między statusami
- **Interaktywny Drilldown**: Kliknięcie na wzorzec pokazuje listę zadań z linkami do Jira

Przykładowe metryki:
- W Trakcie → Do Testów → W Trakcie (liczba regresji)
- Do Testów → Gotowe (pomyślny przepływ)
- Średnia liczba dni od utworzenia do zakończenia

### 3. Trendy Czasowe

#### Granulacja Dzienna
- Zadania utworzone dziennie
- Zadania zakończone dziennie
- Dystrybucja statusów w czasie
- Trendy prędkości

#### Granulacja Tygodniowa
- Metryki zagregowane tygodniowo
- Analiza na poziomie sprintu (jeśli dotyczy)
- Porównania tydzień do tygodnia

### 4. Wizualizacje

Raport HTML zawiera:

#### Interaktywne Wykresy NVD3.js
- **Wykresy Liniowe**: Kumulatywne trendy zadań w czasie
- **Wykresy Warstwowe**: Ewolucja dystrybucji statusów
- **Wykresy Słupkowe**: Tworzenie/ukończenie zadań według okresu
- **Wykresy Wielosłupkowe**: Analiza porównawcza między okresami

#### Statyczne Wykresy Seaborn
- **Mapy Ciepła**: Macierz częstotliwości przejść między statusami
- **Wykresy Pudełkowe**: Dystrybucja czasu w statusie
- **Wykresy Rozkładu**: Analiza czasu ukończenia zadań
- **Macierze Korelacji**: Zależności między różnymi metrykami

### 5. Kompleksowe Metryki

- **Przepustowość**: Zadania ukończone na okres
- **Czas Cyklu**: Czas od rozpoczęcia do zakończenia
- **Czas Realizacji**: Czas od utworzenia do zakończenia
- **Praca w Toku (WIP)**: Liczba aktywnych zadań w czasie
- **Częstotliwość Zmian Statusu**: Liczba przejść na zadanie
- **Analiza Regresji**: Zadania cofające się w przepływie pracy

## Struktura Projektu

```
jira-scraper/
│
├── main.py                 # Punkt wejścia CLI
├── jira_scraper/
│   ├── __init__.py
│   ├── scraper.py         # Podstawowa interakcja z API Jira
│   ├── analyzer.py        # Analiza danych i kalkulacja metryk
│   ├── visualizer.py      # Generowanie wykresów (NVD3 + Seaborn)
│   ├── report_generator.py # Kompilacja raportu HTML
│   └── models.py          # Modele danych i struktury
│
├── templates/
│   └── report_template.html  # Szablon HTML dla raportów
│
├── static/
│   ├── css/
│   │   └── styles.css     # Stylowanie raportu
│   └── js/
│       └── nvd3/          # Pliki biblioteki NVD3.js
│
├── tests/
│   ├── test_scraper.py
│   ├── test_analyzer.py
│   └── test_visualizer.py
│
├── .env                   # Zmienne środowiskowe (nie w git)
├── .env.example          # Przykładowy plik środowiskowy
├── .gitignore
├── requirements.txt
└── README.md
```

## Przykładowe Wyjście

Wygenerowany raport HTML zawiera następujące sekcje:

### 1. Podsumowanie Wykonawcze
- Całkowita liczba przeanalizowanych zadań
- Zakres dat
- Prędkość projektu
- Przegląd kluczowych metryk

### 2. Analiza Przepływu Zadań
- Diagram Sankeya przejść między statusami
- Najczęstsze wzorce przepływu
- Statystyki regresji

### 3. Trendy Czasowe
- Interaktywne wykresy szeregów czasowych
- Dystrybucja statusów w czasie
- Trendy tworzenia vs ukończenia

### 4. Analiza Statusów
- Czas spędzony w każdym statusie
- Częstotliwość zmian statusu
- Analiza zablokowanych zadań

### 5. Szczegółowe Tabele
- Historia poszczególnych zadań
- Log przejść między statusami
- Identyfikacja wartości odstających

## Limitowanie Szybkości API

API Jira ma limity szybkości. Scraper zawiera:
- Automatyczne wykrywanie limitów szybkości
- Logikę ponownych prób z wykładniczym cofaniem
- Wskaźniki postępu dla długotrwałych operacji

```python
# Konfiguracja limitowania szybkości
scraper = JiraScraper(
    max_retries=3,
    backoff_factor=2,
    requests_per_minute=60
)
```

## Prywatność Danych

- Wszystkie dane są przetwarzane lokalnie
- Żadne dane nie są wysyłane do usług zewnętrznych
- Dane uwierzytelniające API są przechowywane bezpiecznie w pliku `.env`
- Dodaj `.env` do `.gitignore` aby zapobiec eksponowaniu danych uwierzytelniających

## Rozwiązywanie Problemów

### Problemy z Uwierzytelnianiem
```
Error: 401 Unauthorized
```
- Sprawdź poprawność tokena API
- Upewnij się, że email Jira pasuje do właściciela tokena
- Sprawdź, czy token ma wymagane uprawnienia

### Projekt Nie Znaleziony
```
Error: Project 'PROJ' not found
```
- Sprawdź poprawność klucza projektu (uwzględnia wielkość liter)
- Upewnij się, że masz dostęp do projektu
- Sprawdź uprawnienia projektu w Jira

### Problemy z Pamięcią dla Dużych Projektów
Dla projektów z tysiącami zadań:
```python
# Przetwarzanie partiami
scraper.generate_report(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23",
    batch_size=100  # Przetwarzaj po 100 zadań na raz
)
```

## Optymalizacja Wydajności

- **Cachowanie**: Wyniki są cachowane, aby uniknąć nadmiarowych wywołań API
- **Przetwarzanie Równoległe**: Używa wątków dla współbieżnych zapytań API
- **Aktualizacje Przyrostowe**: Aktualizuj istniejące raporty bez pełnego ponownego scrapowania

```python
# Włącz cachowanie
scraper = JiraScraper(cache_enabled=True, cache_ttl=3600)

# Użyj istniejącego cache
scraper.generate_report(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23",
    use_cache=True
)
```

## Współpraca

Wkład mile widziany! Proszę:

1. Zforkuj repozytorium
2. Utwórz gałąź funkcji (`git checkout -b feature/niesamowita-funkcja`)
3. Zatwierdź zmiany (`git commit -m 'Dodaj niesamowitą funkcję'`)
4. Wypchnij do gałęzi (`git push origin feature/niesamowita-funkcja`)
5. Otwórz Pull Request

## Testowanie

Uruchom pakiet testów:

```bash
# Uruchom wszystkie testy
pytest

# Uruchom z pokryciem
pytest --cov=jira_scraper tests/

# Uruchom konkretny plik testowy
pytest tests/test_scraper.py
```

---

## 📊 Bitbucket Commit Analyzer

Narzędzie do analizy statystyk commitów i pull requestów z Bitbucket Server (On-Premise).

### Funkcje Bitbucket Analyzer

- 📊 Analiza commitów dla wybranych użytkowników
- 📈 Statystyki linii kodu: dodane, usunięte, zmienione (osobno)
- 🏆 Rankingi Top 3 i Bottom 3 według:
  - Liczby commitów
  - Liczby zmian (linie kodu)
  - Liczby pull requestów
- 👥 Wsparcie dla aliasów użytkowników (grupowanie zespołowe)
- 📅 Filtrowanie według zakresu dat
- 💾 Cachowanie danych dla szybszego przetwarzania
- 📄 Generowanie raportów HTML z kolorystycznymi wizualizacjami

### Konfiguracja Bitbucket

Dodaj do pliku `.env`:

```env
# Bitbucket Server (On-Premise)
BITBUCKET_URL=http://bitbucket.your-company.com
BITBUCKET_USERNAME=your_username
BITBUCKET_PASSWORD=your_password_or_api_token
```

### Użycie Bitbucket Analyzer

#### Podstawowe użycie

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith
```

#### Z zakresem dat

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson \
    --start-date 2024-01-01 --end-date 2024-12-31
```

#### Z aliasami użytkowników (grupowanie zespołowe)

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson alice.jones \
    --aliases "Team A:john.doe,jane.smith" "Team B:bob.wilson,alice.jones" \
    --start-date 2024-01-01
```

#### Ze szczegółową listą commitów

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe \
    --detailed-commits \
    --output john_commits_report.html
```

### Jak Działa Liczenie Linii?

- **Linie dodane**: Nowe linie dodane do kodu
- **Linie usunięte**: Linie usunięte z kodu
- **Linie zmodyfikowane**: Linie zmienione (nie liczone jako dodane + usunięte)
- **Suma zmian**: Dodane + Usunięte + Zmodyfikowane

> **Uwaga**: Linie zmodyfikowane są liczone oddzielnie. Jeśli linia została zmieniona,
> jest liczona jako "zmodyfikowana", a nie jako "usunięta + dodana".

### Raport Bitbucket

Wygenerowany raport HTML zawiera:

1. **Podsumowanie statystyk** - całkowite liczby dla wszystkich użytkowników
2. **Rankingi Top 3 i Bottom 3** - według commitów, zmian i PRów
3. **Szczegółowa tabela użytkowników** - pełne statystyki dla każdego developera
4. **Szczegółowe listy commitów** (opcjonalnie) - dla każdego użytkownika

📖 **Pełna dokumentacja**: [bitbucket_analyzer/README.md](bitbucket_analyzer/README.md)

---

## Licencja

Licencja MIT - szczegóły w pliku LICENSE

## Podziękowania

- [Jira Python Library](https://jira.readthedocs.io/)
- [NVD3.js](http://nvd3.org/) za interaktywne wizualizacje
- [Seaborn](https://seaborn.pydata.org/) za wizualizacje statystyczne

## Wsparcie

W przypadku problemów, pytań lub współpracy:
- Otwórz zgłoszenie na GitHubie
- Sprawdź [Wiki](https://github.com/yourrepo/jira-scraper/wiki) dla szczegółowej dokumentacji
- Przejrzyj istniejące zgłoszenia przed utworzeniem nowych

## Plan Rozwoju

- [ ] Dodaj wsparcie dla Jira Cloud i Jira Server
- [ ] Zaimplementuj analizę niestandardowych pól
- [ ] Dodaj eksport do formatu PDF
- [ ] Utwórz widok pulpitu z aktualizacjami w czasie rzeczywistym
- [ ] Dodaj analizę predykcyjną czasu ukończenia
- [ ] Wsparcie dla wielu projektów w jednym raporcie
- [ ] Integracja ze Slack/Teams dla automatycznego raportowania

## Historia Zmian

### Wersja 1.0.0 (Aktualna)
- Pierwsze wydanie
- Podstawowa funkcjonalność scrapowania projektu
- Generowanie raportu HTML z NVD3 i Seaborn
- Analiza przepływu zadań
- Analiza trendów dziennych i tygodniowych
- Śledzenie przejść między statusami
