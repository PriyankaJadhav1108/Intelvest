from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum


class ItemType(str, Enum):
    press_release = "press_release"
    presentation = "presentation"
    webcast = "webcast"
    unknown = "unknown"


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


class ScrapeResponse(BaseModel):
    source_url: str
    ir_page_url: Optional[str] = None
    items: List[IRItem] = []
    message: str = "OK"
