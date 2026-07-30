from fastapi import APIRouter, HTTPException, Depends, Request
from backend.governance.rbac import Permission, requires_permission
from typing import Dict, Any
from ..agents.supervisor.supervisor_agent import SupervisorFactory, WorkflowRequest
from ..llm_manager import LLMManager
import logging

from backend.shared.utils.logger import get_logger
logger = get_logger(__name__)
router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])

def get_llm_manager(request: Request):
    return request.app.state.llm_manager

@router.post("/workflow/execute", dependencies=[Depends(requires_permission(Permission.ANALYZE))])
async def execute_workflow(
    workflow_data: Dict[str, Any],
    llm_mgr: LLMManager = Depends(get_llm_manager)
):
    """Execute supervised workflow"""
    try:
        # Create supervisor
        supervisor = SupervisorFactory.create_supervisor(llm_mgr)
        
        # Create workflow request
        request = WorkflowRequest(
            workflow_id=workflow_data.get("workflow_id", "default"),
            workflow_type=workflow_data.get("workflow_type", "contract_analysis"),
            input_data=workflow_data.get("input_data", {})
        )
        
        # Execute workflow
        result = supervisor.coordinate_workflow(request)
        
        return {
            "success": True,
            "workflow_id": result.workflow_id,
            "status": result.status,
            "results": result.results,
            "summary": result.summary
        }
        
    except Exception as e:
        logger.error(f"Supervisor workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    llm_mgr: LLMManager = Depends(get_llm_manager)
):
    """Get workflow status"""
    try:
        supervisor = SupervisorFactory.create_supervisor(llm_mgr)
        status = supervisor.get_workflow_status(workflow_id)
        return {"success": True, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))