#!/usr/bin/env python3
"""
Shiny App A/B Test Analysis

This script runs a complete analysis pipeline for the A/B test data,
utilizing all modules in the src directory to:
1. Process and analyze the data
2. Run statistical tests
3. Generate visualizations
4. Update the final report with the results

Usage:
    python analyze_ab_test.py

Author: Your Name
Date: April 15, 2025
"""

import os
import sys
import json
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.io as pio

# Add the project root to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from src.data_analysis import load_data, describe_dataset, save_processed_data
from src.statistical_tests import analyze_all_metrics, save_results
from src.visualization import (
    create_metric_comparison_chart,
    create_metrics_overview,
    create_conversion_funnel,
    create_time_spent_chart,
    create_significant_metrics_chart,
    create_statistical_significance_table,
    save_figure
)


def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'data',
        'reports',
        'reports/figures'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    print("Directory structure set up successfully.")


def run_data_analysis(file_path='data/shiny_user_data.csv'):
    """Run the data analysis pipeline."""
    print("\n" + "=" * 80)
    print("STEP 1: DATA ANALYSIS")
    print("=" * 80)

    print("Loading and processing data...")
    df = load_data(file_path)

    print("\nDataset Description:")
    description = describe_dataset(df)
    print(f"Total samples: {description['total_samples']}")
    print(f"Group counts: {description['group_counts']}")

    print("\nSaving processed data...")
    processed_path = 'data/processed_data.csv'
    save_processed_data(df, processed_path)

    return df


def run_statistical_tests(df):
    """Run statistical tests on the data."""
    print("\n" + "=" * 80)
    print("STEP 2: STATISTICAL ANALYSIS")
    print("=" * 80)

    print("Running statistical tests...")
    results = analyze_all_metrics(df)

    # Print significant findings from t-tests
    significant_t_tests = [r for r in results['t_test_results']
                           if 'significant' in r and r['significant']]

    print(f"\nFound {len(significant_t_tests)} significant differences (t-tests):")
    for result in significant_t_tests:
        metric = result['metric'].replace('_', ' ')
        change = result['percent_change']
        direction = "higher" if change > 0 else "lower"

        # Handle special metrics where decrease is positive
        if 'exit' in metric.lower() or 'error' in metric.lower() or 'latency' in metric.lower():
            interpretation = "better" if change < 0 else "worse"
        else:
            interpretation = "better" if change > 0 else "worse"

        print(f"- {metric}: Group B is {abs(change):.2f}% {direction} than Group A" +
              f" (p={result['p_value']:.4f}) [{interpretation}]")

    # Save results
    results_path = 'reports/statistical_results.json'
    save_results(results, results_path)

    return results


def generate_visualizations(df, results):
    """Generate all visualizations."""
    print("\n" + "=" * 80)
    print("STEP 3: VISUALIZATION")
    print("=" * 80)

    print("Generating visualizations...")

    # Key metrics to analyze
    key_metrics = [
        'Task_Completion_Rate',
        'Button_Click_Rate',
        'Plot_Interactions',
        'Early_Exit_Rate',
        'Total_Time_Spent'
    ]

    # 1. Create metrics overview
    print("Creating metrics overview...")
    overview_fig = create_metrics_overview(df, key_metrics)
    save_figure(overview_fig, "metrics_overview")

    # 2. Create individual metric charts for significant metrics
    significant_metrics = [r['metric'] for r in results['t_test_results']
                           if 'significant' in r and r['significant']]

    print(f"Creating individual charts for {len(significant_metrics)} significant metrics...")
    for metric in significant_metrics:
        fig = create_metric_comparison_chart(df, metric)
        save_figure(fig, f"metric_{metric.lower()}")

    # 3. Create time spent chart
    print("Creating time spent chart...")
    time_fig = create_time_spent_chart(df)
    save_figure(time_fig, "time_spent")

    # 4. Create engagement funnel
    print("Creating engagement funnel...")
    funnel_fig = create_conversion_funnel(df)
    save_figure(funnel_fig, "engagement_funnel")

    # 5. Create significant metrics chart
    print("Creating significant metrics chart...")
    sig_fig = create_significant_metrics_chart(df)
    if sig_fig:
        save_figure(sig_fig, "significant_metrics")

    # 6. Create statistical table
    print("Creating statistical table...")
    table_fig = create_statistical_significance_table(df)
    save_figure(table_fig, "statistical_table")

    print("All visualizations created successfully!")

    # Return list of generated files
    figure_dir = Path('reports/figures')
    return list(figure_dir.glob('*.html')), list(figure_dir.glob('*.png'))


