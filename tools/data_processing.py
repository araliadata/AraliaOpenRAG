"""Data processing utilities for Aralia OpenRAG."""

import pandas as pd
from typing import List, Dict, Any, Optional
from utils.logging import get_logger


class DataProcessor:
    """Utility class for processing and analyzing data from Aralia."""
    
    def __init__(self):
        """Initialize data processor."""
        self.logger = get_logger("data_processor")
    
    def parse_exploration_results(
        self,
        df: pd.DataFrame,
        x_labels: Optional[List[str]] = None,
        value_labels: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Parse exploration results DataFrame to flatten arrays.
        
        Args:
            df: Input DataFrame with 'x' and 'values' columns
            x_labels: Custom column names for flattened 'x' values
            value_labels: Custom column names for flattened 'values'
            
        Returns:
            Parsed DataFrame with flattened columns
        """
        self.logger.info(f"Parsing exploration results with {len(df)} rows")
        
        # Initialize lists to store parsed column data
        x_columns = []
        value_columns = []
        
        # Process each row of the DataFrame
        for _, row in df.iterrows():
            # Extract and flatten 'x' values
            combined_x = [item[0] for item in row['x']]
            x_columns.append(combined_x)
            
            # Add 'values' array directly
            value_columns.append(row['values'])
        
        # Create DataFrames for flattened 'x' and 'values'
        x_df = pd.DataFrame(
            x_columns,
            columns=x_labels if x_labels and len(x_labels) == len(x_columns[0]) else [
                f"x{i+1}" for i in range(len(x_columns[0]))]
        )
        
        values_df = pd.DataFrame(value_columns)
        values_df.columns = value_labels if value_labels and len(
            value_labels) == values_df.shape[1] else [f"value{i+1}" for i in range(values_df.shape[1])]
        
        # Concatenate the original and parsed DataFrames
        result_df = pd.concat([x_df, values_df], axis=1)
        
        self.logger.info(f"Parsed data into {len(result_df.columns)} columns")
        return result_df
    
    
    def prepare_chart_data(
        self,
        exploration_results: List[Dict[str, Any]],
        chart_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare chart data from exploration results.
        
        Args:
            exploration_results: Raw exploration results
            chart_config: Chart configuration with x, y axis info
            
        Returns:
            Processed chart data
        """
        if not exploration_results:
            self.logger.warning("No exploration results to process")
            return {"data": None, "error": "No data available"}
        
        try:
            # Extract column labels
            x_cols = [x_axis.get('displayName', f"x{i}") for i, x_axis in enumerate(chart_config.get('x', []))]
            y_cols = [y_axis.get('displayName', f"y{i}") for i, y_axis in enumerate(chart_config.get('y', []))]
            
            # Convert to DataFrame and parse
            df = pd.DataFrame(exploration_results)
            parsed_df = self.parse_exploration_results(df, x_cols, y_cols)
            
            # Prepare JSON data (limited to first 400 rows for performance)
            json_data = parsed_df.head(400).to_json(force_ascii=False, orient='records')
            
            return {
                "data": parsed_df,
                "json_data": json_data,
                "row_count": len(parsed_df),
                "column_count": len(parsed_df.columns)
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing chart data: {str(e)}")
            return {"data": None, "error": str(e)}
