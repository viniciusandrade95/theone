from fastapi import APIRouter, Response

from core.observability.metrics import render_prometheus

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=render_prometheus(), media_type="text/plain; version=0.0.4; charset=utf-8")

