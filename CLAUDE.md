# CLAUDE.md

Ten plik zawiera wskazówki dla Claude Code (claude.ai/code) podczas pracy z kodem w tym repozytorium.

## Przegląd Projektu

Narzędzie oparte na Pythonie do scrapowania danych projektów z Jira i generowania kompleksowych raportów HTML z interaktywnymi wizualizacjami i szczegółową analizą przepływu zadań.

**Aktualny Status**: Wczesny etap rozwoju - tylko podstawowa struktura modułów, główna funkcjonalność jeszcze nie zaimplementowana.

## Polecenia Deweloperskie

### Konfiguracja Środowiska
```bash
# Utwórz środowisko wirtualne (Python 3.13+)
python -m venv .venv
source .venv/bin/activate  # Na Windows: .venv\Scripts\activate

# Zainstaluj zależności (gdy requirements.txt zostanie utworzony)
pip install -r requirements.txt
```

### Testowanie
```bash
# Uruchom wszystkie testy
pytest

# Uruchom z pokryciem kodu
pytest --cov=jira_scraper tests/

# Uruchom konkretny plik testowy
pytest tests/test_scraper.py
```

### Uruchamianie Narzędzia
```bash
# Użycie CLI
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23 --granularity daily
```

## Architektura

### Główne Komponenty

Aplikacja stosuje modularną architekturę z wyraźnym podziałem odpowiedzialności:

1. **Warstwa Scrapera** (`jira_scraper/scraper.py`)
   - Obsługuje uwierzytelnianie API Jira i ekstrakcję danych
   - Implementuje limitowanie szybkości, logikę ponownych prób i obsługę błędów
   - Pobiera zadania, changelogi i metadane projektu
   - Wspiera przetwarzanie partiami dla dużych zbiorów danych

2. **Warstwa Analizy** (`jira_scraper/analyzer.py`)
   - Przetwarza surowe dane Jira na metryki analityczne
   - Oblicza wzorce przepływu zadań (przejścia między statusami)
   - Wylicza trendy czasowe (agregacje dzienne/tygodniowe)
   - Generuje metryki: przepustowość, czas cyklu, czas realizacji, WIP

3. **Warstwa Wizualizacji** (`jira_scraper/visualizer.py`)
   - Tworzy interaktywne wykresy używając NVD3.js
   - Generuje statyczne wykresy używając Seaborn/Matplotlib
   - Produkuje diagramy przepływu (diagramy Sankeya)
   - Eksportuje wizualizacje jako osadzone HTML/obrazy base64

4. **Generowanie Raportów** (`jira_scraper/report_generator.py`)
   - Kompiluje wyniki analiz i wizualizacje do raportów HTML
   - Używa szablonów z `templates/report_template.html`
   - Włącza statyczne zasoby (CSS, JS) z katalogu `static/`

5. **Modele Danych** (`jira_scraper/models.py`)
   - Definiuje struktury danych dla zadań, przejść, metryk
   - Implementuje `ReportConfig` dla zarządzania konfiguracją

### Kluczowe Wzorce Projektowe

- **Śledzenie Statusów**: Główną funkcją jest śledzenie każdego przejścia statusu dla każdego zadania, budowanie pełnej historii przemieszczania się zadania przez workflow
- **Agregacja Czasowa**: Dane mogą być agregowane w różnych granulacjach (dzienne/tygodniowe) dla analizy trendów
- **Analiza Przepływu**: Identyfikuje wzorce jak regresje (np. "W Trakcie → Do Testów → Powrót do W Trakcie")
- **Strategia Cachowania**: Implementuje cachowanie aby uniknąć nadmiarowych wywołań API i umożliwić aktualizacje przyrostowe

## Konfiguracja

### Zmienne Środowiskowe (.env)
```env
JIRA_URL=https://twoja-firma.atlassian.net
JIRA_EMAIL=twoj-email@firma.com
JIRA_API_TOKEN=twoj_token_api_tutaj
```

Nigdy nie commituj plików `.env`. Używaj `.env.example` dla szablonów.

### Limitowanie Szybkości API
API Jira ma limity szybkości. Scraper powinien implementować:
- Logikę ponownych prób z wykładniczym cofaniem
- Konfigurowalne zapytania na minutę (domyślnie: 60)
- Automatyczne wykrywanie limitów szybkości z nagłówków odpowiedzi

## Zależności

Kluczowe zależności (z README):
- `jira>=3.5.0` - Klient API Jira
- `polars>=0.20.0` - Manipulacja danymi (wysokowydajna biblioteka DataFrame)
- `matplotlib>=3.7.0`, `seaborn>=0.12.0` - Wizualizacje statyczne
- `plotly>=5.14.0` - Wykresy interaktywne (uwaga: README wymienia NVD3.js ale listuje Plotly)
- `python-dotenv>=1.0.0` - Zarządzanie zmiennymi środowiskowymi

## Przepływ Danych

1. **Ekstrakcja**: Scraper łączy się z API Jira, pobiera wszystkie zadania dla projektu w zakresie dat
2. **Transformacja**: Analyzer przetwarza changelogi zadań aby zbudować historię przejść i obliczyć metryki
3. **Analiza**: Generuje wzorce przepływu, trendy czasowe i analizę statystyczną
4. **Wizualizacja**: Tworzy wykresy i diagramy z przeanalizowanych danych
5. **Raport**: Kompiluje wszystkie komponenty w pojedynczy plik HTML z osadzonymi wizualizacjami

## Ważne Uwagi Implementacyjne

### Kategorie Statusów
System powinien wspierać mapowanie niestandardowych statusów Jira na standardowe kategorie:
- `in_progress`: ["In Progress", "In Development"]
- `testing`: ["To Test", "In Testing", "QA"]
- `blocked`: ["Blocked", "On Hold"]
- `done`: ["Done", "Closed", "Resolved"]

### Przetwarzanie Changelogu
Changelog każdego zadania musi być parsowany aby wyodrębnić wszystkie przejścia statusów z timestampami. Jest to kluczowe dla analizy przepływu i kalkulacji czasu w statusie.

### Względy Pamięciowe
Dla dużych projektów (1000+ zadań), zaimplementuj:
- Przetwarzanie partiami (konfigurowalny rozmiar partii)
- Analizę strumieniową gdzie to możliwe
- Wzorce generatorów dla przetwarzania danych

### Funkcje Raportu
Raport HTML powinien zawierać:
- Podsumowanie wykonawcze (całkowita liczba zadań, zakres dat, prędkość)
- Diagram Sankeya przejść między statusami
- Interaktywne wykresy szeregów czasowych (NVD3.js lub Plotly)
- Mapy ciepła częstotliwości przejść
- Szczegółowe tabele z historią poszczególnych zadań
