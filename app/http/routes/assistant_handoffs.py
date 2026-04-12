from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import NotFoundError
from modules.assistant.repo.handoff_repo import AssistantHandoffRepo


router = APIRouter()


class AssistantHandoffOut(BaseModel):
    id: str
    status: str
    reason: str | None = None
    summary: str | None = None
    conversation_id: str
    conversation_epoch: int
    session_id: str | None = None
    customer_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AssistantHandoffListOut(BaseModel):
    items: list[AssistantHandoffOut]


@router.get("/assistant/handoffs", response_model=AssistantHandoffListOut)
def list_assistant_handoffs(
    status: str = Query(default="open", max_length=32),
    identity=Depends(require_user),
    _tenant=Depends(require_tenant_header),
):
    tenant_id = identity["tenant_id"]
    if status != "open":
        # MVP: only open visibility is required.
        status = "open"
    with db_session() as session:
        repo = AssistantHandoffRepo(session)
        rows = repo.list_open(tenant_id=tenant_id, limit=50)
        return AssistantHandoffListOut(
            items=[
                AssistantHandoffOut(
                    id=str(r.id),
                    status=str(r.status),
                    reason=r.reason,
                    summary=r.summary,
                    conversation_id=str(r.conversation_id),
                    conversation_epoch=int(r.conversation_epoch or 0),
                    session_id=r.session_id,
                    customer_id=str(r.customer_id) if r.customer_id else None,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
                for r in rows
            ]
        )


@router.get("/assistant/handoffs/{handoff_id}", response_model=AssistantHandoffOut)
def get_assistant_handoff(
    handoff_id: str,
    identity=Depends(require_user),
    _tenant=Depends(require_tenant_header),
):
    tenant_id = identity["tenant_id"]
    with db_session() as session:
        repo = AssistantHandoffRepo(session)
        row = repo.get_by_id(tenant_id=tenant_id, handoff_id=handoff_id)
        if row is None:
            raise NotFoundError("assistant_handoff_not_found")
        return AssistantHandoffOut(
            id=str(row.id),
            status=str(row.status),
            reason=row.reason,
            summary=row.summary,
            conversation_id=str(row.conversation_id),
            conversation_epoch=int(row.conversation_epoch or 0),
            session_id=row.session_id,
            customer_id=str(row.customer_id) if row.customer_id else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

