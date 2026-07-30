from fastapi import APIRouter, Depends
from backend.governance.rbac import Permission, requires_permission
from backend.infrastructure.contract_repository import Neo4jContractRepository
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/contracts", dependencies=[Depends(requires_permission(Permission.VIEW_AUDIT))])
async def list_all_contracts():
    """Debug endpoint to see all contracts in database"""
    try:
        repo = Neo4jContractRepository()
        
        # Get all contracts with their types
        query = """
        MATCH (c:Contract)
        RETURN c.file_id as contract_id, 
               c.contract_type as contract_type,
               c.summary as summary,
               c.source as source
        ORDER BY c.upload_date DESC
        """
        
        result = repo.graph.query(query)
        
        contracts = []
        for row in result:
            contracts.append({
                "contract_id": row["contract_id"],
                "contract_type": row["contract_type"],
                "summary": row["summary"][:100] + "..." if row["summary"] and len(row["summary"]) > 100 else row["summary"],
                "source": row["source"]
            })
        
        return {
            "total_contracts": len(contracts),
            "contracts": contracts
        }
        
    except Exception as e:
        logger.error(f"Debug contracts failed: {e}")
        return {"error": str(e)}

@router.get("/contract-types", dependencies=[Depends(requires_permission(Permission.VIEW_REPORTS))])
async def get_contract_type_counts():
    """Debug endpoint to see contract type distribution"""
    try:
        repo = Neo4jContractRepository()
        
        query = """
        MATCH (c:Contract)
        RETURN c.contract_type as contract_type, count(*) as count
        ORDER BY count DESC
        """
        
        result = repo.graph.query(query)
        
        return {
            "contract_types": [{"type": row["contract_type"], "count": row["count"]} for row in result]
        }
        
    except Exception as e:
        logger.error(f"Debug contract types failed: {e}")
        return {"error": str(e)}