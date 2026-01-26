import pandas as pd
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv


async def load_excel_to_postgres(excel_file):
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database connection string from environment
        SR_ANALYTICS_DATABASE_URL = os.getenv("SR_ANALYTICS_DATABASE_URL")
        
        print(f"Connecting to database: {SR_ANALYTICS_DATABASE_URL}")
        engine = create_async_engine(SR_ANALYTICS_DATABASE_URL)
        
        print(f"Reading Excel file: {excel_file}")
        # Read the Excel file initially with string dtype
        df = pd.read_excel(excel_file, dtype=str)
        
        print(f"Found {len(df)} rows in Excel file")
        print("\nSample data:")
        print(df.head())
        
        # Clean column names - remove spaces and special characters
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
        
        # Convert specific columns to float and integer types
        float_columns = ['task_travel_time_hours', 'task_actual_time_hours', 'part_unit_cost', 'part_total_cost']
        int_columns = ['part_quantity']
        
        # Convert float columns
        for col in float_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
        
        # Convert integer columns
        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        print("\nImporting data to PostgreSQL...")
        # For async engines, we need to use a different approach for to_sql
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: df.to_sql(
                'sr_data_agent_table',
                sync_conn,
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=1000
            ))

        # Verify the import
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT COUNT(*) FROM sr_data_agent_table"))
            count = result.scalar()
            print(f"\nNumber of rows imported: {count}")

            print("\nSample of imported data:")
            sample = await connection.execute(text("SELECT * FROM sr_data_agent_table LIMIT 5"))
            for row in sample:
                print(row)

        print("Data import completed successfully!")
        return True

    except Exception as e:
        print(f"Error during import: {str(e)}")
        print("\nFull error details:", str(sys.exc_info()))
        return False


# if __name__ == "__main__":
#     excel_file = 'sr_data_excel_table.xlsx'
#     asyncio.run(load_excel_to_postgres(excel_file))

# Priorities: Group by customer, machine types (parts ordered in time frame), by location and by customer address,
# by task assignee.