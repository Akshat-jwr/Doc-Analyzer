# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from typing import Optional
# from models.user import User
# from services.general_chatbot_service import general_chatbot_service
# from auth import get_current_active_user
# from utils.pydantic_objectid import PyObjectId
# from models.pdf import PDF

# router = APIRouter(prefix="/chat/general", tags=["General Chat"])

# class ChatMessage(BaseModel):
#     message: str
#     document_id: Optional[str] = None
#     conversation_id: str = "default"

# class IndexRequest(BaseModel):
#     document_id: str

# class ClearConversationRequest(BaseModel):
#     document_id: Optional[str] = None

# @router.post("/message")
# async def send_general_chat_message(
#     message: ChatMessage,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """✅ SIMPLE: Send chat message that works"""
#     try:
#         result = await general_chatbot_service.general_chat_with_document(
#             query=message.message,
#             document_id=message.document_id,
#             user_id=str(current_user.id),
#             conversation_id=message.conversation_id
#         )
#         return result
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/index-document")
# async def index_document_for_general_chat(
#     request: IndexRequest,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """✅ SIMPLE: Index document that works"""
#     try:
#         # Verify document access
#         document = await PDF.get(PyObjectId(request.document_id))
#         if not document:
#             raise HTTPException(status_code=404, detail="Document not found")
        
#         if document.user_id != current_user.id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         result = await general_chatbot_service.index_document_for_general_chat(request.document_id)
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/document/{document_id}/info")
# async def get_document_general_chat_info(
#     document_id: str,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """✅ SIMPLE: Get document info"""
#     try:
#         # Verify document access
#         document = await PDF.get(PyObjectId(document_id))
#         if not document:
#             raise HTTPException(status_code=404, detail="Document not found")
        
#         if document.user_id != current_user.id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         result = await general_chatbot_service.get_document_general_chat_info(document_id)
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/conversations/{conversation_id}/clear")
# async def clear_general_chat_conversation(
#     conversation_id: str,
#     request: ClearConversationRequest,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """✅ SIMPLE: Clear conversation"""
#     try:
#         if request.document_id:
#             document = await PDF.get(PyObjectId(request.document_id))
#             if not document:
#                 raise HTTPException(status_code=404, detail="Document not found")
            
#             if document.user_id != current_user.id:
#                 raise HTTPException(status_code=403, detail="Access denied")
        
#         general_chatbot_service.clear_general_conversation(
#             conversation_id=conversation_id,
#             user_id=str(current_user.id),
#             document_id=request.document_id
#         )
        
#         return {
#             "success": True,
#             "message": "Conversation cleared",
#             "conversation_id": conversation_id
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/health")
# async def general_chat_health_check():
#     """✅ SIMPLE: Health check"""
#     try:
#         result = await general_chatbot_service.health_check()
#         return result
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/auto-index/{document_id}")
# async def auto_index_document_for_general_chat(
#     document_id: str,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """✅ SIMPLE: Auto-index"""
#     try:
#         # Verify document access
#         document = await PDF.get(PyObjectId(document_id))
#         if not document:
#             raise HTTPException(status_code=404, detail="Document not found")
        
#         if document.user_id != current_user.id:
#             raise HTTPException(status_code=403, detail="Access denied")
        
#         result = await general_chatbot_service.index_document_for_general_chat(document_id)
#         return {
#             **result,
#             "auto_indexed": True,
#             "trigger": "auto"
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
