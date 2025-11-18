# Przykłady Generowania Raportów

Ten dokument zawiera przykładowe komendy do generowania różnych typów raportów.

## Raporty Jira według typu zadania

### 1. Raport Story (Historie Użytkownika)

```bash
# Podstawowy raport Story
python main.py --project PROJ --issue-types Story --report

# Story z zakresem dat
python main.py --project PROJ --issue-types Story \
    --start-date 2024-01-01 --end-date 2024-12-31 --report

# Story z labelem
python main.py --project PROJ --issue-types Story \
    --label "Sprint-5" --report
```

**Wynik:** `story_flow_report.html`

**Metryki:**
- Przepływ historii przez statusy (New → Analysis → To Do → Development → Review → Done)
- Czas cyklu dla Story
- Liczba zmian statusu (rework patterns)
- Trendy czasowe tworzenia/zamykania Story

---

### 2. Raport Zadanie Dev (Development Tasks)

```bash
# Podstawowy raport Zadań Dev
python main.py --project PROJ --issue-types "Zadanie Dev" --report

# Zadania Dev z zakresem dat
python main.py --project PROJ --issue-types "Zadanie Dev" \
    --start-date 2024-01-01 --end-date 2024-12-31 --report

# Zadania Dev z labelem dla konkretnego sprintu
python main.py --project PROJ --issue-types "Zadanie Dev" \
    --label "Sprint-5" --report
```

**Wynik:** `zadanie_dev_flow_report.html`

**Metryki:**
- Przepływ zadań deweloperskich
- Czas spędzony w Development vs Review
- Częstotliwość powrotów do Development (po Review)
- Analiza blokerów

---

### 3. Raport Bug (Błędy)

```bash
# Raport błędów (domyślny typ)
python main.py --project PROJ --report

# Lub jawnie:
python main.py --project PROJ --issue-types Bug "Błąd w programie" --report
```

**Wynik:** `bug_flow_report.html`

---

### 4. Raport Wielotypowy (Combined)

```bash
# Wszystkie typy zadań w jednym raporcie
python main.py --project PROJ \
    --issue-types Story "Zadanie Dev" Bug Task --report
```

**Wynik:** `story_zadanie_dev_bug_task_flow_report.html`

**Korzyści:**
- Porównanie przepływów między różnymi typami zadań
- Identyfikacja różnic w czasie cyklu
- Analiza zależności między typami

---

## Raporty Bitbucket (Commit Analysis)

### 1. Analiza Zespołu

```bash
# Podstawowa analiza zespołu
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson

# Z grupowaniem w zespoły
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith bob.wilson alice.jones \
    --aliases "Backend:john.doe,jane.smith" "Frontend:bob.wilson,alice.jones"
```

**Wynik:** `bitbucket_commit_report.html`

**Metryki:**
- Top 3 i Bottom 3 committerów
- Linie kodu: dodane/usunięte/zmodyfikowane
- Pull requesty
- Ranking według różnych metryk

---

### 2. Analiza Sprintu/Okresu

```bash
# Commits z konkretnego okresu
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe jane.smith \
    --start-date 2024-11-01 --end-date 2024-11-15
```

**Analiza dwutygodniowego sprintu**

---

### 3. Analiza Indywidualna ze Szczegółami

```bash
# Szczegółowy raport dla jednego developera
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors john.doe \
    --detailed-commits \
    --output john_doe_commits.html
```

**Zawiera:**
- Lista wszystkich commitów
- Statystyki dla każdego commita
- Timeline aktywności

---

### 4. Analiza Konkretnej Gałęzi

```bash
# Analiza feature branch
python bitbucket_main.py --project PROJ --repository my-repo \
    --branch feature/new-dashboard \
    --authors john.doe jane.smith
```

---

## Kombinacje i Zaawansowane Użycie

### Sprint Report (Jira + Bitbucket)

```bash
# 1. Jira - Story w sprincie
python main.py --project PROJ --issue-types Story \
    --label "Sprint-5" --report

# 2. Jira - Zadania Dev w sprincie
python main.py --project PROJ --issue-types "Zadanie Dev" \
    --label "Sprint-5" --report

# 3. Bitbucket - Commits w okresie sprintu
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors team_member1 team_member2 team_member3 \
    --start-date 2024-11-01 --end-date 2024-11-14 \
    --aliases "Team A:team_member1,team_member2"
```

**Wynik:** 3 raporty HTML do analizy sprintu z różnych perspektyw

---

### Retrospekcja Kwartalna

```bash
# Q4 2024 - wszystkie typy zadań
python main.py --project PROJ \
    --issue-types Story "Zadanie Dev" Bug \
    --start-date 2024-10-01 --end-date 2024-12-31 --report

# Q4 2024 - aktywność commit
python bitbucket_main.py --project PROJ --repository my-repo \
    --start-date 2024-10-01 --end-date 2024-12-31 \
    --detailed-commits
```

