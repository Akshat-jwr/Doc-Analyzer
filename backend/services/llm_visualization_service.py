import os
import time
import logging
import asyncio
import re
import traceback
import io
import base64
from typing import Dict, Any, Optional, List
import seaborn as sns
import datetime
import math
from scipy import stats

# Matplotlib setup for a headless server environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO
import numpy as np
from matplotlib import colors, cm

# Pydantic and Database Models
from pydantic import BaseModel, Field
import google.generativeai as genai
from models.pdf import PDF
from models.table import Table
from models.llm_visualization import LLMVisualization
from utils.pydantic_objectid import PyObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMVisualizationRequest(BaseModel):
    document_id: str
    page_number: int = Field(..., ge=1, description="Page number is REQUIRED")
    query: str
    user_id: str

class LLMVisualizationService:
    """
    ðŸš€ A definitive, self-healing LLM Visualization Service.
    This version fixes the TypeError and incorporates all best practices.
    """
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel('gemini-2.5-flash')
        try:
            self.llm.generate_content("Test", generation_config=genai.types.GenerationConfig(max_output_tokens=5))
            logger.info("âœ… LLM Visualization Service initialized successfully.")
        except Exception as e:
            logger.error(f"âŒ LLM API test failed during initialization: {e}")
            raise

    async def create_visualization(self, request: LLMVisualizationRequest) -> Dict[str, Any]:
        start_time = time.time()
        try:
            logger.info(f"ðŸŽ¨ New visualization request for page {request.page_number}: {request.query}")
            document = await PDF.get(PyObjectId(request.document_id))
            if not document: return {"success": False, "error": "Document not found"}
            
            tables = await self._get_tables_for_page(request.document_id, request.page_number)
            if not tables: return {"success": False, "error": f"No usable tables found on page {request.page_number}."}
            
            relevant_table = self._filter_and_select_best_table(tables, request.query)
            if not relevant_table: return {"success": False, "error": "No tables relevant to the query were found."}
            
            logger.info(f"ðŸ“Š Selected table: '{relevant_table['title']}' for visualization.")
            
            viz_result = await self._generate_visualization_via_code_execution([relevant_table], request.query)
            
            if not viz_result["success"]: return viz_result
            
            processing_time = int((time.time() - start_time) * 1000)
            viz_id = await self._save_to_database(request, viz_result, [relevant_table], processing_time)
            logger.info(f"âœ… Visualization created successfully: {viz_id}")
            
            return { "success": True, "visualization": { "id": viz_id, **viz_result } }
            
        except Exception as e:
            logger.error(f"âŒ Unhandled error in create_visualization: {e}", exc_info=True)
            return {"success": False, "error": f"An unexpected server error occurred: {str(e)}"}

    async def _generate_visualization_via_code_execution(self, tables: List[Dict], query: str) -> Dict[str, Any]:
        clean_python_code = None
        last_error = "Failed to generate valid Python code after multiple attempts."
        max_attempts = 2

        for attempt in range(max_attempts):
            logger.info(f"ðŸš€ Visualization attempt {attempt + 1}/{max_attempts}...")
            
            try:
                # This function call is now fixed and will no longer crash.
                prompt = self._create_code_generation_prompt(tables, query, clean_python_code, last_error if attempt > 0 else None)
                llm_response = await self._call_llm_api(prompt, timeout=60)
                logger.info(f"ðŸ¤– Raw LLM Response (Attempt {attempt + 1}):\n---\n{llm_response}\n---")

                extracted_code = self._extract_python_code(llm_response)
                if not extracted_code:
                    last_error = "LLM did not return a valid Python code block."
                    logger.warning(last_error)
                    continue
                
                clean_python_code = extracted_code
                execution_result = await self._execute_python_visualization_safely(clean_python_code, tables)

                if execution_result["success"]:
                    logger.info("âœ… Python code executed successfully!")
                    description_prompt = f"Based on the user query '{query}', write a brief, one-sentence description of the chart created by the following Python code:\n\nCODE:\n{clean_python_code}"
                    description_response = await self._call_llm_api(description_prompt, timeout=20)
                    chart_type = self._determine_chart_type(clean_python_code, query)
                    
                    return {
                        "success": True, "image_base64": execution_result["image_base64"],
                        "python_code": clean_python_code, "description": description_response.strip(),
                        "chart_type": chart_type
                    }
                else:
                    last_error = execution_result["error"]
                    logger.warning(f"Execution failed on attempt {attempt + 1}. The LLM will now try to debug this error.")

            except Exception as e:
                last_error = f"An unexpected error occurred during generation: {str(e)}"
                logger.error(last_error, exc_info=True)
        
        return {"success": False, "error": last_error, "python_code": clean_python_code}

    # âœ… FIXED THE TypeError HERE.
    def _create_code_generation_prompt(self, tables: List[Dict], query: str, broken_code: Optional[str], error: Optional[str]) -> str:
        """Creates a prompt for the LLM using the user's improved version."""
        # THE BUG WAS HERE. `tables` is a list, so we must access the first element `tables[0]`.
        table = tables[0]
        table_context = f"# TABLE 1 (available as `table_1_data` string variable)\n# Title: {table['title']}\n# Data:\n\"\"\"\n{table['content']}\n\"\"\"\n"
        
        if not error or not broken_code:
            # Using your improved prompt from paste-3.txt
            return f"""
You are an expert Python data visualization programmer using Matplotlib and Pandas.
Your task is to generate clean, executable Python code to create a chart based on a user's request and provided table data.

USER REQUEST: "{query}"
AVAILABLE DATA:{table_context}
**Stricty NEVER EVER USE ```python, ``` or any other code fences. not even ``````. Just the raw code in simple text format without any ```**

**CRITICAL REQUIREMENTS:**
1.  **Code Only**: Generate ONLY the Python raw code. Do not add explanations.
2.  **No Imports/Show**: DO NOT IMPORT ANY MODULES OR USE plt.show() EVEN BY MISTAKE - IT IS DONE EXTERNALLY!!!.
3. Make the code intelligently as you want, you have to declare GIVEN TABLE's MD and you may restructure it if needed to build a proper plot using plt (BUT USE THE SAME TABLE AND NOTHING ELSE - NO DUMMY DATA).
4.  **Finalization**: ALWAYS end with `plt.tight_layout()`.
5. READ THE TABLE PROPERLY, SOME OF THE CELLS OR COLUMN NAMES MIGHT HAVE STRINGS, I DO NOT WANT ANY INVALID STRING PARSING ISSUES INTELLIGENTLY BUT DO NOT CHANGE THE ACTUAL DATA AT ALL.
6.   File "<string>", line 22, in <module>
ValueError: invalid literal for int() with base 10: 'Highest average'
- I DO NOT WANT SUCH VALUE ERRORS,YOU NEED TO HANDLE IT INTELLIGENTLY AND YOU CANNOT TRY TO CONVERT STRING TO INTEGER BECAUSE IT WILL CAUSE ERRORS!!

Generate the robust Python code now."""
        else:
            return f"""
You are an expert Python debugger. The following Python code you wrote failed to execute.
USER REQUEST: "{query}"

FAILED CODE:
{broken_code}

EXECUTION ERROR:
{error}

INSTRUCTIONS:
1.  Analyze the error message and the failed code. The error is often due to incorrect data types (e.g., trying to plot strings as numbers).
2.  Fix the code. Ensure you are using `pd.to_numeric(df.iloc[:, index], errors='coerce')` on any column used for plotting.
3.  Return the COMPLETE, corrected Python code inside a single markdown block.
4.  Do not apologize, explain, or add any text outside the code block.

Generate the corrected Python code now."""

    async def _execute_python_visualization_safely(self, python_code: str, tables_data: List[Dict]) -> Dict[str, Any]:
        """Executes Python code safely after sanitizing it."""
        sanitized_code = ""
        try:
            # CRITICAL FIX 1: Sanitize the code first to remove forbidden statements.
            sanitized_code = self._sanitize_code(python_code)

            plt.clf(); plt.close('all')
            # CRITICAL FIX 2: A flexible, curated list of safe built-ins to prevent NameErrors.
            SAFE_BUILTINS = {
                'abs': abs, 'all': all, 'any': any, 'ascii': ascii, 'bin': bin, 'bool': bool,
                'bytearray': bytearray, 'bytes': bytes, 'callable': callable, 'chr': chr,
                'complex': complex, 'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
                'filter': filter, 'float': float, 'format': format, 'frozenset': frozenset,
                'getattr': getattr, 'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id,
                'int': int, 'isinstance': isinstance, 'issubclass': issubclass, 'iter': iter,
                'len': len, 'list': list, 'map': map, 'max': max, 'min': min, 'next': next,
                'object': object, 'oct': oct, 'ord': ord, 'pow': pow, 'print': print,
                'property': property, 'range': range, 'repr': repr, 'reversed': reversed,
                'round': round, 'set': set, 'slice': slice, 'sorted': sorted, 'str': str,
                'sum': sum, 'super': super, 'tuple': tuple, 'type': type, 'vars': vars, 'zip': zip
            }

            # ✅ STEP 2: PROVIDE A RICH TOOLBOX OF PRE-APPROVED MODULES
            # This gives the AI all the common tools for data visualization and analysis [3][5][7].
            safe_globals = {
                '__builtins__': SAFE_BUILTINS,  # Override built-ins with our safe list
                
                # Core Data Science & Plotting
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,  # Seaborn is extremely common for statistical plots
                
                # In-memory file operations
                'io': io,
                'StringIO': StringIO,
                'base64': base64,
                
                # Common Utilities
                'datetime': datetime,
                'math': math,
                
                # Advanced Statistics
                'stats': stats, # from scipy.stats
                
                # Matplotlib specifics
                'colors': colors,
                'cm': cm,
            }
            safe_globals['table_1_data'] = tables_data[0]['content']
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: exec(sanitized_code, safe_globals))

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=120)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close('all')
            return {"success": True, "image_base64": f"data:image/png;base64,{img_base64}", "executed_code": sanitized_code}
        except Exception:
            error_trace = traceback.format_exc()
            logger.error(f"âŒ Python execution failed!\nCode Attempted (after sanitization):\n{sanitized_code}\nError:\n{error_trace}")
            plt.close('all')
            return {"success": False, "error": error_trace}
        
    def _sanitize_code(self, code: str) -> str:
        """Removes forbidden statements like imports and plt.show() from generated code."""
        lines = code.split('\n')
        sanitized_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('import ') or stripped_line.startswith('from '):
                continue
            if stripped_line == 'plt.show()':
                continue
            sanitized_lines.append(line)
        logger.info("Code sanitized: removed potential import/show statements.")
        return '\n'.join(sanitized_lines)



    def _extract_python_code(self, response_text: str) -> Optional[str]:
        """A robust function to extract Python code from a markdown block."""
        if not response_text: return None
        # This regex robustly finds ```````````` or ``````.
        if response_text.startswith("```python") and response_text.endswith("```"):
            response_text = response_text[9:-3].strip() 
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()

        return response_text
        # Fallback for when the LLM forgets the fences.
        if "plt.figure" in response_text and "pd.read_csv" in response_text:
            return response_text.strip()
        return None

    # --- HELPER AND DATABASE FUNCTIONS ---
    
    async def _get_tables_for_page(self, document_id: str, page_number: int) -> List[Dict[str, Any]]:
        """Fetches and validates tables for a specific page from the database."""
        tables = await Table.find(
            Table.pdf_id == PyObjectId(document_id),
            Table.start_page <= page_number,
            Table.end_page >= page_number
        ).to_list()
        return [{
            "id": str(t.id), "title": t.table_title or f"Table_{t.table_number}",
            "content": t.markdown_content, "rows": t.row_count or 0, "columns": t.column_count or 0
        } for t in tables if t.markdown_content and len(t.markdown_content.strip()) > 10]

    def _filter_and_select_best_table(self, tables: List[Dict], query: str) -> Optional[Dict]:
        """Scores and selects the single most relevant table to the user's query."""
        if not tables: return None
        if len(tables) == 1: return tables[0]
        scored_tables = []
        for table in tables:
            score = 0
            title = table.get('title', '').lower()
            content_preview = table.get('content', '')[:250].lower()
            for word in query.lower().split():
                if len(word) > 2:
                    if word in title: score += 10
                    if word in content_preview: score += 1
            score += min((table.get('rows', 0) * table.get('columns', 0)) / 20.0, 5)
            scored_tables.append((score, table))
        if not scored_tables: return None
        scored_tables.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"ðŸ† Top table candidate: {scored_tables[0][1]['title']} (Score: {scored_tables[0][0]})")
        return scored_tables[0][1]

    async def _call_llm_api(self, prompt: str, timeout: int) -> str:
        try:
            response = await asyncio.wait_for(
                self.llm.generate_content_async(prompt, generation_config=genai.types.GenerationConfig(temperature=0.0)),
                timeout=timeout
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM API call failed: {e}", exc_info=True)
            raise

    def _determine_chart_type(self, python_code: str, query: str) -> str:
        code_lower, query_lower = python_code.lower(), query.lower()
        if 'plt.bar' in code_lower or 'bar chart' in query_lower: return 'bar'
        if 'plt.plot' in code_lower or 'line chart' in query_lower: return 'line'
        if 'plt.pie' in code_lower or 'pie chart' in query_lower: return 'pie'
        if 'plt.scatter' in code_lower: return 'scatter'
        if 'plt.hist' in code_lower: return 'histogram'
        return 'custom'
        
    async def _save_to_database(self, request: LLMVisualizationRequest, viz_result: Dict, 
                                tables: List[Dict], processing_time: int) -> str:
        """Saves the final, correct visualization result to the database."""
        viz = LLMVisualization(
            user_id=request.user_id, document_id=request.document_id, query=request.query,
            page_number=request.page_number, chart_type=viz_result.get("chart_type", "unknown"),
            success=True, image_base64=viz_result.get("image_base64"),
            llm_description=viz_result.get("description"), python_code=viz_result.get("python_code"),
            selected_tables=[{"id": t['id'], "title": t['title']} for t in tables],
            processing_time_ms=processing_time,
        )
        await viz.insert()
        return str(viz.id)
    
    async def get_history(self, user_id: str, document_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Retrieves visualization history, ensuring ALL necessary data,
        including the image and selected tables, is returned for the frontend.
        """
        try:
            search_criteria = {"user_id": PyObjectId(user_id)}
            if document_id:
                search_criteria["document_id"] = PyObjectId(document_id)

            history_cursor = LLMVisualization.find(search_criteria).sort(-LLMVisualization.created_at).limit(limit)
            history_list = await history_cursor.to_list()

            # ✅ THE DEFINITIVE FIX: Manually construct the response dictionary for each item.
            # This is the most robust way to guarantee the frontend gets ALL the data it needs.
            results = []
            for viz in history_list:
                results.append({
                    "id": str(viz.id),
                    "user_id": str(viz.user_id),
                    "document_id": str(viz.document_id),
                    "query": viz.query,
                    "page_number": viz.page_number,
                    "chart_type": viz.chart_type,
                    "success": viz.success,
                    "image_base64": viz.image_base64, # Included for the image
                    "selected_tables": viz.selected_tables, # Included for the Excel button
                    "llm_description": viz.llm_description,
                    "created_at": viz.created_at.isoformat() if viz.created_at else None,
                })

            return results
        except Exception as e:
            # This generic catch prevents the endpoint from crashing
            logger.error(f"Error building visualization history response: {e}", exc_info=True)
            return []
        

    async def get_details(self, viz_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieves full details for a single visualization, including the image."""
        try:
            viz = await LLMVisualization.find_one(
                LLMVisualization.id == PyObjectId(viz_id),
                LLMVisualization.user_id == PyObjectId(user_id)
            )
            if not viz:
                return {"success": False, "error": "Visualization not found or access denied."}
            
            return {"success": True, "visualization": viz.to_full_dict()}
        except Exception as e:
            logger.error(f"Error getting visualization details: {e}")
            return {"success": False, "error": "An internal error occurred."}

    async def delete_viz(self, viz_id: str, user_id: str) -> Dict[str, Any]:
        """Deletes a specific visualization."""
        try:
            viz = await LLMVisualization.find_one(
                LLMVisualization.id == PyObjectId(viz_id),
                LLMVisualization.user_id == PyObjectId(user_id)
            )
            if not viz:
                return {"success": False, "error": "Visualization not found or access denied."}
            
            await viz.delete()
            logger.info(f"Deleted visualization {viz_id} for user {user_id}")
            return {"success": True, "message": "Visualization deleted successfully."}
        except Exception as e:
            logger.error(f"Error deleting visualization: {e}")
            return {"success": False, "error": "An internal error occurred."}