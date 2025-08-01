#!/usr/bin/env python3
"""
Main entry point for Render deployment
This file serves as the entry point for the entire application
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the main FastAPI app
from src.main_app.main import app

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 