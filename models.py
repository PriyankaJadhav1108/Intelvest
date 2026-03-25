from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from enum import Enum


class ItemType(str, Enum):
    press_release = "press_release"
    presentation = "presentation"
    webcast = "webcast"
    transcript = "transcript"
    unknown = "unknown"


class QuarterlyDocs(BaseModel):
    slides: Optional[str] = None
    slides_title: Optional[str] = None
    press_release: Optional[str] = None
    press_release_title: Optional[str] = None
    webcast_link: Optional[str] = None
    webcast_title: Optional[str] = None
    transcript: Optional[str] = None
    transcript_title: Optional[str] = None


class YearlyData(BaseModel):
    year: int
    quarters: dict[str, QuarterlyDocs] = {}


class ScrapeRequest(BaseModel):
    source_url: str

    model_config = {
        "json_schema_extra": {
            "example": {"source_url": "https://www.jnj.com"}
        }
    }


class IRItem(BaseModel):
    title: str
    link: str
    item_type: ItemType
    pdf_path: Optional[str] = None   # relative path served at /downloads/{filename}
    pdf_url: Optional[str] = None    # absolute URL to download the PDF
    parsed_year: Optional[int] = None
    parsed_quarter: Optional[int] = None


class ScrapeResponse(BaseModel):
    source_url: str
    ir_page_url: Optional[str] = None
    items: List[IRItem] = []
    years: List[YearlyData] = []
    message: str = "OK"
    playwright_used: bool = False
    playwright_error: Optional[str] = None
