"""Pydantic models for Aralia OpenRAG."""

from pydantic import BaseModel, Field
from typing import List, Optional
from typing_extensions import Literal, Annotated


class DatasetExtractOutput(BaseModel):
    """Output schema for dataset extraction."""
    dataset_key: List[str] = Field(..., description="List of dataset keys to extract")
    dataset_name: List[str] = Field(..., description="List of dataset names")


class DatasetSpaceInfo(BaseModel):
    """Information about dataset geographic and language context."""
    id: str = Field(..., description="Dataset identifier")
    region: Annotated[Literal["Taiwan", "Japan", "Malaysia", "Singapore", "America"], 
                     "Geographic region where dataset originates"]
    language: Annotated[Literal["zh-tw", "zh-cn", "en", "ja", "ms"], 
                       "Primary language of the dataset"]


class DatasetSpaceInfoList(BaseModel):
    """List of dataset space information."""
    datasets: List[DatasetSpaceInfo] = Field(..., description="List of dataset space info")


class XAxis(BaseModel):
    """X-axis configuration for data visualization."""
    columnID: str = Field(..., description="Column identifier")
    displayName: str = Field(..., description="Human-readable column name")
    type: str = Field(..., description="Data type of the column")
    format: str = Field("", description="Format specification for the column")


class YAxis(BaseModel):
    """Y-axis configuration for data visualization."""
    columnID: str = Field(..., description="Column identifier")
    displayName: str = Field(..., description="Human-readable column name")
    calculation: str = Field(..., description="Calculation method (sum, avg, count, etc.)")


class FilterConfig(BaseModel):
    """Filter configuration for data queries."""
    columnID: str = Field(..., description="Column identifier")
    displayName: str = Field(..., description="Human-readable column name")
    type: str = Field(..., description="Data type of the column")
    format: str = Field("", description="Format specification for the column")
    operator: str = Field(..., description="Filter operator (eq, in, range, etc.)")
    value: List[str] = Field(..., description="Filter values")


class QueryConfig(BaseModel):
    """Complete query configuration for data exploration."""
    sourceURL: str = Field(..., description="Data source URL")
    id: str = Field(..., description="Dataset identifier")
    name: str = Field(..., description="Dataset name")
    x: List[XAxis] = Field(..., description="X-axis configurations")
    y: List[YAxis] = Field(..., description="Y-axis configurations") 
    filter: List[FilterConfig] = Field(default_factory=list, description="Filter configurations")


class QueryList(BaseModel):
    """List of query configurations."""
    querys: List[QueryConfig] = Field(..., description="List of query configurations")


# Legacy aliases for backward compatibility
datasets_extract_output = DatasetExtractOutput
dataset_space_info = DatasetSpaceInfo
dataset_space_info_list = DatasetSpaceInfoList
x = XAxis
y = YAxis
filter = FilterConfig
query = QueryConfig
query_list = QueryList
