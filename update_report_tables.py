#!/usr/bin/env python3
"""
Update Report Tables Script

This script reads the statistical_results.json file and updates
the tables in the final report with the actual results.
"""

import json
import os
import re
from pathlib import Path


def update_results_table(report_path, results_path):
    """
    Update the statistical results table in the report with actual values.

    Args:
        report_path (str): Path to the final report markdown file
        results_path (str): Path to the statistical results JSON file
    """
    print(f"Updating results table in {report_path}...")

    # Check if files exist
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        return

    if not os.path.exists(results_path):
        print(f"Error: Results file not found at {results_path}")
        return

    # Load statistical results
    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Extract t-test results
    t_test_results = results.get('t_test_results', [])

    # Filter for significant results and key metrics
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

    # Read the report content
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # Find the table in the report
    table_pattern = r"(\| Metric \| Group A Mean \| Group B Mean \| % Difference \| p-value \| Significant\? \|\n\|[-]+\|[-]+\|[-]+\|[-]+\|[-]+\|[-]+\|)(?:\n\|.*\|.*\|.*\|.*\|.*\|.*\|)*"
    table_match = re.search(table_pattern, report_content)

    if table_match:
        # Construct the new table
        table_header = table_match.group(1)
        new_table = table_header + "\n" + "\n".join(table_rows)

        # Replace the table in the report
        updated_report = report_content[:table_match.start()] + new_table + report_content[table_match.end():]

        # Write the updated report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(updated_report)

        print("Results table updated successfully!")
    else:
        print("Warning: Could not find the results table in the report.")


def main():
    """Main function."""
    report_path = 'reports/final_report.md'
    results_path = 'reports/statistical_results.json'

    update_results_table(report_path, results_path)


if __name__ == "__main__":
    main()