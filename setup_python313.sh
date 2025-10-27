#!/bin/bash
# Setup script for Python 3.13 compatibility

echo "========================================="
echo "Jira Scraper - Python 3.13 Setup"
echo "========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if Python 3.13
if [[ $PYTHON_VERSION == 3.13.* ]]; then
    echo "✓ Python 3.13 detected"
    echo ""
    echo "Installing atlassian-python-api for Python 3.13 compatibility..."
    echo ""

    # Install atlassian-python-api
    pip install atlassian-python-api>=3.41.0

    echo ""
    echo "Replacing scraper.py with Python 3.13 compatible version..."

    # Backup original scraper
    if [ -f "src/jira_scraper/scraper.py" ]; then
        cp src/jira_scraper/scraper.py src/jira_scraper/scraper_original_backup.py
        echo "✓ Backed up original scraper to scraper_original_backup.py"
    fi

    # Copy Python 3.13 compatible version
    cp src/jira_scraper/scraper_py313.py src/jira_scraper/scraper.py
    echo "✓ Installed Python 3.13 compatible scraper"

else
    echo "✓ Python $PYTHON_VERSION detected (not 3.13)"
    echo ""
    echo "Installing jira library (standard version)..."
    echo ""

    # Install jira library
    pip install jira>=3.5.0
fi

echo ""
echo "Installing other dependencies..."
echo ""

# Install other requirements
pip install polars>=0.20.0
pip install numpy>=1.24.0
pip install matplotlib>=3.7.0
pip install seaborn>=0.12.0
pip install plotly>=5.14.0
pip install python-dotenv>=1.0.0
pip install python-dateutil>=2.8.0
pip install requests>=2.31.0

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure your .env file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your Jira credentials"
echo ""
echo "2. Test connection:"
echo "   python -c 'from jira_scraper import JiraScraper; s = JiraScraper(); s.test_connection()'"
echo ""
echo "3. Run examples:"
echo "   python examples/generate_charts_example.py"
echo ""
echo "For more information:"
echo "  - Python 3.13 compatibility: PYTHON313_COMPATIBILITY.md"
echo "  - Authentication setup: AUTHENTICATION_GUIDE.md"
echo "  - Chart features: NEW_CHARTS_DOCUMENTATION.md"
echo ""
