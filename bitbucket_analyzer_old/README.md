# Bitbucket Commit Analyzer

Analiza statystyk commitów i pull requestów z Bitbucket Server (On-Premise) dla zespołów deweloperskich.

## Funkcjonalności

- 📊 Analiza commitów dla wybranych użytkowników
- 📈 Statystyki linii kodu: dodane, usunięte, zmienione
- 🏆 Rankingi Top 3 i Bottom 3 według:
  - Liczby commitów
  - Liczby zmian (linie kodu)
  - Liczby pull requestów
- 👥 Wsparcie dla aliasów użytkowników (grupowanie zespołowe)
- 📅 Filtrowanie według zakresu dat
- 💾 Cachowanie danych dla szybszego przetwarzania
- 📄 Generowanie raportów HTML z interaktywnymi wizualizacjami

## Wymagania

- Python 3.10+
- Bitbucket Server (On-Premise) z API REST
- Dane uwierzytelniające (username + password lub API token)

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Skonfiguruj dane uwierzytelniające
cp .env.example .env
nano .env
```

## Konfiguracja

Utwórz plik `.env` z następującymi zmiennymi:

```env
# Bitbucket Server (On-Premise)
BITBUCKET_URL=http://bitbucket.your-company.com
BITBUCKET_USERNAME=your_username
BITBUCKET_PASSWORD=your_password_or_api_token
```

## Użycie

### Podstawowe użycie

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith
```

### Z zakresem dat

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson \
    --start-date 2024-01-01 --end-date 2024-12-31
```

### Z aliasami użytkowników (grupowanie zespołowe)

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson alice.jones \
    --aliases "Team A:john.doe,jane.smith" "Team B:bob.wilson,alice.jones" \
    --start-date 2024-01-01
```

### Ze szczegółową listą commitów

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe \
    --detailed-commits \
    --output john_commits_report.html
```

### Analiza konkretnej gałęzi

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --branch develop \
    --authors john.doe jane.smith
```

### Tylko zmergowane pull requesty

```bash
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith \
    --pr-state MERGED
```

## Argumenty CLI

| Argument | Skrót | Opis | Wymagany |
|----------|-------|------|----------|
| `--project` | `-p` | Klucz projektu Bitbucket | ✅ Tak |
| `--repository` | `-r` | Nazwa/slug repozytorium | ✅ Tak |
| `--authors` | `-a` | Lista nazw użytkowników do analizy | ❌ Nie |
| `--start-date` | - | Data początkowa (YYYY-MM-DD) | ❌ Nie |
| `--end-date` | - | Data końcowa (YYYY-MM-DD) | ❌ Nie |
| `--branch` | - | Nazwa gałęzi (domyślnie: master) | ❌ Nie |
| `--aliases` | - | Aliasy użytkowników "Grupa:user1,user2" | ❌ Nie |
| `--output` | `-o` | Nazwa pliku wyjściowego HTML | ❌ Nie |
| `--cache-dir` | - | Katalog cache (domyślnie: data/bitbucket_cache) | ❌ Nie |
| `--detailed-commits` | - | Dołącz szczegółowe listy commitów | ❌ Nie |
| `--pr-state` | - | Stan PR (ALL/OPEN/MERGED/DECLINED) | ❌ Nie |

## Struktura Raportu

Wygenerowany raport HTML zawiera:

### 1. Podsumowanie Statystyk
- Całkowita liczba użytkowników
- Całkowita liczba commitów
- Całkowita liczba zmian (linie)
- Linie dodane/usunięte/zmodyfikowane
- Całkowita liczba pull requestów
- Średnie wartości na użytkownika

### 2. Rankingi

**Top 3** i **Bottom 3** według:
- Liczby commitów
- Liczby zmian w kodzie
- Liczby pull requestów

### 3. Szczegółowe Statystyki Użytkowników

Tabela zawierająca dla każdego użytkownika:
- Liczba commitów
- Linie dodane
- Linie usunięte
- Linie zmodyfikowane
- Suma zmian
- Pull requesty
- Zmienione pliki

