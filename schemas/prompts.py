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
            # [Role and Core Objective]
            You are a senior data analyst expert, skilled in data exploration and correlation analysis, and proficient in designing effective data visualizations.
            Your objective is: Based on the user's question, analyze each provided dataset, and for **each dataset deemed relevant**, propose **only one specific chart proposal** that most effectively answers the question.

            # [Input Information]
            - **Question:** {question}
            - **Datasets:** {datasets} (This should include dataset descriptions, column names, column types, etc. - metadata)
            - **admin_level:** {admin_level}

            # [Execution Steps]
            Please strictly write down your thought process for each step.

            **Phase 1: Problem Analysis**
                * Deeply understand the intent of the user's `Question`, break it down, and identify the key entities and metrics.
                * **Crucially, distinguish between two types of dimensions:**
                    * **1. 主軸維度 (Primary Axis Dimension):** The main dimension that forms the chart's primary axis (e.g., a time series, a continuous numerical range). A chart typically has only one.
                    * **2. 分類比較維度 (Grouping/Comparison Dimension):** Categorical fields used to group or break down the metrics for comparison (e.g., store names, product types, station names). There can be one or more.
                * Thought Record: Document your understanding and analysis of the question, explicitly listing the identified metrics, primary axis dimensions, and grouping/comparison dimensions.

            **Phase 2: Datasets Removal**
                * Retain only the best datasets to the question, remove the worse ones.*

            **Phase 3: Column Selection**
                * For best datasets, identify the **minimum necessary set of columns** required to answer the `Question`. 

            **Phase 4: Charting Specification(Per Dataset)**
                a. Identify required data components based on Phase 1 analysis:
                    - Metrics (指標): Quantitative fields for measurement (usually for the y-axis).
                    - Primary Axis Dimension (主軸維度): The dimension for the x-axis.
                    - Grouping/Comparison Dimension (分類比較維度): The dimension used to break down the data into different series/colors/groups.
                b. If a field's type is **date/datetime/space/nominal/ordinal/point/line/polygon** specify it for the x-axis (if it's a Primary Axis Dimension or a Grouping/Comparison Dimension).
                c. If a field's type is **integer/float** specify it for the y-axis (if it's a Metric).

            **Phase 5: Filtering Specification(Per Dataset)**
                a. Define filter parameters (including any dual-purpose fields used in both x/y and filtering):
                    - Temporal Scope: Date/time ranges (if necessary)
                    - Spatial Boundaries: Geographic constraints (if necessary)
                    - Category Filters: Specific categorical values
                b. Specify required filter fields (including any dual-purpose fields used in both x/y and filtering)

            **Phase 6: Format and Calculation Specification(Per Dataset)**
                Please specify the format for each time filter if necessary.
                a.If field's type is **date, datetime**, 
                - "format" should be one of:
                    ["year", "quarter", "month", "week", "date", "day", "weekday", "year_month", "year_quarter", "year_week", "month_day", "day_hour", "hour", "minute", "second", "hour_minute", "time"].
                - "operator" should be "in"

                b.If field's type is **space, point, line, polygon**.
                - Please carefully consider user's question to fill the most general admin_level_x(lowest number) to "format".

                c.If field's type is **nominal, integer, float**
                - "format" is ""

                d.If field's type is **integer, float**
                - "calculation" should be one of:
                    ["count", "sum", "avg", "min", "max", "distinct_count"].
        
                e.If field's type is **nominal**
                - "calculation" should be one of:
                    ["count", "distinct_count"]

            **Phase 7: Final Output Generation**
                a. The `x` array should include both the **Primary Axis Dimension** and any **Grouping/Comparison Dimensions** identified in Phase 4.
                b. The `y` array should contain the **Metrics**.
                c. Apply Phase 5 to the `filter` array. Remember that a Grouping/Comparison Dimension (like "站點") often needs to be in both the `x` array (for grouping) and the `filter` array (to select specific categories).
                d. Apply to the `json_format` specified below.
                
            json_format:
            {{
                "charts": [
                    {{
                        "id": "dataset_id",
                        "name": "dataset_name
                        "x":[
                            {{
                                "columnID": "column_id",
                                "name": "filed_displayName",
                                "type":"",
                                "format": "",
                            }}
                        ],
                        "y":[
                            {{
                                "columnID": "column_id",
                                "name": "filed_displayName",
                                "type":"",
                                "calculation": "aggregate_function"
                            }}
                        ],
                        "filter":[
                            {{
                                "columnID": "column_id",
                                "name": "filed_name",
                                "calculation": "aggregate_function",
                                "type":"",
                                "format": "",
                                "operator":"",
                                "value": ["filter_value"]
                            }}
                        ]
                    }},
                    ...
                ]
            }}

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
