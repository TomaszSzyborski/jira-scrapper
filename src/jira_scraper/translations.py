"""Translation module for multilingual report support."""

from typing import Dict, Any


class Translations:
    """Translations for English and Polish languages."""

    LANGUAGES = {
        "en": {
            # Header and Navigation
            "report_title": "Jira Report",
            "generated_at": "Generated at",
            "date_range": "Date Range",
            "language": "Language",
            
            # Sections
            "executive_summary": "Executive Summary",
            "daily_issue_trends": "Daily Issue Trends",
            "status_category_distribution": "Status Category Distribution",
            "in_progress_tracking": "In Progress Tracking",
            "bug_tracking": "Bug Tracking",
            "test_execution_progress": "Test Execution Progress",
            "xray_test_execution": "Xray Test Execution Progress (Legacy)",
            "flow_analysis": "Flow Analysis",
            "temporal_trends": "Temporal Trends",
            "cycle_metrics": "Cycle Time Metrics",
            "status_distribution": "Status Distribution",
            
            # Chart Titles
            "issues_raised_closed": "Daily Issue Trends (Raised vs Closed)",
            "status_category_chart": "Status Category Distribution Day by Day",
            "issues_not_done": "Issues Not Done (statusCategory != Done) Day by Day",
            "bug_tracking_chart": "Daily Bug Tracking - Created vs Closed",
            "test_execution_chart": "Cumulative Test Execution Progress",
            
            # Statistics Cards
            "total_tickets": "Total Tickets",
            "resolved_tickets": "Resolved Tickets",
            "avg_lead_time": "Avg Lead Time",
            "avg_cycle_time": "Avg Cycle Time",
            "total_raised": "Total Raised",
            "total_closed": "Total Closed",
            "avg_raised_per_day": "Avg Raised/Day",
            "avg_closed_per_day": "Avg Closed/Day",
            "net_change": "Net Change",
            "avg_todo": "Avg To Do",
            "avg_in_progress": "Avg In Progress",
            "avg_done": "Avg Done",
            "currently_not_done": "Currently Not Done",
            "max_in_progress": "Max In Progress",
            "min_in_progress": "Min In Progress",
            "currently_in_progress": "Currently In Progress",
            "total_bugs_created": "Total Bugs Created",
            "total_bugs_closed": "Total Bugs Closed",
            "currently_open_bugs": "Currently Open Bugs",
            "total_test_executions": "Test Executions",
            "total_test_cases": "Total Test Cases",
            "current_test_executions": "Current Test Executions",
            "cumulative_test_case_statuses": "Cumulative Test Case Statuses",
            "passed": "Passed",
            "failed": "Failed",
            "remaining": "Remaining",
            "created": "Created",
            
            # Chart Labels
            "issues_raised": "Issues Raised",
            "issues_closed": "Issues Closed",
            "raised_trend": "Raised Trend",
            "closed_trend": "Closed Trend",
            "not_done": "Not Done (In Progress)",
            "trend": "Trend",
            "to_do": "To Do",
            "in_progress": "In Progress",
            "done": "Done",
            "bugs_created": "Bugs Created",
            "bugs_closed": "Bugs Closed",
            "created_trend": "Created Trend",
            "executing": "Executing",
            "aborted": "Aborted",
            
            # Axes Labels
            "date": "Date",
            "number_of_issues": "Number of Issues",
            "number_of_issues_not_done": "Number of Issues Not Done",
            "number_of_bugs": "Number of Bugs",
            "number_of_tests": "Number of Tests",
            
            # Drilldown
            "bug_details_by_date": "Bug Details by Date",
            "click_to_see_details": "Click on a date to see bug details",
            "bugs_created_on": "Bugs Created on",
            "bugs_closed_on": "Bugs Closed on",
            "in_progress_issues_by_date": "In Progress Issues by Date",
            "click_to_see_in_progress": "Click on a date to see issues that were in progress",
            "issues_in_progress_on": "Issues In Progress on",
            "test_execution_details": "Test Execution Details",
            "click_to_see_test_details": "Click on a date to see test execution details",
            
            # Table Headers
            "key": "Key",
            "summary": "Summary",
            "status": "Status",
            "priority": "Priority",
            "assignee": "Assignee",
            "updated": "Updated",
            
            # Common
            "days": "days",
            "tickets": "tickets",
            "in_progress_count": "in progress",
            "label": "Label",
        },
        
        "pl": {
            # Header and Navigation
            "report_title": "Raport Jira",
            "generated_at": "Wygenerowano",
            "date_range": "Zakres dat",
            "language": "Język",
            
            # Sections
            "executive_summary": "Podsumowanie wykonawcze",
            "daily_issue_trends": "Dzienne trendy zadań",
            "status_category_distribution": "Rozkład kategorii statusów",
            "in_progress_tracking": "Śledzenie w trakcie",
            "bug_tracking": "Śledzenie błędów",
            "test_execution_progress": "Postęp wykonania testów",
            "xray_test_execution": "Postęp wykonania testów Xray (Starsza wersja)",
            "flow_analysis": "Analiza przepływu",
            "temporal_trends": "Trendy czasowe",
            "cycle_metrics": "Metryki czasu cyklu",
            "status_distribution": "Rozkład statusów",
            
            # Chart Titles
            "issues_raised_closed": "Dzienne trendy zadań (Utworzone vs Zamknięte)",
            "status_category_chart": "Rozkład kategorii statusów dzień po dniu",
            "issues_not_done": "Zadania niezakończone (statusCategory != Done) dzień po dniu",
            "bug_tracking_chart": "Dzienne śledzenie błędów - Utworzone vs Zamknięte",
            "test_execution_chart": "Kumulatywny postęp wykonania testów",
            
            # Statistics Cards
            "total_tickets": "Wszystkie zadania",
            "resolved_tickets": "Rozwiązane zadania",
            "avg_lead_time": "Średni czas realizacji",
            "avg_cycle_time": "Średni czas cyklu",
            "total_raised": "Wszystkie utworzone",
            "total_closed": "Wszystkie zamknięte",
            "avg_raised_per_day": "Średnio utworzonych/dzień",
            "avg_closed_per_day": "Średnio zamkniętych/dzień",
            "net_change": "Zmiana netto",
            "avg_todo": "Średnio do zrobienia",
            "avg_in_progress": "Średnio w trakcie",
            "avg_done": "Średnio ukończone",
            "currently_not_done": "Obecnie nieukończone",
            "max_in_progress": "Max w trakcie",
            "min_in_progress": "Min w trakcie",
            "currently_in_progress": "Obecnie w trakcie",
            "total_bugs_created": "Wszystkie błędy utworzone",
            "total_bugs_closed": "Wszystkie błędy zamknięte",
            "currently_open_bugs": "Obecnie otwarte błędy",
            "total_test_executions": "Wykonania testów",
            "total_test_cases": "Wszystkie przypadki testowe",
            "current_test_executions": "Bieżące wykonania testów",
            "cumulative_test_case_statuses": "Skumulowane statusy przypadków testowych",
            "passed": "Zaliczone",
            "failed": "Niezaliczone",
            "remaining": "Pozostałe",
            "created": "Utworzono",
            
            # Chart Labels
            "issues_raised": "Zadania utworzone",
            "issues_closed": "Zadania zamknięte",
            "raised_trend": "Trend utworzonych",
            "closed_trend": "Trend zamkniętych",
            "not_done": "Nieukończone (W trakcie)",
            "trend": "Trend",
            "to_do": "Do zrobienia",
            "in_progress": "W trakcie",
            "done": "Ukończone",
            "bugs_created": "Błędy utworzone",
            "bugs_closed": "Błędy zamknięte",
            "created_trend": "Trend utworzonych",
            "executing": "Wykonywane",
            "aborted": "Przerwane",
            
            # Axes Labels
            "date": "Data",
            "number_of_issues": "Liczba zadań",
            "number_of_issues_not_done": "Liczba nieukończonych zadań",
            "number_of_bugs": "Liczba błędów",
            "number_of_tests": "Liczba testów",
            
            # Drilldown
            "bug_details_by_date": "Szczegóły błędów według daty",
            "click_to_see_details": "Kliknij na datę, aby zobaczyć szczegóły błędów",
            "bugs_created_on": "Błędy utworzone",
            "bugs_closed_on": "Błędy zamknięte",
            "in_progress_issues_by_date": "Zadania w trakcie według daty",
            "click_to_see_in_progress": "Kliknij na datę, aby zobaczyć zadania w trakcie",
            "issues_in_progress_on": "Zadania w trakcie",
            "test_execution_details": "Szczegóły wykonania testów",
            "click_to_see_test_details": "Kliknij na datę, aby zobaczyć szczegóły wykonania testów",
            
            # Table Headers
            "key": "Klucz",
            "summary": "Podsumowanie",
            "status": "Status",
            "priority": "Priorytet",
            "assignee": "Przypisany",
            "updated": "Zaktualizowano",
            
            # Common
            "days": "dni",
            "tickets": "zadań",
            "in_progress_count": "w trakcie",
            "label": "Etykieta",
        }
    }

    @staticmethod
    def get(key: str, lang: str = "en") -> str:
        """
        Get translation for a key in specified language.
        
        Args:
            key: Translation key
            lang: Language code ('en' or 'pl')
            
        Returns:
            Translated string or key if not found
        """
        return Translations.LANGUAGES.get(lang, {}).get(key, key)

    @staticmethod
    def get_all(lang: str = "en") -> Dict[str, str]:
        """
        Get all translations for a language.
        
        Args:
            lang: Language code ('en' or 'pl')
            
        Returns:
            Dictionary of all translations
        """
        return Translations.LANGUAGES.get(lang, Translations.LANGUAGES["en"])

    @staticmethod
    def get_language_switcher_js() -> str:
        """
        Get JavaScript code for language switching.
        
        Returns:
            JavaScript code as string
        """
        return """
        <script>
        // Language switcher functionality
        const translations = """ + str(Translations.LANGUAGES).replace("'", '"') + """;
        
        let currentLang = localStorage.getItem('reportLanguage') || 'en';
        
        function switchLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('reportLanguage', lang);
            updateLanguage();
            
            // Update language selector
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
            
            // Update chart titles (Plotly charts)
            updatePlotlyChartLanguage();
        }
        
        function updatePlotlyChartLanguage() {
            // This would require regenerating charts with new language
            // For now, we'll just update text elements we can access
            const trans = translations[currentLang];
            
            // Update section titles
            document.querySelectorAll('.section-title').forEach(title => {
                const key = title.getAttribute('data-i18n');
                if (key && trans[key]) {
                    title.textContent = trans[key];
                }
            });
        }
        
        // Initialize language on page load
        document.addEventListener('DOMContentLoaded', function() {
            switchLanguage(currentLang);
        });
        </script>
        """


def get_translations_json() -> str:
    """
    Get translations as JSON string for embedding in HTML.
    
    Returns:
        JSON string of all translations
    """
    import json
    return json.dumps(Translations.LANGUAGES, ensure_ascii=False, indent=2)
