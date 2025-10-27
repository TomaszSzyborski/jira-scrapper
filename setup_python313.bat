@echo off
REM Setup script for Python 3.13 compatibility (Windows)

echo =========================================
echo Jira Scraper - Python 3.13 Setup
echo =========================================
echo.

REM Check Python version
python --version
echo.

echo Checking Python version...
python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and v.minor==13 else 1)"

if %ERRORLEVEL% EQU 0 (
    echo Python 3.13 detected
    echo.
    echo Installing atlassian-python-api for Python 3.13 compatibility...
    echo.

    REM Install atlassian-python-api
    pip install atlassian-python-api>=3.41.0

    echo.
    echo Replacing scraper.py with Python 3.13 compatible version...

    REM Backup original scraper
    if exist "src\jira_scraper\scraper.py" (
        copy src\jira_scraper\scraper.py src\jira_scraper\scraper_original_backup.py
        echo Backed up original scraper to scraper_original_backup.py
    )

    REM Copy Python 3.13 compatible version
    copy src\jira_scraper\scraper_py313.py src\jira_scraper\scraper.py
    echo Installed Python 3.13 compatible scraper

) else (
    echo Python version is not 3.13
    echo.
    echo Installing jira library (standard version)...
    echo.

    REM Install jira library
    pip install jira>=3.5.0
)

echo.
echo Installing other dependencies...
echo.

REM Install other requirements
pip install polars>=0.20.0
pip install numpy>=1.24.0
pip install matplotlib>=3.7.0
pip install seaborn>=0.12.0
pip install plotly>=5.14.0
pip install python-dotenv>=1.0.0
pip install python-dateutil>=2.8.0
pip install requests>=2.31.0

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Configure your .env file:
echo    copy .env.example .env
echo    # Edit .env with your Jira credentials
echo.
echo 2. Test connection:
echo    python -c "from jira_scraper import JiraScraper; s = JiraScraper(); s.test_connection()"
echo.
echo 3. Run examples:
echo    python examples\generate_charts_example.py
echo.
echo For more information:
echo   - Python 3.13 compatibility: PYTHON313_COMPATIBILITY.md
echo   - Authentication setup: AUTHENTICATION_GUIDE.md
echo   - Chart features: NEW_CHARTS_DOCUMENTATION.md
echo.

pause
