from .auth import router as auth_router
from .health import router as health_router
from .pdf import router as pdf_router
from .tables import router as tables_router
from .llm_visualization import router as visualization_router
from .multi_chat import router as multi_chat_router

__all__ = ["auth_router", "health_router", "pdf_router", "tables_router","visualization_router","multi_chat_router"]
