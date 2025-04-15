"""
Visualization Module for Shiny App A/B Test

This module creates visualizations to compare metrics between Groups A and B
in the A/B test experiment using Plotly.
"""

import os
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path


def create_metric_comparison_chart(df, metric, title=None):
    """
    Create a box plot comparing a metric between groups A and B.

    Args:
        df (pandas.DataFrame): The processed dataset
        metric (str): The column name of the metric to visualize
        title (str, optional): Custom title for the plot

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    if title is None:
        title = f"Comparison of {metric.replace('_', ' ')} Between Groups"

    # Create the figure
    fig = px.box(
        df,
        x="Group",
        y=metric,
        color="Group",
        title=title,
        points="all",  # Show all data points
        color_discrete_map={"A": "#636EFA", "B": "#EF553B"}
    )

    # Add mean markers
    for group in ['A', 'B']:
        group_data = df[df['Group'] == group][metric].dropna()
        if not group_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=[group],
                    y=[group_data.mean()],
                    mode="markers",
                    marker=dict(
                        symbol="star",
                        size=12,
                        color="yellow",
                        line=dict(width=1, color="black")
                    ),
                    name=f"Mean ({group})"
                )
            )

    # Update layout
    fig.update_layout(
        yaxis_title=metric.replace('_', ' '),
        showlegend=True,
        boxmode='group',
        template='plotly_white'
    )

    return fig


def create_metrics_overview(df, metrics=None):
    """
    Create a subplot with multiple metrics comparisons.

    Args:
        df (pandas.DataFrame): The processed dataset
        metrics (list, optional): List of metrics to include

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    if metrics is None:
        # Use all numeric columns except User_ID
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metrics = [col for col in numeric_cols if col != 'User_ID']

    # Calculate the grid dimensions (approximately square)
    n_metrics = len(metrics)
    n_cols = int(np.ceil(np.sqrt(n_metrics)))
    n_rows = int(np.ceil(n_metrics / n_cols))

    # Create subplot figure
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[metric.replace('_', ' ') for metric in metrics]
    )

    # Add each metric as a bar chart
    for i, metric in enumerate(metrics):
        row = i // n_cols + 1
        col = i % n_cols + 1

        # Calculate statistics for each group
        stats = []
        for group in ['A', 'B']:
            group_data = df[df['Group'] == group][metric].dropna()
            if not group_data.empty:
                stats.append({
                    'Group': group,
                    'Mean': group_data.mean(),
                    'StdErr': group_data.std() / np.sqrt(len(group_data))
                })

        if stats:
            stats_df = pd.DataFrame(stats)

            # Add bar chart
            fig.add_trace(
                go.Bar(
                    x=stats_df['Group'],
                    y=stats_df['Mean'],
                    error_y=dict(
                        type='data',
                        array=stats_df['StdErr'],
                        visible=True
                    ),
                    name=metric,
                    showlegend=False,
                    marker_color=['#636EFA', '#EF553B']
                ),
                row=row, col=col
            )

            # Set y-axis title
            fig.update_yaxes(
                title_text=metric.replace('_', ' '),
                row=row, col=col
            )

    # Update layout
    fig.update_layout(
        title_text="Comparison of Key Metrics Between Groups",
        template='plotly_white',
        height=250 * n_rows,
        width=300 * n_cols,
        showlegend=False
    )

    return fig


def create_conversion_funnel(df):
    """
    Create a conversion funnel visualization.

    Args:
        df (pandas.DataFrame): The processed dataset

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Metrics for the funnel (in descending order)
    funnel_metrics = [
        'Module_Navigation_Depth',
        'Button_Click_Rate',
        'Plot_Interactions',
        'Task_Completion_Rate'
    ]

    # Calculate average for each metric by group
    funnel_data = []
    for group in ['A', 'B']:
        group_df = df[df['Group'] == group]

        for metric in funnel_metrics:
            metric_name = metric.replace('_', ' ')
            avg_value = group_df[metric].mean()

            funnel_data.append({
                'Group': group,
                'Metric': metric_name,
                'Average': avg_value
            })

    # Create dataframe from the funnel data
    funnel_df = pd.DataFrame(funnel_data)

    # Create the funnel chart
    fig = px.funnel(
        funnel_df,
        x='Average',
        y='Metric',
        color='Group',
        color_discrete_map={"A": "#636EFA", "B": "#EF553B"}
    )

    # Update layout
    fig.update_layout(
        title_text="User Engagement Funnel by Group",
        template='plotly_white',
        height=500,
        width=700
    )

    return fig


def create_time_spent_chart(df):
    """
    Create a visualization for time spent in different sections.

    Args:
        df (pandas.DataFrame): The processed dataset

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Time sections to analyze
    time_sections = ['Time_data_upload', 'Time_data_cleaning',
                    'Time_feature_engineering', 'Time_exploratory_analysis']

    # Create a dataframe for time spent by section and group
    time_data = []

    for group in ['A', 'B']:
        group_df = df[df['Group'] == group]

        for section in time_sections:
            clean_name = section.replace('Time_', '').replace('_', ' ').title()

            time_data.append({
                'Group': group,
                'Section': clean_name,
                'Average Time (seconds)': group_df[section].mean()
            })

    # Create dataframe
    time_df = pd.DataFrame(time_data)

    # Create the grouped bar chart
    fig = px.bar(
        time_df,
        x='Section',
        y='Average Time (seconds)',
        color='Group',
        barmode='group',
        color_discrete_map={"A": "#636EFA", "B": "#EF553B"},
        title="Average Time Spent in Each Section by Group"
    )

    # Update layout
    fig.update_layout(
        xaxis_title="Application Section",
        yaxis_title="Average Time (seconds)",
        template='plotly_white',
        height=500,
        width=800
    )

    return fig


