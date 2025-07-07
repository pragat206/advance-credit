import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common_models import Base
from sqlalchemy import create_engine, text
from common_models import Employee, Lead, Partner, Reminder

DATABASE_URL = "sqlite:////Users/pragattiwari/news_slider/crm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create all tables
Base.metadata.create_all(engine)

# Add new columns to existing leads table if they don't exist
with engine.connect() as conn:
    # Check if new columns exist, if not add them
    result = conn.execute(text("PRAGMA table_info(leads)"))
    existing_columns = [row[1] for row in result.fetchall()]
    
    new_columns = [
        ("form_type", "VARCHAR(32)"),
        ("lead_type", "VARCHAR(64)"),
        ("total_emi", "FLOAT"),
        ("phone", "VARCHAR(64)"),
        ("occupation", "VARCHAR(64)"),
        ("loan_amount", "FLOAT"),
        ("loan_type", "VARCHAR(64)"),
        ("partner_name", "VARCHAR(128)"),
        ("current_monthly_emi", "FLOAT"),
        ("number_of_loans", "INTEGER"),
        ("average_interest_rate", "FLOAT"),
        ("credit_score", "VARCHAR(32)")
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}"))
                print(f"Added column: {column_name}")
            except Exception as e:
                print(f"Error adding column {column_name}: {e}")
    
    conn.commit()

print("All tables created and updated.") 