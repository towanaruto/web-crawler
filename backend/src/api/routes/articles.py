from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas import ArticleDetail, ArticleListItem, PaginatedArticles
from src.db.engine import get_db
from src.db.repository import delete_article, get_article_by_slug, list_articles

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=PaginatedArticles)
def get_articles(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    articles, total = list_articles(
        db, category_slug=category, search=search, offset=offset, limit=limit,
    )
    return PaginatedArticles(items=articles, total=total, offset=offset, limit=limit)


@router.get("/{slug}", response_model=ArticleDetail)
def get_article(slug: str, db: Session = Depends(get_db)):
    article = get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.delete("/{article_id}", response_model=ArticleListItem)
def remove_article(article_id: UUID, db: Session = Depends(get_db)):
    article = delete_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.commit()
    return article
