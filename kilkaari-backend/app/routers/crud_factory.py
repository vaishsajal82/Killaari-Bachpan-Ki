"""
crud_factory.py — builds a standard "public read, admin write" CRUD router
for simple content models (programs, events, campaigns, gallery items,
testimonials, centers, student stories) so each one doesn't need hand-written
boilerplate that would otherwise just repeat this same pattern seven times.
"""

import logging
from typing import Callable, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import User

logger = logging.getLogger("kilkaari.crud")


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
    # Optional hooks — every existing router (programs, events, campaigns,
    # testimonials, centers, student stories) simply doesn't pass these
    # and behaves exactly as before. Only gallery.py currently uses them,
    # to clean up the old Cloudinary asset after an image is replaced or
    # the item is deleted. Both run AFTER the database change has already
    # committed successfully — cleanup is best-effort and must never be
    # able to make an otherwise-successful update/delete fail or roll
    # back, so exceptions from the hook itself are caught and logged here
    # rather than propagated to the client.
    after_update: Optional[Callable[[object, dict], None]] = None,
    after_delete: Optional[Callable[[dict], None]] = None,
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

        changed_fields = payload.model_dump(exclude_unset=True)
        # Snapshot only the fields actually being changed, taken BEFORE
        # they're overwritten — this is what after_update needs to compare
        # old vs. new (e.g. "did the image actually change?").
        old_values = {field: getattr(item, field) for field in changed_fields}

        for field, value in changed_fields.items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)

        if after_update:
            try:
                after_update(item, old_values)
            except Exception:
                logger.exception("after_update hook failed for %s %s (DB update already succeeded)", tag, item_id)

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

        # Snapshot before delete — after commit, the ORM object is expired
        # and its attributes aren't safely readable anymore.
        snapshot = {c.name: getattr(item, c.name) for c in model.__table__.columns}

        db.delete(item)
        db.commit()

        if after_delete:
            try:
                after_delete(snapshot)
            except Exception:
                logger.exception("after_delete hook failed for %s %s (DB delete already succeeded)", tag, item_id)

        return None

    return router
