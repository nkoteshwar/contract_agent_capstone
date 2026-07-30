from fastapi import APIRouter
from backend.api.contract_intelligence import router as intelligence_router
from backend.api.enhanced_contract_search import router as search_router
from backend.api.enhanced_document_upload import router as upload_router

def create_production_router() -> APIRouter:
    """Create production-only routes"""
    router = APIRouter(tags=["production"])
    
    # Include production routes without additional prefix
    router.include_router(intelligence_router)
    router.include_router(search_router)
    router.include_router(upload_router)
    
    return router