def update_final_report(html_files, png_files, results):
    """Update the final report to include visualization references and statistical results."""
    print("\n" + "=" * 80)
    print("STEP 4: UPDATING FINAL REPORT")
    print("=" * 80)

    report_path = 'reports/final_report.md'

    # Check if report exists
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return

    # Read the existing report
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # Update the statistical results table
    print("Updating statistical results table...")

    # Extract t-test results
    t_test_results = results.get('t_test_results', [])

    # Filter for key metrics
    key_metrics = [
        'Button_Click_Rate',
        'Task_Completion_Rate',
        'Plot_Interactions',
        'Early_Exit_Rate',
        'Total_Time_Spent'
    ]

    # Prepare table rows
    table_rows = []

    for metric in key_metrics:
        # Find the result for this metric
        result = next((r for r in t_test_results if r['metric'] == metric), None)

        if result and 'error' not in result:
            group_a_mean = result.get('group_a_mean', 'N/A')
            group_b_mean = result.get('group_b_mean', 'N/A')
            pct_change = result.get('percent_change', 'N/A')
            p_value = result.get('p_value', 'N/A')
            significant = result.get('significant', False)

            # Format values
            if isinstance(group_a_mean, (int, float)):
                group_a_mean = f"{group_a_mean:.2f}"

            if isinstance(group_b_mean, (int, float)):
                group_b_mean = f"{group_b_mean:.2f}"

            if isinstance(pct_change, (int, float)):
                pct_change = f"{'+' if pct_change > 0 else ''}{pct_change:.2f}%"

            if isinstance(p_value, (int, float)):
                p_value = f"{p_value:.4f}"

            sig_text = "Yes" if significant else "No"

            # Create table row
            row = f"| {metric} | {group_a_mean} | {group_b_mean} | {pct_change} | {p_value} | {sig_text} |"
            table_rows.append(row)

    # Find the table in the report
    import re
    table_pattern = r"(\| Metric \| Group A Mean \| Group B Mean \| % Difference \| p-value \| Significant\? \|\n\|[-]+\|[-]+\|[-]+\|[-]+\|[-]+\|[-]+\|)(?:\n\|.*\|.*\|.*\|.*\|.*\|.*\|)*"
    table_match = re.search(table_pattern, report_content)

    if table_match:
        # Construct the new table
        table_header = table_match.group(1)
        new_table = table_header + "\n" + "\n".join(table_rows)

        # Replace the table in the report
        report_content = report_content[:table_match.start()] + new_table + report_content[table_match.end():]

        print("Results table updated successfully!")
    else:
        print("Warning: Could not find the results table in the report.")

    # Create a visualization section if it doesn't exist
    if "## Visualizations" not in report_content:
        # Find the Statistical Analysis section
        stats_section_pos = report_content.find("## Statistical Analysis & Results")
        if stats_section_pos == -1:
            # If not found, add at the end
            insert_pos = len(report_content)
        else:
            # Find the next section after Statistical Analysis
            next_section_pos = report_content.find("##", stats_section_pos + 1)
            if next_section_pos == -1:
                insert_pos = len(report_content)
            else:
                insert_pos = next_section_pos

        # Create visualization section content
        viz_section = "\n\n## Visualizations\n\n"
        viz_section += "The following visualizations illustrate the key findings from our A/B test:\n\n"

        # Add references to each visualization
        viz_files = {Path(f).stem: f for f in png_files}

        if "metrics_overview" in viz_files:
            viz_section += "### Overview of Key Metrics\n\n"
            viz_section += "![Metrics Overview](figures/metrics_overview.png)\n\n"
            viz_section += "This chart compares the key metrics between Group A and Group B, showing the mean values with standard error bars.\n\n"

        if "significant_metrics" in viz_files:
            viz_section += "### Significant Percentage Changes\n\n"
            viz_section += "![Significant Metrics](figures/significant_metrics.png)\n\n"
            viz_section += "This chart shows the percentage change in metrics that showed statistically significant differences between groups.\n\n"

        if "time_spent" in viz_files:
            viz_section += "### Time Spent by Section\n\n"
            viz_section += "![Time Spent](figures/time_spent.png)\n\n"
            viz_section += "This chart shows the average time spent in different sections of the application for each group.\n\n"

        if "engagement_funnel" in viz_files:
            viz_section += "### User Engagement Funnel\n\n"
            viz_section += "![Engagement Funnel](figures/engagement_funnel.png)\n\n"
            viz_section += "This funnel chart shows how users progress through different stages of engagement with the application.\n\n"

        # Add individual metric charts
        individual_metrics = [f for f in viz_files if f.startswith("metric_")]
        if individual_metrics:
            viz_section += "### Individual Metric Comparisons\n\n"
            for metric_file in individual_metrics[:3]:  # Limit to first 3 to avoid clutter
                clean_name = metric_file.replace("metric_", "").replace("_", " ").title()
                viz_section += f"![{clean_name}](figures/{metric_file}.png)\n\n"

        # Insert the visualization section
        report_content = report_content[:insert_pos] + viz_section + report_content[insert_pos:]

        print(f"Final report updated with visualizations section at {report_path}")
    else:
        print("Visualization section already exists in the report. No changes made.")

    # Write updated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"Final report updated successfully at {report_path}")


def main():
    """Main function to run the full analysis pipeline."""
    print("=" * 80)
    print("SHINY APP A/B TEST ANALYSIS")
    print("=" * 80)

    # Set default Plotly renderer for inline display
    pio.renderers.default = "browser"

    # Setup directories
    setup_directories()

    # Run data analysis
    df = run_data_analysis()

    # Run statistical tests
    results = run_statistical_tests(df)

    # Generate visualizations
    html_files, png_files = generate_visualizations(df, results)

    # Update final report with visualizations and statistical results
    update_final_report(html_files, png_files, results)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nFinal report available at: {os.path.abspath('reports/final_report.md')}")
    print(f"Visualizations available in: {os.path.abspath('reports/figures')}")

    # Open a few key visualizations in browser
    key_visualizations = [
        'reports/figures/metrics_overview.html',
        'reports/figures/significant_metrics.html',
        'reports/figures/engagement_funnel.html'
    ]

    for viz_path in key_visualizations:
        if os.path.exists(viz_path):
            try:
                print(f"\nOpening visualization: {viz_path}")
                fig = pio.read_html(viz_path)
                fig.show()
            except Exception as e:
                print(f"Error displaying visualization: {e}")


if __name__ == "__main__":
    main()