"""Issue trends visualization module - daily open, raised, and closed issues with trend lines."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


class IssueTrendsChart:
    """Generates charts for daily issue trends with trend lines."""

    def __init__(self, tickets: List[Dict[str, Any]]):
        """
        Initialize with ticket data.

        Args:
            tickets: List of ticket dictionaries from JiraScraper
        """
        self.tickets = tickets
        self.df: Optional[pl.DataFrame] = None

    def build_dataframe(self) -> pl.DataFrame:
        """
        Convert raw ticket data into Polars DataFrame.

        Returns:
            DataFrame with ticket data
        """
        ticket_records = []
        for ticket in self.tickets:
            ticket_records.append({
                "key": ticket["key"],
                "created": datetime.fromisoformat(ticket["created"].replace("Z", "+00:00")),
                "updated": datetime.fromisoformat(ticket["updated"].replace("Z", "+00:00")),
                "resolved": datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                if ticket.get("resolved") else None,
                "status": ticket["status"],
            })

        self.df = pl.DataFrame(ticket_records)
        return self.df

    def calculate_daily_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate daily metrics for issues raised and closed.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily metrics
        """
        from datetime import timezone

        if self.df is None:
            self.build_dataframe()

        # Create timezone-aware datetimes to match DataFrame columns
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate date range with timezone
        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []
        for current_date in date_range:
            # Issues raised on this day
            raised = self.df.filter(
                pl.col("created").dt.date() == current_date.date()
            ).height

            # Issues closed on this day
            closed = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved").dt.date() == current_date.date())
            ).height

            daily_metrics.append({
                "date": current_date,
                "issues_raised": raised,
                "issues_closed": closed,
            })

        return pl.DataFrame(daily_metrics)

    @staticmethod
    def calculate_trend_line(dates: List[datetime], values: List[float]) -> List[float]:
        """
        Calculate linear trend line using least squares regression.

        Args:
            dates: List of datetime objects
            values: List of corresponding values

        Returns:
            List of trend line values
        """
        # Convert dates to numeric values (days since first date)
        if not dates or not values:
            return []

        x = np.array([(d - dates[0]).days for d in dates])
        y = np.array(values)

        # Calculate linear regression
        coefficients = np.polyfit(x, y, 1)
        trend = np.polyval(coefficients, x)

        return trend.tolist()

    def create_combined_chart(
        self,
        start_date: str,
        end_date: str,
        title: str = "Daily Issue Trends"
    ) -> str:
        """
        Create combined chart with raised and closed metrics and trend lines.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics_df = self.calculate_daily_metrics(start_date, end_date)

        dates = metrics_df["date"].to_list()
        raised = metrics_df["issues_raised"].to_list()
        closed = metrics_df["issues_closed"].to_list()

        # Calculate trend lines
        raised_trend = self.calculate_trend_line(dates, raised)
        closed_trend = self.calculate_trend_line(dates, closed)

        # Create figure
        fig = go.Figure()

        # Issues Raised
        fig.add_trace(go.Scatter(
            x=dates,
            y=raised,
            name="Issues Raised",
            mode="lines+markers",
            line=dict(color="#3498db", width=2),
            marker=dict(size=4),
        ))
        fig.add_trace(go.Scatter(
            x=dates,
            y=raised_trend,
            name="Raised Trend",
            mode="lines",
            line=dict(color="#3498db", width=2, dash="dash"),
            showlegend=True,
        ))

        # Issues Closed
        fig.add_trace(go.Scatter(
            x=dates,
            y=closed,
            name="Issues Closed",
            mode="lines+markers",
            line=dict(color="#2ecc71", width=2),
            marker=dict(size=4),
        ))
        fig.add_trace(go.Scatter(
            x=dates,
            y=closed_trend,
            name="Closed Trend",
            mode="lines",
            line=dict(color="#2ecc71", width=2, dash="dash"),
            showlegend=True,
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Issues",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def create_separate_charts(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, str]:
        """
        Create two separate charts for each metric with trend lines.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with HTML strings for each chart
        """
        metrics_df = self.calculate_daily_metrics(start_date, end_date)

        dates = metrics_df["date"].to_list()
        raised = metrics_df["issues_raised"].to_list()
        closed = metrics_df["issues_closed"].to_list()

        # Calculate trend lines
        raised_trend = self.calculate_trend_line(dates, raised)
        closed_trend = self.calculate_trend_line(dates, closed)

        charts = {}

        # Issues Raised Chart
        fig_raised = go.Figure()
        fig_raised.add_trace(go.Scatter(
            x=dates, y=raised,
            name="Issues Raised",
            mode="lines+markers",
            line=dict(color="#3498db", width=2),
            marker=dict(size=6),
        ))
        fig_raised.add_trace(go.Scatter(
            x=dates, y=raised_trend,
            name="Trend",
            mode="lines",
            line=dict(color="#3498db", width=2, dash="dash"),
        ))
        fig_raised.update_layout(
            title="Issues Raised Day by Day",
            xaxis_title="Date",
            yaxis_title="Issues Raised",
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )
        charts["raised"] = fig_raised.to_html(full_html=False, include_plotlyjs="cdn")

        # Issues Closed Chart
        fig_closed = go.Figure()
        fig_closed.add_trace(go.Scatter(
            x=dates, y=closed,
            name="Issues Closed",
            mode="lines+markers",
            line=dict(color="#2ecc71", width=2),
            marker=dict(size=6),
        ))
        fig_closed.add_trace(go.Scatter(
            x=dates, y=closed_trend,
            name="Trend",
            mode="lines",
            line=dict(color="#2ecc71", width=2, dash="dash"),
        ))
        fig_closed.update_layout(
            title="Issues Closed Day by Day",
            xaxis_title="Date",
            yaxis_title="Issues Closed",
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )
        charts["closed"] = fig_closed.to_html(full_html=False, include_plotlyjs="cdn")

        return charts

    def get_summary_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get summary statistics for the date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with summary statistics
        """
        metrics_df = self.calculate_daily_metrics(start_date, end_date)

        return {
            "total_raised": metrics_df["issues_raised"].sum(),
            "total_closed": metrics_df["issues_closed"].sum(),
            "avg_raised_per_day": metrics_df["issues_raised"].mean(),
            "avg_closed_per_day": metrics_df["issues_closed"].mean(),
            "net_change": metrics_df["issues_raised"].sum() - metrics_df["issues_closed"].sum(),
        }
