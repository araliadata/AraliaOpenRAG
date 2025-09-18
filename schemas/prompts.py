"""Prompt templates for Aralia OpenRAG."""

from langchain_core.prompts import PromptTemplate
from typing import Dict, Any


class PromptTemplates:
    """Collection of prompt templates for different nodes."""
    
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
        # ROLE AND OBJECTIVE
        You are a senior data analyst expert, skilled in data exploration, correlation analysis, and effective data visualization design.
        
        **Objective**: Based on the user's question, analyze each provided dataset and propose **only one specific chart proposal per relevant dataset** that most effectively answers the question.

        # INPUT INFORMATION
        - **Question:** {question}
        - **Datasets:** {datasets} (includes dataset descriptions, column names, column types, and metadata)
        - **Administrative Levels:** {admin_level}

        # ANALYSIS FRAMEWORK
        Execute the following phases systematically, documenting your thought process for each step:

        ## Phase 1: Problem Analysis
        **Deep Question Understanding:**
        - Analyze the user's question intent and break it down into components
        - Identify key entities, metrics, and analytical requirements
        
        **Dimension Classification (Critical):**
        Distinguish between two types of dimensions:
        
        1. **主軸維度 (Primary Axis Dimension):**
           - Forms the chart's main axis (typically x-axis)
           - Examples: time series, continuous numerical ranges
           - Usually only one per chart
        
        2. **分類比較維度 (Grouping/Comparison Dimension):**
           - Categorical fields for grouping/comparing metrics
           - Examples: store names, product types, geographic regions
           - Can have multiple dimensions
        
        **Documentation:** Record your analysis explicitly listing:
        - Identified metrics
        - Primary axis dimensions  
        - Grouping/comparison dimensions

        ## Phase 2: Dataset Curation
        - Retain only the most relevant datasets for answering the question
        - Remove datasets that are indirect, redundant, or tangentially related
        - Prioritize quality over quantity

        ## Phase 3: Column Selection
        - For each selected dataset, identify the **minimum necessary columns** to answer the question
        - Focus on essential fields that directly contribute to the analysis

        ## Phase 4: Chart Specification (Per Dataset)
        **Component Identification:**
        Based on Phase 1 analysis, identify:
        - **Metrics (指標):** Quantitative fields for measurement (y-axis candidates)
        - **Primary Axis Dimension (主軸維度):** Main dimension for x-axis
        - **Grouping/Comparison Dimension (分類比較維度):** Dimensions for data breakdown
        
        **Axis Assignment Rules:**
        - **X-axis:** Fields of type `date/datetime/space/nominal/ordinal/point/line/polygon` 
          (when serving as Primary Axis or Grouping/Comparison Dimension)
        - **Y-axis:** Fields of type `integer/float` (when serving as Metrics)

        ## Phase 5: Filter Specification (Per Dataset)
        **Filter Categories:**
        - **Temporal Scope:** Date/time ranges (when applicable)
        - **Spatial Boundaries:** Geographic constraints (when applicable)  
        - **Category Filters:** Specific categorical values (when applicable)
        
        **Dual-Purpose Fields:** Include fields that serve both as chart dimensions and filter criteria

        ## Phase 6: Format and Calculation Rules (Per Dataset)
        
        **Date/DateTime Fields:**
        - `format` options: `["year", "quarter", "month", "week", "date", "day", "weekday", "year_month", "year_quarter", "year_week", "month_day", "day_hour", "hour", "minute", "second", "hour_minute", "time"]`
        - `operator`: `"in"`
        
        **Spatial Fields (space/point/line/polygon):**
        - `format`: Use most general `admin_level_x` (lowest number) based on user question context
        
        **Nominal/Integer/Float Fields:**
        - `format`: `""` (empty string)
        
        **Calculation Methods:**
        - **Integer/Float:** `["count", "sum", "avg", "min", "max", "distinct_count"]`
        - **Nominal:** `["count", "distinct_count"]`

        ## Phase 7: Output Generation
        **Array Construction Rules:**
        - **`x` array:** Include Primary Axis Dimension + any Grouping/Comparison Dimensions
        - **`y` array:** Include identified Metrics with appropriate calculations
        - **`filter` array:** Apply Phase 5 specifications
        
        **Important:** Grouping/Comparison Dimensions often appear in both `x` array (for grouping) and `filter` array (for category selection)

        # OUTPUT FORMAT
        Return results in the following JSON structure:
        
        ```json
        {{
            "charts": [
                {{
                    "id": "dataset_id",
                    "name": "dataset_name",
                    "x": [
                        {{
                            "columnID": "column_id",
                            "name": "field_displayName",
                            "type": "field_type",
                            "format": "format_specification"
                        }}
                    ],
                    "y": [
                        {{
                            "columnID": "column_id", 
                            "name": "field_displayName",
                            "type": "field_type",
                            "calculation": "aggregate_function"
                        }}
                    ],
                    "filter": [
                        {{
                            "columnID": "column_id",
                            "name": "field_name", 
                            "calculation": "aggregate_function",
                            "type": "field_type",
                            "format": "format_specification",
                            "operator": "filter_operator",
                            "value": ["filter_value"]
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


