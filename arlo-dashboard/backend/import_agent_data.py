import pandas as pd
from sqlalchemy import create_engine, text
import sys
from urllib.parse import quote_plus

def clean_percentage(value):
    """Clean percentage values and handle all formats including negative values"""
    if pd.isna(value):
        return 0.0
    try:
        # Convert to string and clean
        value = float(str(value).strip().replace('%', '').strip())
        # Multiply by 100 if value is between 0 and 1
        if -1 <= value <= 1:
            value = value * 100
        return value
    except:
        return 0.0

def clean_agent_name(name):
    """Clean agent name"""
    if pd.isna(name):
        return ''
    return str(name).strip()

def import_excel_to_postgres(excel_file, sheet_name):
    try:
        # Database connection parameters
        DB_PARAMS = {
            'host': 'localhost',
            'database': 'arlo_dashboard',
            'user': 'postgres',
            'password': 'Vijaya@2210$',
            'port': '5432'
        }

        password = quote_plus(DB_PARAMS['password'])
        connection_string = f"postgresql://{DB_PARAMS['user']}:{password}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
        
        print("Connecting to database...")
        engine = create_engine(connection_string)

        print("Reading Excel file...")
        print(f"Attempting to read: {excel_file}")
        print(f"Using sheet: {sheet_name}")
        
        # Skip the first 5 rows to get to the actual headers
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=5)
        
        print("\nFirst few rows of raw data:")
        print(df.head())
        
        # Clean up any whitespace in column names
        df.columns = df.columns.str.strip()
        
        print("\nColumns after cleaning:")
        print(df.columns.tolist())
        
        # Clean up the data
        df = df.dropna(how='all')
        
        # Create cleaned dataframe with correct column mappings
        df_cleaned = pd.DataFrame({
            'agent_name': df['Case Owner'].apply(clean_agent_name),
            'date': pd.to_datetime(df['Date']),
            'ai_usage': df['AI Usage'].fillna('No').astype(str),
            'case_symptoms': df['Case Symptoms'].fillna(''),
            'num_surveys': pd.to_numeric(df['# Of Surveys'], errors='coerce').fillna(0).astype(int),
            'positive_surveys': pd.to_numeric(df['# of Positive Survey'], errors='coerce').fillna(0).astype(int),
            'negative_surveys': pd.to_numeric(df['# of Negative Survey'], errors='coerce').fillna(0).astype(int),
            'positive_asat': pd.to_numeric(df['# of Positive ASAT Survey'], errors='coerce').fillna(0).astype(int),
            'negative_asat': pd.to_numeric(df['# of Negative ASAT Survey'], errors='coerce').fillna(0).astype(int),
            'asat_percentage': df['ASAT%'].apply(clean_percentage),
            'csat_percentage': df['CSAT %'].apply(clean_percentage),
            'nps_percentage': df['NPS %'].apply(clean_percentage),
            'ces_ws': pd.to_numeric(df['CES WS'], errors='coerce').fillna(0),
            'fcr_percentage': df['FCR %'].apply(clean_percentage)
        })

        # Remove rows with invalid dates or empty agent names
        df_cleaned = df_cleaned[df_cleaned['date'].notna() & df_cleaned['agent_name'].notna()]

        print(f"\nFound {len(df_cleaned)} rows to import")
        print("\nSample of data to be imported:")
        print(df_cleaned.head())

        print("\nImporting data to PostgreSQL...")
        df_cleaned.to_sql(
            'agent_metrics',
            engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )

        # Create indexes after import
        print("\nCreating indexes...")
        with engine.connect() as connection:
            # Create time-based index
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_date 
                ON agent_metrics (date);
            """))
            
            # Create compound index for date and agent
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_date_agent 
                ON agent_metrics (date, agent_name);
            """))
            
            # Create index for agent name
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent 
                ON agent_metrics (agent_name);
            """))

        # Verify the import
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM agent_metrics")).scalar()
            print(f"\nNumber of rows imported: {result}")
            
            print("\nVerifying indexes...")
            indexes = connection.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'agent_metrics';
            """))
            print("\nCreated indexes:")
            for idx in indexes:
                print(f"- {idx[0]}: {idx[1]}")
            
            print("\nSample of imported data:")
            sample = connection.execute(text("""
                SELECT 
                    agent_name,
                    date,
                    ai_usage,
                    num_surveys,
                    positive_surveys,
                    negative_surveys,
                    asat_percentage,
                    csat_percentage,
                    nps_percentage,
                    ces_ws,
                    fcr_percentage
                FROM agent_metrics 
                ORDER BY date, agent_name
                LIMIT 5
            """))
            for row in sample:
                print(row)

        print("Data import completed successfully!")
        return True

    except Exception as e:
        print(f"Error during import: {str(e)}")
        print("\nFull error details:", str(sys.exc_info()))
        return False

if __name__ == "__main__":
    excel_file = '../src/Assets/Agents-december.xlsx'
    
    # First read the Excel file to get the sheet name
    xls = pd.ExcelFile(excel_file)
    sheet_name = xls.sheet_names[0]  # Get the first sheet name
    print(f"Found sheet name: {sheet_name}")
    
    import_excel_to_postgres(excel_file, sheet_name)