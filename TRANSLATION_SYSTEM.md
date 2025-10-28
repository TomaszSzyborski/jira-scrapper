# Translation System Documentation

## Overview

The Jira report now supports bilingual display with English (EN) and Polish (PL) languages. Users can switch between languages using the language selector in the report header.

## Features

✅ Language switcher buttons in header (EN/PL)
✅ All translations stored in `translations.py` module
✅ Automatic language persistence using localStorage
✅ Smooth language switching without page reload
✅ Comprehensive Polish and English translations

## Architecture

### 1. Translations Module (`translations.py`)

Contains all translations in a structured dictionary:

```python
LANGUAGES = {
    "en": {
        "report_title": "Jira Report",
        "executive_summary": "Executive Summary",
        ...
    },
    "pl": {
        "report_title": "Raport Jira",
        "executive_summary": "Podsumowanie wykonawcze",
        ...
    }
}
```

### 2. HTML Attributes (`data-i18n`)

HTML elements that need translation include the `data-i18n` attribute:

```html
<h2 class="section-title" data-i18n="executive_summary">Executive Summary</h2>
<div class="stat-label" data-i18n="total_tickets">Total Tickets</div>
```

### 3. JavaScript Language Switcher

Embedded in the report HTML:
- Stores translations JSON
- Reads/writes language preference to localStorage
- Updates all `[data-i18n]` elements dynamically

## Key Translations

### Section Titles

| English | Polish |
|---------|--------|
| Executive Summary | Podsumowanie wykonawcze |
| Daily Issue Trends | Dzienne trendy zadań |
| Status Category Distribution | Rozkład kategorii statusów |
| In Progress Tracking | Śledzenie w trakcie |
| Bug Tracking | Śledzenie błędów |
| Test Execution Progress | Postęp wykonania testów |

### Statistics Labels

| English | Polish |
|---------|--------|
| Total Tickets | Wszystkie zadania |
| Resolved Tickets | Rozwiązane zadania |
| Avg Lead Time | Średni czas realizacji |
| Total Bugs Created | Wszystkie błędy utworzone |
| Currently In Progress | Obecnie w trakcie |

### Chart Labels

| English | Polish |
|---------|--------|
| Issues Raised | Zadania utworzone |
| Issues Closed | Zadania zamknięte |
| To Do | Do zrobienia |
| In Progress | W trakcie |
| Done | Ukończone |
| Passed | Zaliczone |
| Failed | Niezaliczone |

## Usage

### For Users

1. Open the HTML report
2. Click **EN** or **PL** button in the top-right corner
3. Language preference is saved automatically
4. Next time you open any report, it will use your preferred language

### For Developers

#### Adding New Translations

Edit `src/jira_scraper/translations.py`:

```python
LANGUAGES = {
    "en": {
        ...
        "new_key": "New English Text",
    },
    "pl": {
        ...
        "new_key": "Nowy Polski Tekst",
    }
}
```

#### Using Translations in HTML

Add `data-i18n` attribute to elements:

```python
# In report_generator.py
f'<h2 class="section-title" data-i18n="new_key">New English Text</h2>'
```

#### Getting Translation in Python

```python
from jira_scraper.translations import Translations

# Get single translation
text = Translations.get("report_title", "pl")  # Returns "Raport Jira"

# Get all translations for a language
all_pl = Translations.get_all("pl")
```

## Implementation Details

### Language Switcher CSS

```css
.language-switcher {
    display: flex;
    gap: 8px;
}

.lang-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.4);
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.lang-btn.active {
    background: white;
    color: #667eea;
}
```

### Language Switcher JavaScript

```javascript
const translations = {...};  // Embedded from translations.py
let currentLang = localStorage.getItem('reportLanguage') || 'en';

function switchLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('reportLanguage', lang);
    updateLanguage();
    
    // Update button states
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.lang-btn[data-lang="${lang}"]`).classList.add('active');
}

