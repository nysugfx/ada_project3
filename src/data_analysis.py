"""
Data Analysis Module for Shiny App A/B Testing

This module handles data loading, cleaning, and preparation for the A/B test analysis.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def load_data(file_path='data/shiny_user_data.csv'):
    """
    Load and preprocess the A/B test data.

    Args:
        file_path (str): Path to the CSV data file

    Returns:
        pandas.DataFrame: Preprocessed data frame
    """
    # Load the data
    df = pd.read_csv(file_path)

    # Process the Time_Spent column which contains JSON-like dictionaries
    def parse_time_spent(time_str):
        try:
            # Convert string representation of dict to actual dict
            time_dict = json.loads(time_str.replace("'", '"'))
            # Return total time across all sections
            return sum(time_dict.values())
        except (json.JSONDecodeError, AttributeError):
            return np.nan

    # Apply the parser to create a Total_Time_Spent column
    df['Total_Time_Spent'] = df['Time_Spent'].apply(parse_time_spent)

    # Extract time spent in individual sections
    sections = ['data_upload', 'data_cleaning', 'feature_engineering', 'exploratory_analysis']

    for section in sections:
        df[f'Time_{section}'] = df['Time_Spent'].apply(
            lambda x: json.loads(x.replace("'", '"')).get(section, np.nan)
            if isinstance(x, str) else np.nan
        )

    return df


def describe_dataset(df):
    """
    Generate descriptive statistics for the dataset.

    Args:
        df (pandas.DataFrame): The dataset

    Returns:
        dict: Dictionary containing dataset description
    """
    # Basic info
    description = {
        'total_samples': len(df),
        'group_counts': df['Group'].value_counts().to_dict(),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().to_dict()
    }

    # Descriptive statistics by group
    description['group_stats'] = {}

    for group in df['Group'].unique():
        group_df = df[df['Group'] == group]

        # Select numeric columns for statistics
        numeric_cols = group_df.select_dtypes(include=[np.number]).columns

        # Calculate statistics for each numeric column
        description['group_stats'][group] = {
            col: {
                'mean': group_df[col].mean(),
                'median': group_df[col].median(),
                'std': group_df[col].std(),
                'min': group_df[col].min(),
                'max': group_df[col].max()
            }
            for col in numeric_cols
        }

    return description


def save_processed_data(df, output_path='data/processed_data.csv'):
    """
    Save the processed dataframe to a CSV file.

    Args:
        df (pandas.DataFrame): The processed dataframe
        output_path (str): Path to save the CSV file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")


def main():
    """Main function to run the data analysis pipeline."""
    print("Loading and processing data...")
    df = load_data()

    print("\nDataset Description:")
    description = describe_dataset(df)
    print(f"Total samples: {description['total_samples']}")
    print(f"Group counts: {description['group_counts']}")

    print("\nSaving processed data...")
    save_processed_data(df)

    print("\nData analysis complete!")

    return df


if __name__ == "__main__":
    main()