def create_significant_metrics_chart(df, results_path='reports/statistical_results.json'):
    """
    Create a chart highlighting statistically significant metrics.

    Args:
        df (pandas.DataFrame): The processed dataset
        results_path (str): Path to the statistical results JSON file

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Check if results file exists, if not use default metrics
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Get significant t-test results
        t_test_results = results.get('t_test_results', [])
        significant_metrics = [
            r['metric'] for r in t_test_results
            if 'significant' in r and r['significant']
        ]
    else:
        # Use default metrics if results file doesn't exist
        significant_metrics = [
            'Task_Completion_Rate',
            'Button_Click_Rate',
            'Plot_Interactions',
            'Early_Exit_Rate'
        ]

    # Filter metrics and prepare data
    if not significant_metrics:
        # No significant metrics found
        return None

    # Create a figure showing percentage change in significant metrics
    sig_data = []

    for metric in significant_metrics:
        group_a = df[df['Group'] == 'A'][metric].mean()
        group_b = df[df['Group'] == 'B'][metric].mean()

        # Calculate percentage change
        if group_a != 0:
            pct_change = ((group_b - group_a) / abs(group_a)) * 100
        else:
            pct_change = 0

        sig_data.append({
            'Metric': metric.replace('_', ' '),
            'Percentage Change': pct_change
        })

    # Create dataframe
    sig_df = pd.DataFrame(sig_data)

    # Determine colors - green for positive changes (usually good)
    # except for Early_Exit_Rate where negative is better
    colors = []
    for _, row in sig_df.iterrows():
        metric_name = row['Metric'].lower()
        change = row['Percentage Change']

        if 'exit' in metric_name or 'error' in metric_name or 'latency' in metric_name:
            # For these metrics, negative change is good
            colors.append('#00CC96' if change < 0 else '#EF553B')
        else:
            # For other metrics, positive change is good
            colors.append('#00CC96' if change > 0 else '#EF553B')

    # Create horizontal bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=sig_df['Metric'],
            x=sig_df['Percentage Change'],
            orientation='h',
            marker_color=colors,
            text=[f"{val:+.1f}%" for val in sig_df['Percentage Change']],
            textposition='outside'
        )
    )

    # Add a reference line at 0%
    fig.add_shape(
        type='line',
        x0=0, y0=-0.5,
        x1=0, y1=len(sig_df) - 0.5,
        line=dict(color='black', width=1)
    )

    # Update layout
    fig.update_layout(
        title="Percentage Change in Significant Metrics (Group B vs Group A)",
        xaxis_title="Percentage Change (%)",
        template='plotly_white',
        height=400,
        width=800,
        margin=dict(l=150)  # Add left margin for metric names
    )

    return fig


def create_statistical_significance_table(df, results_path='reports/statistical_results.json'):
    """
    Create a table visualization showing statistical test results.

    Args:
        df (pandas.DataFrame): The processed dataset
        results_path (str): Path to the statistical results JSON file

    Returns:
        plotly.graph_objects.Figure: Plotly figure object
    """
    # Check if results file exists, if not compute results
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Get t-test results
        t_test_results = results.get('t_test_results', [])
    else:
        # Basic computation of results
        from scipy import stats

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metrics = [col for col in numeric_cols if col != 'User_ID']

        t_test_results = []
        for metric in metrics:
            group_a = df[df['Group'] == 'A'][metric].dropna()
            group_b = df[df['Group'] == 'B'][metric].dropna()

            if len(group_a) >= 2 and len(group_b) >= 2:
                t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)

                t_test_results.append({
                    'metric': metric,
                    'group_a_mean': group_a.mean(),
                    'group_b_mean': group_b.mean(),
                    'p_value': p_value,
                    'significant': p_value < 0.05
                })

    # Prepare data for table
    table_data = []

    for result in t_test_results:
        if 'error' not in result:
            metric = result['metric']
            p_value = result['p_value']
            significant = result.get('significant', False)

            # Calculate percent change
            group_a_mean = result['group_a_mean']
            group_b_mean = result['group_b_mean']

            if group_a_mean != 0:
                pct_change = ((group_b_mean - group_a_mean) / abs(group_a_mean)) * 100
            else:
                pct_change = 0

            table_data.append({
                'Metric': metric.replace('_', ' '),
                'Group A': f"{group_a_mean:.2f}",
                'Group B': f"{group_b_mean:.2f}",
                'Difference': f"{group_b_mean - group_a_mean:+.2f}",
                'Change': f"{pct_change:+.2f}%",
                'P-value': f"{p_value:.4f}",
                'Significant': "Yes" if significant else "No"
            })

    # Sort by significance and p-value
    table_data = sorted(table_data, key=lambda x: (0 if x['Significant'] == "Yes" else 1, float(x['P-value'].replace("p=", ""))))

    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(table_data[0].keys()),
            fill_color='#0072B2',
            align='center',
            font=dict(color='white', size=12)
        ),
        cells=dict(
            values=[
                [row['Metric'] for row in table_data],
                [row['Group A'] for row in table_data],
                [row['Group B'] for row in table_data],
                [row['Difference'] for row in table_data],
                [row['Change'] for row in table_data],
                [row['P-value'] for row in table_data],
                [row['Significant'] for row in table_data]
            ],
            fill_color=[
                ['white'] * len(table_data),
                ['white'] * len(table_data),
                ['white'] * len(table_data),
                ['white'] * len(table_data),
                ['white'] * len(table_data),
                ['white'] * len(table_data),
                [['#E8F4F8' if row['Significant'] == 'Yes' else 'white'] for row in table_data]
            ],
            align='center'
        )
    )])

    # Update layout
    fig.update_layout(
        title="Statistical Test Results (Group B vs Group A)",
        template='plotly_white',
        height=400,
        width=800
    )

    return fig


def save_figure(fig, filename, output_dir='reports/figures'):
    """
    Save a Plotly figure to HTML and image files.

    Args:
        fig (plotly.graph_objects.Figure): Plotly figure to save
        filename (str): Base filename without extension
        output_dir (str): Directory to save the files
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save as HTML (interactive)
    html_path = os.path.join(output_dir, f"{filename}.html")
    fig.write_html(html_path)

    # Save as PNG (static)
    png_path = os.path.join(output_dir, f"{filename}.png")
    fig.write_image(png_path)

    print(f"Figure saved to {html_path} and {png_path}")


