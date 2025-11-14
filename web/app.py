#!/usr/bin/env python3
"""
FastAPI Web Service for Jira Flow Reports.

This service provides a web interface and API endpoints for generating
and serving Jira flow analysis reports on demand.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Import jira_analyzer modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from jira_analyzer import JiraFetcher, FlowAnalyzer, ReportGenerator


app = FastAPI(
    title="Jira Flow Analyzer API",
    description="Generate and serve Jira flow analysis reports",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Data storage directories
CACHE_DIR = Path("data/cache")
REPORTS_DIR = Path("data/reports")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportRequest(BaseModel):
    """Request model for generating a report."""
    project: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    label: Optional[str] = None
    issue_types: Optional[List[str]] = None
    force_fetch: bool = False


class ReportStatus(BaseModel):
    """Status response for report generation."""
    report_id: str
    status: str  # pending, generating, completed, failed
    message: str
    report_url: Optional[str] = None
    created_at: str


# In-memory storage for report statuses
report_statuses = {}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "jira_url": os.getenv("JIRA_URL", "not_configured")
    }


@app.post("/api/reports/generate", response_model=ReportStatus)
async def generate_report(report_req: ReportRequest, background_tasks: BackgroundTasks):
    """
    Generate a Jira flow report.

    This endpoint initiates report generation as a background task.
    """
    # Generate report ID
    report_id = f"{report_req.project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create status entry
    status = ReportStatus(
        report_id=report_id,
        status="pending",
        message="Report generation queued",
        created_at=datetime.now().isoformat()
    )
    report_statuses[report_id] = status.dict()

    # Add background task
    background_tasks.add_task(
        generate_report_task,
        report_id,
        report_req
    )

    return status


async def generate_report_task(report_id: str, report_req: ReportRequest):
    """Background task to generate a report."""
    try:
        # Update status
        report_statuses[report_id]["status"] = "generating"
        report_statuses[report_id]["message"] = "Fetching issues from Jira..."

        # Set default issue types
        issue_types = report_req.issue_types if report_req.issue_types else ['Bug', 'Błąd w programie']
        issue_type_label = '_'.join([t.lower().replace(' ', '_') for t in issue_types])

        # Cache file path
        cache_file = CACHE_DIR / f"jira_{report_req.project}_{issue_type_label}_cached.json"

        # Check cache or fetch
        if cache_file.exists() and not report_req.force_fetch:
            report_statuses[report_id]["message"] = "Using cached data..."
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            issues = cached_data['issues']
        else:
            report_statuses[report_id]["message"] = "Fetching from Jira API..."
            fetcher = JiraFetcher()
            issues = fetcher.fetch_issues(
                project=report_req.project,
                issue_types=issue_types
            )

            # Save to cache
            cache_data = {
                'metadata': {
                    'project': report_req.project,
                    'issue_types': issue_types,
                    'fetched_at': datetime.now().isoformat(),
                    'total_issues': len(issues)
                },
                'issues': issues
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

        # Analyze flows
        report_statuses[report_id]["message"] = "Analyzing flows..."
        analyzer = FlowAnalyzer(
            issues,
            start_date=report_req.start_date,
            end_date=report_req.end_date,
            label=report_req.label
        )
        flow_metrics = analyzer.calculate_flow_metrics()

        # Generate report
        report_statuses[report_id]["message"] = "Generating HTML report..."
        report_filename = f"{report_id}_{issue_type_label}_flow_report.html"
        report_path = REPORTS_DIR / report_filename

        metadata = {
            'project': report_req.project,
            'fetched_at': datetime.now().isoformat()
        }

        generator = ReportGenerator(
            metadata,
            flow_metrics,
            start_date=report_req.start_date,
            end_date=report_req.end_date,
            jira_url=os.getenv('JIRA_URL')
        )
        generator.generate_html(str(report_path))

        # Update status
        report_statuses[report_id]["status"] = "completed"
        report_statuses[report_id]["message"] = "Report generated successfully"
        report_statuses[report_id]["report_url"] = f"/api/reports/view/{report_id}/{report_filename}"

    except Exception as e:
        report_statuses[report_id]["status"] = "failed"
        report_statuses[report_id]["message"] = f"Error: {str(e)}"


@app.get("/api/reports/status/{report_id}", response_model=ReportStatus)
async def get_report_status(report_id: str):
    """Get the status of a report generation task."""
    if report_id not in report_statuses:
        raise HTTPException(status_code=404, detail="Report not found")

    return report_statuses[report_id]


@app.get("/api/reports/view/{report_id}/{filename}")
async def view_report(report_id: str, filename: str):
    """View a generated report."""
    report_path = REPORTS_DIR / filename

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report_path,
        media_type="text/html",
        filename=filename
    )


@app.get("/api/reports/list")
async def list_reports():
    """List all available reports."""
    reports = []
    for report_file in REPORTS_DIR.glob("*.html"):
        stat = report_file.stat()
        reports.append({
            "filename": report_file.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "url": f"/api/reports/download/{report_file.name}"
        })

    return {"reports": reports}


@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    """Download a report file."""
    report_path = REPORTS_DIR / filename

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report_path,
        media_type="application/octet-stream",
        filename=filename
    )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
