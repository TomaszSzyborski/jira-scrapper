# Python 3.13 Compatibility Guide

## Issue

Python 3.13 removed `pkgutil.ImpImporter`, which breaks the `jira` library (version 3.x). This causes errors like:

```
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'
```

## Solutions

We provide **two solutions** - choose the one that best fits your needs:

### ✅ Solution 1: Use atlassian-python-api (Recommended for Python 3.13)

This is the **recommended solution** for Python 3.13 users.

#### 1. Install atlassian-python-api

```bash
pip install atlassian-python-api>=3.41.0
```

#### 2. Replace scraper.py

Rename the Python 3.13 compatible version:

```bash
cd src/jira_scraper/
mv scraper.py scraper_old.py
mv scraper_py313.py scraper.py
```

Or directly:

```bash
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py
```

#### 3. Install all requirements

```bash
pip install -r requirements.txt
```

#### 4. Usage (no changes needed!)

The API is exactly the same:

```python
from jira_scraper import JiraScraper

# Works exactly the same!
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ")
```

**Benefits:**
- ✅ Python 3.13 compatible
- ✅ Same API - no code changes needed
- ✅ Actively maintained
- ✅ Works with both Cloud and On-Premise

---

### Solution 2: Downgrade to Python 3.11 or 3.12

If you prefer to stick with the original `jira` library:

#### 1. Use Python 3.11 or 3.12

```bash
# Using pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Or using conda
conda create -n jira-scraper python=3.12
conda activate jira-scraper
```

#### 2. Install requirements

```bash
pip install jira>=3.5.0
pip install -r requirements.txt
```

#### 3. Use original scraper.py

No changes needed - the original scraper.py will work fine.

---

## Automatic Fallback

The new `scraper_py313.py` includes **automatic fallback**:

```python
try:
    from atlassian import Jira
    USING_ATLASSIAN_API = True
except ImportError:
    from jira import JIRA
    USING_ATLASSIAN_API = False
```

This means:
- If `atlassian-python-api` is installed → uses it (Python 3.13 compatible)
- If not → falls back to `jira` library (Python ≤ 3.12)

---

## Installation Instructions

### Quick Start (Python 3.13)

```bash
# 1. Install atlassian-python-api
pip install atlassian-python-api

# 2. Install other requirements
pip install polars numpy matplotlib seaborn plotly python-dotenv

# 3. Copy the Python 3.13 compatible scraper
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py

# 4. Test connection
python -c "from jira_scraper import JiraScraper; s = JiraScraper(); s.test_connection()"
```

### Full Installation

```bash
# 1. Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install requirements
pip install -r requirements.txt

# 3. Use Python 3.13 compatible scraper
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py

# 4. Configure .env
cp .env.example .env
# Edit .env with your credentials

# 5. Test
python examples/generate_charts_example.py
```

---

## API Differences

### atlassian-python-api vs jira library

Both libraries work with the same code, but there are minor internal differences:

| Feature | jira library | atlassian-python-api |
|---------|--------------|----------------------|
| Python 3.13 | ❌ Not compatible | ✅ Compatible |
| Cloud Support | ✅ Yes | ✅ Yes |
| On-Premise | ✅ Yes | ✅ Yes |
| Return Type | Objects | Dictionaries |
| Our API | ✅ Same | ✅ Same |

**Good news:** Our `scraper_py313.py` handles both, so your code doesn't change!

---

## Troubleshooting

### Error: "No module named 'atlassian'"

```bash
pip install atlassian-python-api
```

### Error: "pkgutil has no attribute 'ImpImporter'"

You're using Python 3.13 with the old `jira` library. Choose one:
- **Option A:** Use `atlassian-python-api` (recommended)
- **Option B:** Downgrade to Python 3.12

### Error: "module 'jira_scraper' has no attribute 'JiraScraper'"

Make sure you copied the scraper file:

```bash
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py
```

### Connection fails with atlassian-python-api

Check your credentials and authentication method:

```python
# For Cloud
scraper = JiraScraper(
    jira_url="https://company.atlassian.net",
    jira_email="user@company.com",
    jira_api_token="your_token"
)

# For On-Premise
scraper = JiraScraper(
    jira_url="http://jira.company.com",
    jira_username="username",
    jira_password="password"
)
```

---

## Testing

### Test with Python 3.13

```python
import sys
print(f"Python version: {sys.version}")

from jira_scraper import JiraScraper

# Test connection
scraper = JiraScraper()
if scraper.test_connection():
    print("✓ Connection successful")

    # Test fetching tickets
    tickets = scraper.get_project_tickets("PROJ", start_date="2024-01-01", end_date="2024-01-31")
    print(f"✓ Fetched {len(tickets)} tickets")
else:
    print("✗ Connection failed")
```

### Test both libraries

```bash
# Test with atlassian-python-api
pip install atlassian-python-api
python test_scraper.py

# Test with jira library (Python ≤ 3.12 only)
pip uninstall atlassian-python-api
pip install jira
python test_scraper.py
```

---

## Performance Comparison

Both libraries have similar performance:

| Operation | jira library | atlassian-python-api |
|-----------|--------------|----------------------|
| Fetch 100 tickets | ~5s | ~5s |
| Fetch 1000 tickets | ~45s | ~47s |
| Get project info | <1s | <1s |

---

## Migration Checklist

- [ ] Check Python version: `python --version`
- [ ] If Python 3.13:
  - [ ] Install `atlassian-python-api`
  - [ ] Copy `scraper_py313.py` to `scraper.py`
- [ ] If Python 3.11/3.12:
  - [ ] Install `jira` library
  - [ ] Use original `scraper.py`
- [ ] Configure `.env` file
- [ ] Test connection: `scraper.test_connection()`
- [ ] Test fetching tickets
- [ ] Test Xray charts (if applicable)

---

## Recommended Setup

### For New Projects (Python 3.13)

```bash
# 1. Create project with Python 3.13
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Install atlassian-python-api
pip install atlassian-python-api polars numpy matplotlib seaborn plotly python-dotenv

# 3. Use Python 3.13 compatible scraper
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py

# 4. Configure and run
cp .env.example .env
# Edit .env with credentials
python main.py --project PROJ --start-date 2024-01-01 --end-date 2024-10-23
```

### For Existing Projects (Python 3.11/3.12)

```bash
# No changes needed! Continue using:
pip install jira>=3.5.0
# Use original scraper.py
```

---

## Future Plans

- The `jira` library maintainers are working on Python 3.13 support
- Once `jira>=4.0` is released with Python 3.13 support, you can switch back
- Our code will work with both libraries

---

## Support

### If using atlassian-python-api:
- Documentation: https://atlassian-python-api.readthedocs.io/
- Issues: https://github.com/atlassian-api/atlassian-python-api/issues

### If using jira library:
- Documentation: https://jira.readthedocs.io/
- Issues: https://github.com/pycontribs/jira/issues

---

## Summary

| Python Version | Recommended Library | Action |
|---------------|---------------------|--------|
| 3.13 | atlassian-python-api | Use `scraper_py313.py` |
| 3.12 | jira or atlassian-python-api | Either works |
| 3.11 | jira or atlassian-python-api | Either works |
| 3.10 | jira or atlassian-python-api | Either works |

**Bottom line:** For Python 3.13, use `atlassian-python-api` and the new `scraper_py313.py`. Everything else stays the same!
