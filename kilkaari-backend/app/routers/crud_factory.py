"""
crud_factory.py — builds a standard "public read, admin write" CRUD router
for simple content models (programs, events, campaigns, gallery items,
testimonials, centers, student stories) so each one doesn't need hand-written
boilerplate that would otherwise just repeat this same pattern seven times.
"""

from typing import Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import User


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    model,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    out_schema: Type[BaseModel],
    published_only_field: str | None = None,
    order_by: str | None = None,
    order_desc: bool = False,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=list[out_schema])
    def list_items(db: Session = Depends(get_db)):
        query = db.query(model)
        if published_only_field:
            query = query.filter(getattr(model, published_only_field) == True)  # noqa: E712
        if order_by:
            column = getattr(model, order_by)
            query = query.order_by(column.desc() if order_desc else column.asc())
        return query.all()

    @router.get("/{item_id}", response_model=out_schema)
    def get_item(item_id: str, db: Session = Depends(get_db)):
        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{tag[:-1].capitalize()} not found")
        return item

    @router.post("", response_model=out_schema, status_code=201)
    def create_item(
        payload: create_schema,
        db: Session = Depends(get_db),
        _admin: User = Depends(require_admin),
    ):
        item = model(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.put("/{item_id}", response_model=out_schema)
    def update_item(
        item_id: str,
        payload: update_schema,
        db: Session = Depends(get_db),
        _admin: User = Depends(require_admin),
    ):
        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{tag[:-1].capitalize()} not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=204)
    def delete_item(
        item_id: str,
        db: Session = Depends(get_db),
        _admin: User = Depends(require_admin),
    ):
        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{tag[:-1].capitalize()} not found")
        db.delete(item)
        db.commit()
        return None

    return router
