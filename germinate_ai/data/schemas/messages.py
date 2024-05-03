from typing import Optional

from pydantic import BaseModel

class Message(BaseModel):
    source: str
    destination: Optional[str] = "*"
    subject: Optional[str] = ""

    content: Optional[str] = ""
    payload: Optional[dict] = {}
