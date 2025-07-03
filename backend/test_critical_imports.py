#!/usr/bin/env python3
"""
Test script to verify all critical imports work correctly.
This should be run inside the Docker container to verify the build.
"""

def test_imports():
    print("Testing critical imports...")
    
    try:
        # Core framework
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn")
        
        # Database
        import motor
        import pymongo
        import beanie
        import sqlalchemy
        import asyncpg
        import alembic
        print("✅ Database libraries")
        
        # PDF Processing
        import fitz  # PyMuPDF
        import PyPDF2
        import pdf2image
        import pytesseract
        from PIL import Image
        import reportlab
        print("✅ PDF processing libraries")
        
        # Document processing
        from docx import Document as DocxDocument
        print("✅ Word document processing (python-docx)")
        
        try:
            import docx2pdf
            print("✅ DOCX to PDF conversion")
        except ImportError:
            print("⚠️  docx2pdf not available (may need LibreOffice)")
        
        # File type detection
        import magic
        print("✅ File type detection (python-magic)")
        
        # AI/ML
        import google.generativeai as genai
        import sentence_transformers
        import transformers
        import torch
        import chromadb
        print("✅ AI/ML libraries")
        
        # Data science
        import pandas
        import numpy
        import matplotlib
        import seaborn
        import scipy
        print("✅ Data science libraries")
        
        # Utilities
        import requests
        import certifi
        import urllib3
        import jwt
        import aiofiles
        import cloudinary
        print("✅ Utility libraries")
        
        print("\n🎉 All critical imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
