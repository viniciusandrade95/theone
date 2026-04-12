from fastapi import APIRouter

from app.http.routes.assistant_prebook import router as assistant_prebook_router

router = APIRouter()

# Assistant operational surface (week 1 foundation):
# - POST /crm/assistant/prebook
router.include_router(assistant_prebook_router)

