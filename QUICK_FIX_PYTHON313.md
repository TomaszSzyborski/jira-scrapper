# Quick Fix for Python 3.13

```bash
python -m enusrepip --upgrade
python -m pip install --upgrade pip setuptools
```

## The Problem

```
AttributeError: module 'pkgutil' has no attribute 'ImpImporter'
```

## The Solution (3 steps)

### Step 1: Install atlassian-python-api

```bash
pip install atlassian-python-api
```

### Step 2: Replace scraper.py

```bash
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py
```

### Step 3: Done!

```python
from jira_scraper import JiraScraper

scraper = JiraScraper()  # Works now!
```

## Automated Setup

### Linux/Mac:

```bash
./setup_python313.sh
```

### Windows:

```cmd
setup_python313.bat
```

## Manual Installation

```bash
# Install atlassian-python-api
pip install atlassian-python-api>=3.41.0

# Install other dependencies
pip install polars numpy matplotlib seaborn plotly python-dotenv

# Copy Python 3.13 compatible scraper
cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py

# Configure credentials
cp .env.example .env
# Edit .env with your Jira URL and credentials

# Test
python -c "from jira_scraper import JiraScraper; s = JiraScraper(); s.test_connection()"
```

## What Changed?

- **Old:** Uses `jira` library (Python ≤ 3.12)
- **New:** Uses `atlassian-python-api` (Python 3.13 compatible)
- **API:** Exactly the same - no code changes needed!

## Verification

```python
import sys
print(f"Python: {sys.version}")

from jira_scraper import JiraScraper
print("Import successful!")

scraper = JiraScraper()
print("Scraper initialized!")
```

Expected output:
```
Python: 3.13.0 ...
Using atlassian-python-api (Python 3.13 compatible)
Auto-detected: Using username/password authentication (Jira On-Premise)
Import successful!
Scraper initialized!
```

## Still Having Issues?

See [PYTHON313_COMPATIBILITY.md](PYTHON313_COMPATIBILITY.md) for detailed troubleshooting.

## Need Help?

1. **Check your Python version:** `python --version`
2. **Verify atlassian-python-api is installed:** `pip list | grep atlassian`
3. **Confirm scraper.py was replaced:** `head -1 src/jira_scraper/scraper.py`
   - Should say: `"""Jira data extraction module - Python 3.13 compatible version."""`

## Quick Reference

| Issue | Solution |
|-------|----------|
| `pkgutil has no attribute 'ImpImporter'` | Use atlassian-python-api + scraper_py313.py |
| `No module named 'atlassian'` | `pip install atlassian-python-api` |
| `No module named 'jira_scraper'` | Check PYTHONPATH or run from project root |
| Connection fails | Check .env credentials |

That's it! 🎉
