from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credits.credit_request_service import CreditRequestService
from auth import get_current_user

router = APIRouter(prefix="/credits", tags=["Credit Requests"])

class CreditRequestModel(BaseModel):
    amount: int
    reason: str

class ApproveRequestModel(BaseModel):
    request_id: int
    approved_amount: int
    admin_notes: Optional[str] = ""

class RejectRequestModel(BaseModel):
    request_id: int
    admin_notes: Optional[str] = ""

@router.post("/request")
async def submit_credit_request(request: CreditRequestModel, current_user = Depends(get_current_user)):
    """Submit a credit request"""
    try:
        service = CreditRequestService()
        
        # Handle both dict and object user formats
        userid = current_user.userid if hasattr(current_user, 'userid') else current_user.get('userid')
        
        result = service.create_request(
            userid=userid,
            amount=request.amount,
            reason=request.reason
        )
        return result
    except Exception as e:
        print(f"Credit request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/my")
async def get_my_requests(current_user = Depends(get_current_user)):
    """Get current user's credit requests"""
    try:
        service = CreditRequestService()
        userid = current_user.userid if hasattr(current_user, 'userid') else current_user.get('userid')
        requests = service.get_user_requests(userid)
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/pending")
async def get_pending_requests(current_user = Depends(get_current_user)):
    """Get pending credit requests (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = CreditRequestService()
        requests = service.get_pending_requests()
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/all")
async def get_all_requests(current_user = Depends(get_current_user)):
    """Get all credit requests (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = CreditRequestService()
        requests = service.get_all_requests()
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/approve")
async def approve_request(request: ApproveRequestModel, current_user = Depends(get_current_user)):
    """Approve credit request (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = CreditRequestService()
        userid = current_user.userid if hasattr(current_user, 'userid') else current_user.get('userid')
        result = service.approve_request(
            request_id=request.request_id,
            approved_amount=request.approved_amount,
            admin_notes=request.admin_notes,
            admin_userid=userid
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/reject")
async def reject_request(request: RejectRequestModel, current_user = Depends(get_current_user)):
    """Reject credit request (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = CreditRequestService()
        userid = current_user.userid if hasattr(current_user, 'userid') else current_user.get('userid')
        result = service.reject_request(
            request_id=request.request_id,
            admin_notes=request.admin_notes,
            admin_userid=userid
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))