### 4. Szczegółowe Listy Commitów (opcjonalnie)

Jeśli włączona opcja `--detailed-commits`:
- Lista wszystkich commitów dla każdego użytkownika
- ID commita
- Wiadomość commita
- Data i godzina
- Statystyki zmian dla każdego commita

## Jak Działa Liczenie Linii?

- **Linie dodane**: Nowe linie dodane do kodu
- **Linie usunięte**: Linie usunięte z kodu
- **Linie zmodyfikowane**: Linie zmienione (nie liczone jako dodane + usunięte)
- **Suma zmian**: Dodane + Usunięte + Zmodyfikowane

> **Uwaga**: Linie zmodyfikowane są liczone oddzielnie. Jeśli linia została zmieniona,
> jest liczona jako "zmodyfikowana", a nie jako "usunięta + dodana".

## Aliasy Użytkowników

Aliasy pozwalają na grupowanie użytkowników w zespoły:

```bash
--aliases "Backend Team:john.doe,jane.smith" "Frontend Team:bob.wilson,alice.jones"
```

W raporcie przy nazwie użytkownika pojawi się alias grupy, co ułatwia identyfikację zespołów.

## Cachowanie

Dane z Bitbucket są cachowane w katalogu `data/bitbucket_cache/` (lub w katalogu określonym przez `--cache-dir`).

Aby wymusić ponowne pobranie danych, usuń odpowiedni plik cache:

```bash
rm data/bitbucket_cache/PROJ_my-repo_*.json
```

## Przykładowe Dane Wyjściowe

```
================================================================================
Summary
================================================================================
Total Users:        5
Total Commits:      234
Total Changes:      45,678 lines
  - Added:          28,901
  - Deleted:        12,345
  - Modified:       4,432
Total PRs:          45

Average per user:   46.8 commits
                    9135.6 changes
                    9.0 PRs

================================================================================
✅ Report generated successfully: bitbucket_commit_report.html
================================================================================
```

## Struktura Katalogów

```
bitbucket_analyzer/
├── __init__.py           # Inicjalizacja pakietu
├── fetcher.py            # Pobieranie danych z Bitbucket API
├── analyzer.py           # Analiza statystyk commitów
├── report_generator.py   # Generowanie raportów HTML
└── README.md            # Ta dokumentacja
```

## Troubleshooting

### Błąd uwierzytelniania

```
ValueError: Missing Bitbucket credentials
```

**Rozwiązanie**: Upewnij się, że plik `.env` zawiera `BITBUCKET_URL`, `BITBUCKET_USERNAME` i `BITBUCKET_PASSWORD`.

### Błąd połączenia

```
requests.exceptions.HTTPError: 401 Client Error
```

**Rozwiązanie**: Sprawdź poprawność danych uwierzytelniających. Dla Bitbucket Cloud użyj API tokena zamiast hasła.

### Brak danych w raporcie

**Rozwiązanie**:
- Sprawdź czy nazwy użytkowników są poprawne
- Sprawdź zakres dat
- Sprawdź nazwę gałęzi (domyślnie: master)
- Sprawdź czy użytkownicy mają commity w tym okresie

### Wolne generowanie raportu

**Rozwiązanie**:
- Użyj cachowania (dane są automatycznie cachowane)
- Ogranicz zakres dat
- Ogranicz liczbę użytkowników
- Pomiń opcję `--detailed-commits` dla dużych zbiorów danych

## API Bitbucket

Narzędzie korzysta z Bitbucket Server REST API 1.0:

- `/rest/api/1.0/projects/{project}/repos/{repo}/commits` - Lista commitów
- `/rest/api/1.0/projects/{project}/repos/{repo}/commits/{id}/diff` - Diff commita
- `/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests` - Lista PR-ów

Dokumentacja API: https://docs.atlassian.com/bitbucket-server/rest/

## Licencja

Tak jak główny projekt.
