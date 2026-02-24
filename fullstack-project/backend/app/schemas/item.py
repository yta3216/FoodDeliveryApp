from typing import List
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    title: str
    category: str
    tags: List[str] = []

class ItemCreate(BaseModel):
    title: str
    category: str
    tags: List[str] = []

class ItemUpdate(BaseModel):
    title : str
    category:str
    tags: List[str] = []
