from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_pg_db
from ..models import ChatHistory
from ..schemas import ChatRequest, ChatResponse, GuardrailInfo
from ..agent.graph import run_agent

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_pg_db)):
    result = run_agent(request.message, request.session_id)
    
    # Save to chat history
    chat_entry = ChatHistory(
        session_id=request.session_id,
        role="human",
        message=request.message,
        inbound_guardrail_hit=result.get("inbound_guardrail_hit"),
        guardrail_action="passed" if not result.get("inbound_guardrail_hit") and not result.get("outbound_guardrail_hit") else "blocked"
    )
    db.add(chat_entry)
    
    ai_entry = ChatHistory(
        session_id=request.session_id,
        role="ai",
        message=result["reply"],
        inbound_guardrail_hit=result.get("inbound_guardrail_hit"),
        outbound_guardrail_hit=result.get("outbound_guardrail_hit"),
        guardrail_action="blocked" if result.get("inbound_guardrail_hit") or result.get("outbound_guardrail_hit") else "passed"
    )
    db.add(ai_entry)
    db.commit()
    
    return ChatResponse(
        reply=result["reply"],
        session_id=request.session_id,
        inbound_guardrails=result["inbound_guardrails"],
        outbound_guardrails=result["outbound_guardrails"],
        show_order_button=result.get("show_order_button", False)
    )
