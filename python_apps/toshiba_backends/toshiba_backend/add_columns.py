import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def add_columns():
    """Add sr_ticket_id and original_request columns to the existing chat_data_final table"""
    # Get database URL from environment variable
    db_url = os.getenv("SQLALCHEMY_DATABASE_URL")

    # Create engine
    engine = create_async_engine(
        db_url,
        echo=True
    )

    try:
        async with engine.begin() as conn:
            # Execute raw SQL to add both columns if they don't exist
            # Use text() to create an executable SQL statement
            await conn.execute(
                text("ALTER TABLE chat_data_final "
                     "ADD COLUMN IF NOT EXISTS sr_ticket_id TEXT, "
                     "ADD COLUMN IF NOT EXISTS original_request TEXT")
            )
            print("Columns 'sr_ticket_id' and 'original_request' added successfully")
    except Exception as e:
        print(f"Error adding columns: {str(e)}")
    finally:
        await engine.dispose()
