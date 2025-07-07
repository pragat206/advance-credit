#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p app/static_data

# Initialize database if needed
python -c "
from app.db import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
" 