---

## Szablony Raportów dla Managera

### Tygodniowy Raport Postępu

```bash
#!/bin/bash
# weekly_report.sh

WEEK_START="2024-11-11"
WEEK_END="2024-11-17"
PROJECT="PROJ"
REPO="my-repo"

# Story completed
python main.py --project $PROJECT --issue-types Story \
    --start-date $WEEK_START --end-date $WEEK_END --report

# Bugs fixed
python main.py --project $PROJECT --issue-types Bug \
    --start-date $WEEK_START --end-date $WEEK_END --report

# Team commits
python bitbucket_main.py --project $PROJECT --repository $REPO \
    --start-date $WEEK_START --end-date $WEEK_END
```

---

### Raport Performance Review (Deweloper)

```bash
#!/bin/bash
# developer_review.sh

DEVELOPER="john.doe"
PERIOD_START="2024-01-01"
PERIOD_END="2024-12-31"

# Assigned tasks (Jira)
python main.py --project PROJ --issue-types Story "Zadanie Dev" \
    --start-date $PERIOD_START --end-date $PERIOD_END --report

# Code contributions (Bitbucket)
python bitbucket_main.py --project PROJ --repository my-repo \
    --authors $DEVELOPER \
    --start-date $PERIOD_START --end-date $PERIOD_END \
    --detailed-commits \
    --output ${DEVELOPER}_review.html
```

---

## Cache Management

### Wymuszanie Świeżych Danych

```bash
# Jira - pomiń cache
python main.py --project PROJ --force-fetch --report

# Bitbucket - usuń cache ręcznie
rm data/bitbucket_cache/PROJ_my-repo_*.json
python bitbucket_main.py --project PROJ --repository my-repo
```

---

## Output Files Summary

| Typ Raportu | Nazwa Pliku | Lokalizacja |
|-------------|-------------|-------------|
| Bug flow | `bug_flow_report.html` | Katalog główny |
| Story flow | `story_flow_report.html` | Katalog główny |
| Zadanie Dev flow | `zadanie_dev_flow_report.html` | Katalog główny |
| Bitbucket commits | `bitbucket_commit_report.html` | Katalog główny |
| Jira cache | `jira_<type>_cached.json` | Katalog główny |
| Bitbucket cache | `PROJ_repo_*.json` | `data/bitbucket_cache/` |

---

## Tips & Tricks

### 1. Szybkie Porównanie Typów Zadań

```bash
# Wygeneruj wszystkie 3 typy z tego samego okresu
for TYPE in Story "Zadanie Dev" Bug; do
    python main.py --project PROJ --issue-types "$TYPE" \
        --start-date 2024-11-01 --end-date 2024-11-30 --report
done
```

### 2. Multi-Repository Analysis (Bitbucket)

```bash
# Analiza wielu repozytoriów
for REPO in backend frontend mobile; do
    python bitbucket_main.py --project PROJ --repository $REPO \
        --authors john.doe \
        --output ${REPO}_commits.html
done
```

### 3. Label-Based Sprint Reports

```bash
# Wszystkie typy zadań dla konkretnego sprintu
python main.py --project PROJ \
    --issue-types Story "Zadanie Dev" Bug \
    --label "Sprint-5" --report
```

**Toggle switch pozwoli porównać:**
- Zadania z labelem "Sprint-5" (zaplanowane)
- Wszystkie zadania (włączając ad-hoc)

---

## Automatyzacja

### Cron Job - Dzienny Raport

```cron
# Codziennie o 18:00 - raport z ostatnich 7 dni
0 18 * * * cd /path/to/jira-scrapper && ./scripts/daily_report.sh
```

**daily_report.sh:**
```bash
#!/bin/bash
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -d '7 days ago' +%Y-%m-%d)

python main.py --project PROJ --issue-types Story Bug \
    --start-date $START_DATE --end-date $END_DATE --report
```

---

## Troubleshooting

### Sprawdzanie Cache

```bash
# Jira
ls -lh jira_*_cached.json

# Bitbucket
ls -lh data/bitbucket_cache/
```

### Czyszczenie Cache

```bash
# Jira - usuń wszystkie cache
rm jira_*_cached.json

# Bitbucket - usuń stare cache (starsze niż 7 dni)
find data/bitbucket_cache/ -name "*.json" -mtime +7 -delete
```

---

**Więcej przykładów w dokumentacji:**
- [README.md](README.md) - Główna dokumentacja
- [bitbucket_analyzer/README.md](bitbucket_analyzer/README.md) - Bitbucket Analyzer
- [NEW_ANALYSES_PROPOSALS.md](NEW_ANALYSES_PROPOSALS.md) - Propozycje nowych analiz
