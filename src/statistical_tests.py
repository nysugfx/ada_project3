"""
Statistical Testing Module for Shiny App A/B Test

This module implements statistical tests to analyze differences between
Groups A and B in the A/B test experiment.
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import json


def run_t_test(df, metric, alpha=0.05):
    """
    Run a t-test to compare a metric between groups.

    Args:
        df (pandas.DataFrame): The dataset
        metric (str): The column name of the metric to compare
        alpha (float): Significance level

    Returns:
        dict: Dictionary containing test results
    """
    group_a = df[df['Group'] == 'A'][metric].dropna()
    group_b = df[df['Group'] == 'B'][metric].dropna()

    # Check if there's enough data
    if len(group_a) < 2 or len(group_b) < 2:
        return {
            'metric': metric,
            'test': 't-test',
            'error': 'Insufficient data for t-test'
        }

    # Run the t-test
    t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(((len(group_a) - 1) * group_a.std() ** 2 +
                          (len(group_b) - 1) * group_b.std() ** 2) /
                         (len(group_a) + len(group_b) - 2))

    effect_size = abs(group_a.mean() - group_b.mean()) / pooled_std if pooled_std > 0 else 0

    return {
        'metric': metric,
        'test': 't-test',
        'group_a_mean': group_a.mean(),
        'group_b_mean': group_b.mean(),
        'difference': group_b.mean() - group_a.mean(),
        'percent_change': ((group_b.mean() - group_a.mean()) / group_a.mean() * 100) if group_a.mean() != 0 else np.nan,
        't_statistic': t_stat,
        'p_value': p_value,
        'effect_size': effect_size,
        'significant': p_value < alpha,
        'sample_size_a': len(group_a),
        'sample_size_b': len(group_b)
    }


def run_mann_whitney_test(df, metric, alpha=0.05):
    """
    Run a Mann-Whitney U test to compare a metric between groups.

    Args:
        df (pandas.DataFrame): The dataset
        metric (str): The column name of the metric to compare
        alpha (float): Significance level

    Returns:
        dict: Dictionary containing test results
    """
    group_a = df[df['Group'] == 'A'][metric].dropna()
    group_b = df[df['Group'] == 'B'][metric].dropna()

    # Check if there's enough data
    if len(group_a) < 1 or len(group_b) < 1:
        return {
            'metric': metric,
            'test': 'mann-whitney',
            'error': 'Insufficient data for Mann-Whitney test'
        }

    # Run the Mann-Whitney U test
    u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')

    return {
        'metric': metric,
        'test': 'mann-whitney',
        'group_a_median': group_a.median(),
        'group_b_median': group_b.median(),
        'difference': group_b.median() - group_a.median(),
        'percent_change': ((
                                       group_b.median() - group_a.median()) / group_a.median() * 100) if group_a.median() != 0 else np.nan,
        'u_statistic': u_stat,
        'p_value': p_value,
        'significant': p_value < alpha,
        'sample_size_a': len(group_a),
        'sample_size_b': len(group_b)
    }


def analyze_all_metrics(df, alpha=0.05):
    """
    Run statistical tests on all relevant metrics in the dataset.

    Args:
        df (pandas.DataFrame): The processed dataset
        alpha (float): Significance level

    Returns:
        dict: Dictionary containing all test results
    """
    # Metrics to analyze (numeric columns except User_ID)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    metrics = [col for col in numeric_cols if col != 'User_ID']

    results = {
        't_test_results': [],
        'mann_whitney_results': []
    }

    for metric in metrics:
        # Run both tests for each metric
        t_test_result = run_t_test(df, metric, alpha)
        mw_test_result = run_mann_whitney_test(df, metric, alpha)

        results['t_test_results'].append(t_test_result)
        results['mann_whitney_results'].append(mw_test_result)

    return results


def save_results(results, output_path='reports/statistical_results.json'):
    """
    Save the statistical test results to a JSON file.

    Args:
        results (dict): Dictionary containing test results
        output_path (str): Path to save the JSON file
    """
    # Create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert any numpy values to Python native types
    def convert_np(obj):
        if isinstance(obj, dict):
            return {k: convert_np(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_np(item) for item in obj]
        elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                              np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj

    results_converted = convert_np(results)

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results_converted, f, indent=4)

    print(f"Statistical results saved to {output_path}")


def main():
    """Main function to run the statistical testing pipeline."""
    from .data_analysis import load_data

    print("Loading processed data...")
    df = load_data()

    print("\nRunning statistical tests...")
    results = analyze_all_metrics(df)

    # Print significant findings
    significant_t_tests = [r for r in results['t_test_results']
                           if 'significant' in r and r['significant']]

    significant_mw_tests = [r for r in results['mann_whitney_results']
                            if 'significant' in r and r['significant']]

    print(f"\nSignificant findings (t-tests): {len(significant_t_tests)}")
    for result in significant_t_tests:
        print(f"- {result['metric']}: p={result['p_value']:.4f}, " +
              f"change={result['percent_change']:.2f}%")

    print(f"\nSignificant findings (Mann-Whitney): {len(significant_mw_tests)}")
    for result in significant_mw_tests:
        print(f"- {result['metric']}: p={result['p_value']:.4f}, " +
              f"change={result['percent_change']:.2f}%")

    print("\nSaving results...")
    save_results(results)

    print("\nStatistical analysis complete!")

    return results


if __name__ == "__main__":
    main()