def main():
    """Main function to create and save all visualizations."""
    from .data_analysis import load_data

    print("Loading processed data...")
    df = load_data()

    print("\nCreating visualizations...")

    # Create directory structure
    os.makedirs('reports/figures', exist_ok=True)

    # 1. Create and save key metrics comparison chart
    print("Creating metrics overview chart...")
    key_metrics = [
        'Task_Completion_Rate',
        'Button_Click_Rate',
        'Plot_Interactions',
        'Early_Exit_Rate',
        'Total_Time_Spent'
    ]
    overview_fig = create_metrics_overview(df, key_metrics)
    save_figure(overview_fig, "metrics_overview")

    # 2. Create and save individual metric charts
    print("Creating individual metric charts...")
    for metric in key_metrics:
        metric_fig = create_metric_comparison_chart(df, metric)
        save_figure(metric_fig, f"metric_{metric.lower()}")

    # 3. Create and save conversion funnel
    print("Creating conversion funnel chart...")
    funnel_fig = create_conversion_funnel(df)
    save_figure(funnel_fig, "conversion_funnel")

    # 4. Create and save time spent chart
    print("Creating time spent chart...")
    time_fig = create_time_spent_chart(df)
    save_figure(time_fig, "time_spent")

    # 5. Create and save significant metrics chart
    print("Creating significant metrics chart...")
    sig_fig = create_significant_metrics_chart(df)
    if sig_fig:
        save_figure(sig_fig, "significant_metrics")

    # 6. Create and save statistical table
    print("Creating statistical table...")
    table_fig = create_statistical_significance_table(df)
    save_figure(table_fig, "statistical_table")

    print("\nAll visualizations created successfully!")


if __name__ == "__main__":
    main()