"""Chat endpoints for customer interactions."""
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from app.config.database import get_db
from app.models import Business, Table, Message
from app.schemas.message import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    MessageCreate,
    MessageResponse
)
from app.services.websocket.connection_manager import manager
from app.services.ai.chat_service import ChatService

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Send a message to the chat bot.
    
    This is the main endpoint for chat interactions.
    It handles:
    1. Session management
    2. Context retrieval
    3. AI processing
    4. Response generation
    """
    # Generate session ID if not provided
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
    
    # Get business from table if provided
    business_id = None
    if request.table_id:
        table = db.query(Table).filter(Table.id == request.table_id).first()
        if table:
            business_id = table.business_id
    
    # Initialize chat service
    chat_service = ChatService(db, business_id)
    
    # Process message
    response = await chat_service.process_message(
        session_id=request.session_id,
        message=request.message,
        table_id=request.table_id,
        context=request.context
    )
    
    return ChatResponse(
        message=response["message"],
        session_id=request.session_id,
        suggested_actions=response.get("suggested_actions", []),
        metadata=response.get("metadata", {})
    )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    table_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat.
    
    Maintains persistent connection for:
    1. Real-time message exchange
    2. Order status updates
    3. Notifications
    """
    await manager.connect(websocket, session_id)
    
    # Get business from table
    business_id = None
    if table_id:
        table = db.query(Table).filter(Table.id == table_id).first()
        if table:
            business_id = table.business_id
            # Mark table as occupied
            table.status = TableStatus.OCCUPIED
            db.commit()
    
    # Initialize chat service
    chat_service = ChatService(db, business_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to XoneBot chat",
            "session_id": session_id
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            
            # Process message
            response = await chat_service.process_message(
                session_id=session_id,
                message=data.get("message", ""),
                table_id=table_id,
                context=data.get("context", {})
            )
            
            # Send response
            await websocket.send_json({
                "type": "message",
                "message": response["message"],
                "suggested_actions": response.get("suggested_actions", []),
                "metadata": response.get("metadata", {})
            })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        # Free table if it was occupied
        if table_id and table:
            table.status = TableStatus.AVAILABLE
            db.commit()


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """Get chat session information."""
    # Get messages for session
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    first_message = messages[0]
    last_message = messages[-1]
    
    return ChatSession(
        session_id=session_id,
        business_id=first_message.business_id,
        table_id=None,  # Would need to track this separately
        created_at=first_message.created_at,
        last_message_at=last_message.created_at,
        message_count=len(messages),
        status="active" if (datetime.utcnow() - last_message.created_at).seconds < 3600 else "expired"
    )


@router.get("/session/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Any:
    """Get messages for a chat session."""
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).limit(limit).offset(offset).all()
    
    return messages