function updateLanguage() {
    const trans = translations[currentLang];
    
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (trans[key]) {
            element.textContent = trans[key];
        }
    });
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    switchLanguage(currentLang);
});
```

## Files Modified

1. ✅ `src/jira_scraper/translations.py` - NEW - Complete translation dictionary
2. ✅ `src/jira_scraper/report_generator.py` - Added:
   - Import for translations
   - Language switcher buttons in header
   - CSS for language switcher
   - JavaScript for language switching
   - `data-i18n` attributes to key elements
3. ✅ `src/jira_scraper/__init__.py` - Exported Translations class

## Translation Coverage

### Fully Translated:
- ✅ Header and navigation
- ✅ All section titles (Executive Summary, Daily Issue Trends, Status Category, In Progress, Bug Tracking, Test Execution, Flow Analysis, Temporal Trends, Cycle Metrics, Status Distribution)
- ✅ All statistics card labels
- ✅ Chart labels (axes, legends, traces)
- ✅ Drilldown section headers
- ✅ Table headers
- ✅ Common labels (days, tickets, status, etc.)

### Partially Translated:
- Chart titles embedded in Plotly charts (would require modifying chart generation code in individual chart classes)
- Hover tooltips in charts (handled by Plotly, would need chart regeneration)
- Some dynamic drilldown content (ticket details tables)

### Not Translated (Future Enhancement):
- Dynamic content generated by JavaScript after page load
- Date format localization (currently uses ISO format)
- Number format localization (decimal separators)

## Browser Support

The translation system uses:
- `localStorage` API (IE8+, all modern browsers)
- `querySelector` / `querySelectorAll` (IE8+, all modern browsers)
- `classList` API (IE10+, all modern browsers)
- Arrow functions in JavaScript (ES6, IE Edge+, all modern browsers)

For older IE support, would need polyfills or transpilation.

## Testing

### Manual Testing Checklist

- [ ] Open report in browser
- [ ] Click PL button - verify Polish text appears
- [ ] Click EN button - verify English text appears
- [ ] Refresh page - verify language persists
- [ ] Open new report - verify language persists
- [ ] Clear localStorage - verify defaults to EN
- [ ] Check all section titles translate
- [ ] Check all stat labels translate
- [ ] Check table headers translate

### Automated Testing

```python
from jira_scraper.translations import Translations

def test_translations():
    # Test English
    assert Translations.get("report_title", "en") == "Jira Report"
    
    # Test Polish
    assert Translations.get("report_title", "pl") == "Raport Jira"
    
    # Test all keys exist in both languages
    en_keys = set(Translations.LANGUAGES["en"].keys())
    pl_keys = set(Translations.LANGUAGES["pl"].keys())
    assert en_keys == pl_keys, "Missing translations!"
```

## Future Enhancements

Possible improvements:

1. **More Languages**: Add German, French, Spanish, etc.
2. **Date Localization**: Format dates according to locale
3. **Number Localization**: Use locale-specific number formatting
4. **Chart Regeneration**: Regenerate Plotly charts with translated labels
5. **RTL Support**: Support right-to-left languages (Arabic, Hebrew)
6. **Translation Management**: UI for managing translations
7. **Language Detection**: Auto-detect browser language
8. **Translation Export**: Export translations to CSV/JSON for translators

## Example Usage

### Python Code

```python
from jira_scraper import ReportGenerator

# Generate report (translations embedded automatically)
report_gen = ReportGenerator(
    project_name="PROJ",
    start_date="2024-01-01",
    end_date="2024-12-31",
    jira_url="https://jira.company.com"
)

report_gen.generate_html_report(
    summary_stats=summary_stats,
    flow_metrics=flow_metrics,
    cycle_metrics=cycle_metrics,
    temporal_trends=temporal_trends,
    tickets=tickets,
    output_file="report.html"
)

# Translation system is automatically included!
```

### Generated HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Jira Report - PROJ</title>
    <style>
        /* Language switcher styles */
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1 data-i18n="report_title">Jira Report</h1>
        </div>
        <div class="language-switcher">
            <button class="lang-btn active" data-lang="en" onclick="switchLanguage('en')">EN</button>
            <button class="lang-btn" data-lang="pl" onclick="switchLanguage('pl')">PL</button>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title" data-i18n="executive_summary">Executive Summary</h2>
        ...
    </div>
    
    <script>
        const translations = {"en": {...}, "pl": {...}};
        function switchLanguage(lang) { ... }
        function updateLanguage() { ... }
    </script>
</body>
</html>
```

## Summary

The translation system provides:

✅ Seamless English/Polish switching
✅ Persistent language preference
✅ Easy to add new translations
✅ No external dependencies
✅ Works in all modern browsers
✅ Embedded in single HTML file

All reports generated from now on will include the bilingual interface automatically!
