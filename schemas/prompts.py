"""Prompt templates for Aralia OpenRAG."""

from langchain_core.prompts import PromptTemplate
from typing import Dict, Any


class PromptTemplates:
    """Collection of prompt templates for different agents."""
    
    # Dataset search and filtering
    DATASET_EXTRACT = PromptTemplate.from_template(
        """
        You are an expert data analyst tasked with filtering datasets based on relevance to a user's question.
        
        **Task**: For the following question, identify and retain only the most directly relevant datasets.
        Remove any datasets that are indirect, redundant, or tangentially related.
        
        **Question**: {question}
        
        **Available Datasets**: {datasets}
        
        **Instructions**:
        1. Analyze the core intent and key entities in the question
        2. Evaluate each dataset's relevance to answering the question
        3. Prioritize datasets that directly contain the required information
        4. Remove datasets that are only tangentially related
        5. Aim for quality over quantity - better to have fewer highly relevant datasets
        
        Return the dataset keys and names for the most relevant datasets only.
        """
    )
    
    # Chart plotting and analysis planning
    CHART_PLOTTING = PromptTemplate.from_template(
        """
        # Data Visualization Expert
        
        You are a senior data analyst expert, skilled in data exploration and correlation analysis, 
        and proficient in designing effective data visualizations.
        
        ## Objective
        Based on the user's question, analyze each provided dataset and propose **one specific chart** 
        for each relevant dataset that most effectively answers the question.
        
        ## Input Information
        - **Question**: {question}
        - **Datasets**: {datasets}
        - **Admin Levels**: {admin_level}
        
        ## Analysis Framework
        
        ### Phase 1: Question Analysis
        - Understand the user's intent and break down the question
        - Identify key metrics and dimensions needed
        - Distinguish between:
          - **Primary Axis Dimension**: Main dimension for chart axis (e.g., time series)
          - **Grouping Dimension**: Categorical fields for comparison (e.g., regions, categories)
        
        ### Phase 2: Dataset Selection
        - Retain only the best datasets that can answer the question
        - Remove datasets that don't contribute meaningful insights
        
        ### Phase 3: Visualization Design
        For each selected dataset:
        - **Metrics**: Quantitative fields for measurement (y-axis)
        - **Primary Axis**: Main dimension for x-axis
        - **Grouping**: Categorical breakdown for comparison
        
        ### Phase 4: Technical Specification
        - **Date/DateTime fields**: Use formats like "year", "month", "quarter", etc.
        - **Spatial fields**: Use appropriate admin_level_x format
        - **Numeric fields**: Specify calculation method (sum, avg, count, min, max)
        - **Nominal fields**: Use count or distinct_count
        
        ## Output Format
        ```json
        {{
            "charts": [
                {{
                    "id": "dataset_id",
                    "name": "dataset_name",
                    "x": [
                        {{
                            "columnID": "column_id",
                            "name": "display_name",
                            "type": "data_type",
                            "format": "format_specification"
                        }}
                    ],
                    "y": [
                        {{
                            "columnID": "column_id",
                            "name": "display_name",
                            "type": "data_type",
                            "calculation": "calculation_method"
                        }}
                    ],
                    "filter": [
                        {{
                            "columnID": "column_id",
                            "name": "display_name",
                            "type": "data_type",
                            "format": "format_specification",
                            "operator": "operator_type",
                            "value": ["filter_values"]
                        }}
                    ]
                }}
            ]
        }}
        ```
        """
    )
    
    # Query generation and refinement
    QUERY_GENERATION = PromptTemplate.from_template(
        """
        You are a senior data analyst specializing in statistical data analysis and query optimization.
        
        ## Task
        Generate optimized query configurations based on the user's question and available dataset structures.
        
        ## Input
        - **User Question**: {question}
        - **Dataset Configurations**: {response}
        
        ## Instructions
        
        ### Core Rules
        1. **Preserve Structure**: Maintain exact same top-level keys and array structures
        2. **Modify Only**: `operator` and `value` fields in filter objects
        3. **No Additions**: Do not add new filter objects or modify other fields
        4. **No Removals**: Do not remove existing filter objects
        
        ### Operator Selection
        - **Date/DateTime/Nominal/Spatial**: Use `"in"` operator
        - **Integer/Float**: Use `"range"`, `"lt"`, `"gt"`, `"lte"`, or `"gte"`
        
        ### Value Specification
        - Analyze the user question carefully to determine appropriate filter values
        - For geographic locations, consider administrative boundaries and actual locations
        - For nominal categories, use exact matches from available options
        - For date ranges, specify appropriate time periods
        
        ### Special Considerations
        - Some institutions may be named after one location but physically located elsewhere
        - Example: "Taipei Motor Vehicles Office" is actually in New Taipei City
        - Always verify geographic relationships when setting spatial filters
        
        Return the modified configuration with updated `operator` and `value` fields only.
        """
    )
    
    # Interpretation and response generation
    INTERPRETATION = PromptTemplate.from_template(
        """
        You are an expert data analyst providing insights based on retrieved data.
        
        ## Task
        Analyze the provided data and answer the user's question with clear, actionable insights.
        
        ## Input
        - **Question**: {question}
        - **Data Results**: {search_results}
        
        ## Requirements
        
        ### Language Matching
        **CRITICAL**: Your response language MUST exactly match the language used in the question.
        
        ### Content Requirements
        1. **Detailed Analysis**: Provide thorough analysis of the charts and data patterns
        2. **Direct Answer**: Give a clear, direct answer to the specific question asked
        3. **Concise Conclusion**: Summarize key findings in under 300 words
        4. **Evidence-Based**: Base all conclusions on the actual data provided in "json_data"
        
        ### Structure
        1. **Data Overview**: Brief summary of the datasets analyzed
        2. **Key Findings**: Main insights from the data
        3. **Direct Answer**: Specific answer to the user's question
        4. **Conclusion**: Summary of implications and recommendations
        
        Focus on actionable insights and ensure all claims are supported by the provided data.
        """
    )
    
    @classmethod
    def get_admin_levels(cls) -> Dict[str, Dict[str, str]]:
        """Get administrative level mappings for different regions."""
        return {
            "Taiwan": {
                "admin_level_2": "國家",
                "admin_level_4": "直轄市/縣市/六都", 
                "admin_level_7": "直轄市的區",
                "admin_level_8": "縣轄市/鄉鎮",
                "admin_level_9": "村/里",
                "admin_level_10": "鄰"
            },
            "Japan": {
                "admin_level_2": "Country",
                "admin_level_4": "Prefecture (To/Dō/Fu/Ken)",
                "admin_level_5": "Subprefecture (Hokkaido only)",
                "admin_level_6": "County (Gun - limited function) / City subprefecture (Tokyo)",
                "admin_level_7": "City / Town / Village",
                "admin_level_8": "Ward (Ku - in designated cities)",
                "admin_level_9": "District / Town block (Chō/Machi/Chōme)",
                "admin_level_10": "Area (Ōaza/Aza) / Block number (Banchi)"
            },
            "Malaysia": {
                "admin_level_2": "Country",
                "admin_level_4": "State (Negeri) / Federal Territory (Wilayah Persekutuan)",
                "admin_level_5": "Division (Bahagian - Sabah & Sarawak only)",
                "admin_level_6": "District (Daerah)",
                "admin_level_7": "Subdistrict (Daerah Kecil / Mukim)",
                "admin_level_8": "Mukim / Town (Bandar) / Village (Kampung)"
            },
            "Singapore": {
                "admin_level_2": "Country",
                "admin_level_6": "District (CDC - Community Development Council)"
            }
        }
    
    @classmethod
    def get_format_options(cls) -> Dict[str, list]:
        """Get available format options for different data types."""
        return {
            "date": [
                "year", "quarter", "month", "week", "date", "day", "weekday",
                "year_month", "year_quarter", "year_week", "month_day",
                "day_hour", "hour", "minute", "second", "hour_minute", "time"
            ],
            "space": [
                "admin_level_2", "admin_level_3", "admin_level_4",
                "admin_level_5", "admin_level_6", "admin_level_7", 
                "admin_level_8", "admin_level_9", "admin_level_10"
            ],
            "calculation": [
                "count", "sum", "avg", "min", "max", "distinct_count"
            ],
            "operator": [
                "eq", "lt", "gt", "lte", "gte", "in", "range"
            ]
        }


# Legacy aliases for backward compatibility
simple_datasets_extract_template = PromptTemplates.DATASET_EXTRACT
chart_ploting_template = PromptTemplates.CHART_PLOTTING
query_generate_template = PromptTemplates.QUERY_GENERATION
admin_level = PromptTemplates.get_admin_levels()
format = PromptTemplates.get_format_options()
