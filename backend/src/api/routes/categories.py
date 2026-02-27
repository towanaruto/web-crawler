from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas import CategoryOut
from src.db.engine import get_db
from src.db.repository import list_categories

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return list_categories(db)
