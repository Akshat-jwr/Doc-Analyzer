
from .background_table_extractor import BackgroundTableExtractor, extract_tables_background


# And update the __all__ list:
__all__ = [
    "storage_service",
    "StreamlinedPDFProcessor", 
    "process_pdf_phase_1_async",
    "BackgroundTableExtractor",  # Changed this
    "extract_tables_background"
]
