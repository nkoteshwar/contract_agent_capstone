import os
from fastapi import APIRouter
from typing import List

def is_development() -> bool:
    """Check if running in development environment"""
    return os.getenv("ENVIRONMENT", "development") != "production"

def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development") == "production"

def conditionally_include_router(app, router: APIRouter, condition: bool = True):
    """Conditionally include router based on environment or condition"""
    if condition:
        app.include_router(router)

def get_debug_routes() -> List[str]:
    """Get list of debug route paths"""
    return ["/debug/contracts", "/debug/contract-types", "/dev/debug/contracts", "/dev/debug/contract-types"]

def get_production_routes() -> List[str]:
    """Get list of production route paths"""
    return ["/api/contracts", "/api/intelligence", "/api/search"]