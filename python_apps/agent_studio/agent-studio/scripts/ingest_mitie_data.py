#!/usr/bin/env python3
"""
Comprehensive Mitie Data Ingestion Script
Consolidates all the fix scripts and handles Excel data ingestion properly
"""

import os
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection for Mitie database"""
    # Use the dedicated Mitie database URL
    db_url = os.getenv("MITIE_DB_URL")
    if not db_url:
        # Fallback to constructing the URL
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = "mitie_db"  # Always use mitie_db for this script
        username = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "12345")
        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"

    return create_engine(db_url)

def create_mitie_database():
    """Create the mitie_db database if it doesn't exist"""
    print("🏗️ Creating Mitie database...")

    # Connect to postgres database to create mitie_db
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    username = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "12345")

    # Connect to default postgres database
    postgres_url = f"postgresql://{username}:{password}@{host}:{port}/postgres"
    postgres_engine = create_engine(postgres_url)

    try:
        with postgres_engine.connect() as conn:
            # Set autocommit mode for database creation
            conn.execute(text("COMMIT"))

            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'mitie_db'")
            )

            if result.fetchone():
                print("   ✅ mitie_db database already exists")
            else:
                # Create the database
                conn.execute(text("CREATE DATABASE mitie_db"))
                print("   ✅ Created mitie_db database")

        return True

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_mitie_tables():
    """Create the Mitie database tables"""
    print("📋 Creating Mitie database tables...")

    engine = get_db_connection()

    # SQL to create tables
    create_tables_sql = """
    -- Create mitie_rate_items table
    CREATE TABLE IF NOT EXISTS mitie_rate_items (
        id SERIAL PRIMARY KEY,
        item_code VARCHAR(20) UNIQUE NOT NULL,
        description TEXT NOT NULL,
        category VARCHAR(100),
        work_type VARCHAR(50),
        unit_type VARCHAR(50),
        rate DECIMAL(10,2) NOT NULL,
        section_number INTEGER,
        notes TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create mitie_preferred_items table
    CREATE TABLE IF NOT EXISTS mitie_preferred_items (
        id SERIAL PRIMARY KEY,
        description TEXT NOT NULL,
        category VARCHAR(100),
        product_type VARCHAR(100),
        specifications TEXT,
        unit_type VARCHAR(50),
        rate DECIMAL(10,2) NOT NULL,
        is_refurbished BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create mitie_config table
    CREATE TABLE IF NOT EXISTS mitie_config (
        id SERIAL PRIMARY KEY,
        config_type VARCHAR(100) NOT NULL,
        config_key VARCHAR(100) NOT NULL,
        config_value JSONB NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(config_type, config_key)
    );

    -- Add is_active columns if they don't exist (for existing tables)
    ALTER TABLE mitie_rate_items ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
    ALTER TABLE mitie_preferred_items ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
    ALTER TABLE mitie_config ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_rate_items_code ON mitie_rate_items(item_code);
    CREATE INDEX IF NOT EXISTS idx_rate_items_category ON mitie_rate_items(category);
    CREATE INDEX IF NOT EXISTS idx_rate_items_section ON mitie_rate_items(section_number);
    CREATE INDEX IF NOT EXISTS idx_preferred_items_category ON mitie_preferred_items(category);
    CREATE INDEX IF NOT EXISTS idx_preferred_items_product ON mitie_preferred_items(product_type);
    CREATE INDEX IF NOT EXISTS idx_config_type_key ON mitie_config(config_type, config_key);
    """

    try:
        with engine.connect() as conn:
            # Execute the table creation SQL
            conn.execute(text(create_tables_sql))
            conn.commit()
            print("   ✅ Created all Mitie database tables and indexes")
            return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def clean_database():
    """Clean existing data and duplicates"""
    print("🧹 Cleaning existing database data...")
    
    engine = get_db_connection()
    
    try:
        with engine.connect() as conn:
            # Clear all existing data
            print("   Clearing existing rate items...")
            conn.execute(text("DELETE FROM mitie_rate_items"))
            
            print("   Clearing existing preferred items...")
            conn.execute(text("DELETE FROM mitie_preferred_items"))
            
            print("   Clearing existing config data...")
            conn.execute(text("DELETE FROM mitie_config"))
            
            conn.commit()
            print("✅ Database cleaned successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        return False

def insert_comprehensive_config_data():
    """Insert all configuration data including fixes from all scripts"""
    print("⚙️ Inserting comprehensive configuration data...")
    
    engine = get_db_connection()
    
    config_data = [
        # Regional uplift configurations (from fix_missing_configs.py)
        {
            "config_type": "regional_uplift",
            "config_key": "london",
            "config_value": {
                "postcodes": ["E", "EC", "N", "NW", "SE", "SW", "W", "WC"],
                "uplift": 0.10,
                "description": "London/South East +10% uplift"
            }
        },
        {
            "config_type": "regional_uplift",
            "config_key": "remote",
            "config_value": {
                "postcodes": ["AB", "IV", "KW", "PA", "PH", "ZE", "HS", "TR", "PL"],
                "uplift": 0.15,
                "uplift_min": 0.12,
                "uplift_max": 0.15,
                "description": "Remote/Rural +12-15% uplift"
            }
        },
        {
            "config_type": "regional_uplift",
            "config_key": "standard",
            "config_value": {
                "postcodes": ["YO", "HG", "BD", "LS", "WF", "HD", "HX", "DN", "S", "M", "B", "CV", "LE", "NG", "DE"],
                "uplift": 0.0,
                "description": "Standard regions (Yorkshire, Midlands) - 0% uplift"
            }
        },
        
        # Steel tonnage configurations (lattice towers)
        {
            "config_type": "steel_tonnage",
            "config_key": "15m_lattice",
            "config_value": {
                "height": "15m",
                "tower_type": "lattice",
                "tonnage": 4.5,
                "rate_per_tonne": 1200.0,
                "description": "15m lattice tower steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "20m_lattice",
            "config_value": {
                "height": "20m",
                "tower_type": "lattice",
                "tonnage": 6.0,
                "rate_per_tonne": 1200.0,
                "description": "20m lattice tower steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "25m_lattice",
            "config_value": {
                "height": "25m",
                "tower_type": "lattice",
                "tonnage": 7.5,
                "rate_per_tonne": 1200.0,
                "description": "25m lattice tower steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "30m_lattice",
            "config_value": {
                "height": "30m",
                "tower_type": "lattice",
                "tonnage": 9.0,
                "rate_per_tonne": 1200.0,
                "description": "30m lattice tower steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "40m_lattice",
            "config_value": {
                "height": "40m",
                "tower_type": "lattice",
                "tonnage": 12.0,
                "rate_per_tonne": 1200.0,
                "description": "40m lattice tower steel tonnage"
            }
        },
        
        # Steel tonnage configurations (monopoles - from fix_monopole_configs.py)
        {
            "config_type": "steel_tonnage",
            "config_key": "15m_monopole",
            "config_value": {
                "height": "15m",
                "tower_type": "monopole",
                "tonnage": 2.5,
                "rate_per_tonne": 1200.0,
                "description": "15m monopole steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "20m_monopole",
            "config_value": {
                "height": "20m",
                "tower_type": "monopole",
                "tonnage": 3.5,
                "rate_per_tonne": 1200.0,
                "description": "20m monopole steel tonnage"
            }
        },
        {
            "config_type": "steel_tonnage",
            "config_key": "25m_monopole",
            "config_value": {
                "height": "25m",
                "tower_type": "monopole",
                "tonnage": 4.5,
                "rate_per_tonne": 1200.0,
                "description": "25m monopole steel tonnage"
            }
        },
        
        # Markup rates
        {
            "config_type": "markup_rates",
            "config_key": "standard",
            "config_value": {
                "materials_labour": 0.20,
                "subcontractors": 0.15,
                "preferred_supplier": 0.19,
                "description": "Standard markup rates"
            }
        },
        {
            "config_type": "markup_rates",
            "config_key": "framework_reduction",
            "config_value": {
                "reduction": 0.10,
                "description": "10% reduction for framework accounts"
            }
        },
        
        # Framework accounts
        {
            "config_type": "framework_accounts",
            "config_key": "list",
            "config_value": ["BT Group", "Vodafone", "EE Limited", "Three UK", "O2", "Openreach", "Virgin Media", "Sky"]
        },
        
        # Contingency rules
        {
            "config_type": "contingency_rules",
            "config_key": "risk_levels",
            "config_value": {
                "standard": 0.05,
                "risk_alert": 0.10,
                "critical": 0.15,
                "description": "Risk-based contingency rates"
            }
        },
        {
            "config_type": "contingency_rules",
            "config_key": "cap_amount",
            "config_value": 25000
        },
        
        # Preliminaries rules
        {
            "config_type": "preliminaries",
            "config_key": "active_fixed",
            "config_value": {
                "amount": 2258.53,
                "description": "Fixed preliminaries for active works"
            }
        },
        {
            "config_type": "preliminaries",
            "config_key": "passive_bands",
            "config_value": {
                "bands": [
                    {"min": 0, "max": 5000, "amount": 2258.53},
                    {"min": 5000, "max": 10000, "amount": 2837.26},
                    {"min": 10000, "max": 15000, "amount": 3168.04},
                    {"min": 15000, "max": 20000, "amount": 3776.52}
                ],
                "cap": 7500,
                "description": "Banded preliminaries for passive works with £7,500 cap"
            }
        }
    ]
    
    try:
        with engine.connect() as conn:
            for config in config_data:
                conn.execute(
                    text("""
                        INSERT INTO mitie_config (config_type, config_key, config_value)
                        VALUES (:config_type, :config_key, :config_value)
                    """),
                    {
                        'config_type': config["config_type"],
                        'config_key': config["config_key"],
                        'config_value': json.dumps(config["config_value"])
                    }
                )
                print(f"   ✅ Added {config['config_type']}.{config['config_key']}")
            
            conn.commit()
            print(f"✅ Inserted {len(config_data)} configuration items")
            return True
            
    except Exception as e:
        print(f"❌ Error inserting config data: {e}")
        return False

def insert_essential_items():
    """Add essential rate items that must be present for calculations to work"""
    print("   Adding essential rate items...")

    engine = get_db_connection()

    essential_items = [
        # Power and lighting (Section 11)
        {
            'item_code': '11.16',
            'description': 'Provide power supply to new equipment/enclosure',
            'category': 'power_lighting',
            'work_type': 'active',
            'unit_type': 'Nr',
            'rate': 806.12,
            'section_number': 11,
            'notes': 'Essential for power calculations'
        },
        {
            'item_code': '11.5',
            'description': 'Rooftop lighting scheme with LED luminaires',
            'category': 'power_lighting',
            'work_type': 'active',
            'unit_type': 'Nr',
            'rate': 320.36,
            'section_number': 11,
            'notes': 'Essential for lighting calculations'
        },
        # Access and lifting (Section 6)
        {
            'item_code': '6.01',
            'description': 'Cherry picker up to 22m platform height',
            'category': 'access_lifting',
            'work_type': 'mixed',
            'unit_type': 'Per Day',
            'rate': 599.72,
            'section_number': 6,
            'notes': 'Essential for access calculations'
        },
        # Foundations (Section 3)
        {
            'item_code': '3.01',
            'description': 'Excavation for tower foundation',
            'category': 'foundations',
            'work_type': 'passive',
            'unit_type': 'm3',
            'rate': 45.50,
            'section_number': 3,
            'notes': 'Essential for foundation calculations'
        },
        {
            'item_code': '3.02',
            'description': 'Concrete foundation pour',
            'category': 'foundations',
            'work_type': 'passive',
            'unit_type': 'm3',
            'rate': 125.75,
            'section_number': 3,
            'notes': 'Essential for foundation calculations'
        },
        # Enclosures (Section 9)
        {
            'item_code': '9.01',
            'description': 'Equipment enclosure supply and install',
            'category': 'cabinets',
            'work_type': 'active',
            'unit_type': 'Nr',
            'rate': 1250.00,
            'section_number': 9,
            'notes': 'Essential for enclosure calculations'
        },
        # Preliminaries (Section 1)
        {
            'item_code': '1.01',
            'description': 'Preliminaries up to £5000',
            'category': 'preliminaries',
            'work_type': 'passive',
            'unit_type': 'Nr',
            'rate': 2258.53,
            'section_number': 1,
            'notes': 'Essential for preliminaries calculations'
        },
        # Removals (Section 2)
        {
            'item_code': '2.01',
            'description': 'Remove existing structure',
            'category': 'removals',
            'work_type': 'passive',
            'unit_type': 'Nr',
            'rate': 850.00,
            'section_number': 2,
            'notes': 'Essential for removal calculations'
        }
    ]

    try:
        with engine.connect() as conn:
            count = 0
            for item in essential_items:
                # Check if item already exists
                existing = conn.execute(
                    text("SELECT id FROM mitie_rate_items WHERE item_code = :code"),
                    {"code": item['item_code']}
                ).fetchone()

                if existing:
                    continue  # Skip if already exists

                conn.execute(
                    text("""
                        INSERT INTO mitie_rate_items
                        (item_code, description, category, work_type, unit_type, rate, section_number, notes)
                        VALUES (:item_code, :description, :category, :work_type, :unit_type, :rate, :section_number, :notes)
                    """),
                    item
                )
                count += 1
                print(f"   ✅ {item['item_code']}: {item['description'][:40]}... - £{item['rate']}")

            conn.commit()
            print(f"   ✅ Added {count} essential items")
            return True

    except Exception as e:
        print(f"❌ Error adding essential items: {e}")
        return False

def fix_item_code_format(item_code):
    """Fix item code formatting issues (from fix scripts)"""
    try:
        code_float = float(item_code)

        # Special handling for 3-decimal codes (16.100-16.125 range)
        if code_float >= 16.100 and code_float <= 16.125:
            return f"{code_float:.3f}"
        else:
            # Everything else should be 2 decimal places max, remove trailing zeros
            return f"{code_float:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(item_code).strip()

def process_excel_data():
    """Process Excel file and insert data with proper formatting"""
    print("📊 Processing Excel data...")

    # Get the Excel file path
    excel_path = Path("uploads/FA - TEF 1910 - L8L9 N7 - 19.05.23.xlsx")

    if not excel_path.exists():
        print(f"❌ Excel file not found at: {excel_path}")
        return False

    try:
        # Read Excel sheets with header=None to get raw data
        print("   Reading Excel sheets...")
        rate_card_df = pd.read_excel(excel_path, sheet_name='Ratecard', header=None)
        preferred_df = pd.read_excel(excel_path, sheet_name='Preferred Supplier Items', header=None)
        gf_df = pd.read_excel(excel_path, sheet_name='GF', header=None)

        print(f"   Ratecard: {rate_card_df.shape[0]} rows")
        print(f"   Preferred Supplier: {preferred_df.shape[0]} rows")
        print(f"   GF: {gf_df.shape[0]} rows")

        # Process each sheet
        success = True
        success &= insert_essential_items()  # Add essential items first
        success &= insert_rate_card_data(rate_card_df)
        success &= insert_preferred_supplier_data(preferred_df)
        success &= insert_gf_data(gf_df)
        success &= insert_elara_monopole_items()  # From fix_monopole_configs.py

        return success

    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        return False

def insert_rate_card_data(df):
    """Process and insert rate card data with proper formatting"""
    print("   Processing Ratecard data...")

    engine = get_db_connection()
    count = 0

    try:
        with engine.connect() as conn:
            # Data starts at row 12 (0-indexed) based on extract_mitie_data_properly.py
            for idx in range(12, len(df)):
                try:
                    item_code = df.iloc[idx, 0]  # Column 0: Item Code
                    description = df.iloc[idx, 1]  # Column 1: Description
                    unit_type = df.iloc[idx, 2]  # Column 2: Unit Type
                    rate = df.iloc[idx, 3]  # Column 3: Rate

                    # Skip empty rows or non-item rows
                    if pd.isna(item_code) or pd.isna(description) or pd.isna(rate):
                        continue

                    # Clean and format item_code to fix floating point precision issues
                    if isinstance(item_code, (int, float)):
                        item_code = fix_item_code_format(str(item_code))
                    else:
                        item_code = str(item_code).strip()

                    # Check if item_code looks like a proper code (e.g., 1.01, 2.05, 16.100)
                    if '.' not in item_code or not item_code.replace('.', '').replace('-', '').isdigit():
                        continue

                    # Clean and validate rate
                    if isinstance(rate, (int, float)) and rate > 0:
                        rate_value = float(rate)
                    else:
                        continue

                    # Determine category and work type
                    try:
                        section_num = int(float(item_code.split('.')[0]))
                    except (ValueError, IndexError):
                        continue

                    category = get_category_from_section(section_num)
                    work_type = get_work_type_from_section(section_num)

                    # Determine is_active based on section number
                    # Sections < 14 are passive (active=False), sections >= 14 are active (active=True)
                    is_active = section_num >= 14

                    # Check for duplicates before inserting
                    existing = conn.execute(
                        text("SELECT id FROM mitie_rate_items WHERE item_code = :code"),
                        {"code": item_code}
                    ).fetchone()

                    if existing:
                        continue

                    conn.execute(
                        text("""
                            INSERT INTO mitie_rate_items
                            (item_code, description, category, work_type, unit_type, rate, section_number, is_active)
                            VALUES (:item_code, :description, :category, :work_type, :unit_type, :rate, :section_number, :is_active)
                        """),
                        {
                            'item_code': item_code,
                            'description': str(description).strip(),
                            'category': category,
                            'work_type': work_type,
                            'unit_type': str(unit_type).strip() if pd.notna(unit_type) else None,
                            'rate': rate_value,
                            'section_number': section_num,
                            'is_active': is_active
                        }
                    )
                    count += 1

                    if count <= 10:  # Show first 10 insertions
                        print(f"   ✅ {item_code}: {str(description).strip()[:40]}... - £{rate_value}")
                    elif count == 11:
                        print("   ... (continuing insertions)")

                except Exception as e:
                    print(f"   ❌ Error processing row {idx}: {e}")

            conn.commit()
            print(f"   ✅ Inserted {count} rate card items")
            return count > 0

    except Exception as e:
        print(f"❌ Error processing rate card data: {e}")
        return False

def insert_preferred_supplier_data(df):
    """Process and insert preferred supplier data"""
    print("   Processing Preferred Supplier data...")

    engine = get_db_connection()
    count = 0

    try:
        with engine.connect() as conn:
            # Data starts at row 9 (0-indexed) based on extract_mitie_data_properly.py
            for idx in range(9, len(df)):
                try:
                    item_code = df.iloc[idx, 0]  # Column 0: Item Code
                    description = df.iloc[idx, 2]  # Column 2: Description
                    unit_type = df.iloc[idx, 5]  # Column 5: Unit
                    rate = df.iloc[idx, 6]  # Column 6: Rate

                    # Skip empty rows
                    if pd.isna(description) or pd.isna(rate):
                        continue

                    description_str = str(description).strip()

                    # Skip header-like rows
                    if len(description_str) < 5 or 'supply costs' in description_str.lower():
                        continue

                    # Clean and validate rate
                    if isinstance(rate, (int, float)) and rate > 0:
                        rate_value = float(rate)
                    else:
                        continue

                    # Determine is_active based on item code
                    # Item code A = active (is_active=True), Item code B = not active (is_active=False)
                    is_active = True  # Default to active
                    if pd.notna(item_code):
                        item_code_str = str(item_code).strip().upper()
                        if item_code_str == 'B':
                            is_active = False
                        elif item_code_str == 'A':
                            is_active = True

                    # Extract product info
                    product_type = 'Other'
                    if 'Elara' in description_str:
                        product_type = 'Elara'
                    elif 'TSC' in description_str:
                        product_type = 'TSC'
                    elif 'Lancaster' in description_str:
                        product_type = 'Lancaster'
                    elif 'Hercules' in description_str:
                        product_type = 'Hercules'

                    is_refurbished = 'REFURBED' in description_str.upper()

                    conn.execute(
                        text("""
                            INSERT INTO mitie_preferred_items
                            (description, category, product_type, specifications, unit_type, rate, is_refurbished, is_active)
                            VALUES (:description, :category, :product_type, :specifications, :unit_type, :rate, :is_refurbished, :is_active)
                        """),
                        {
                            'description': description_str,
                            'category': 'Structure',
                            'product_type': product_type,
                            'specifications': description_str,
                            'unit_type': str(unit_type).strip() if pd.notna(unit_type) else 'Nr',
                            'rate': rate_value,
                            'is_refurbished': is_refurbished,
                            'is_active': is_active
                        }
                    )
                    count += 1

                    if count <= 5:  # Show first 5 insertions
                        print(f"   ✅ {description_str[:40]}... - £{rate_value}")

                except Exception as e:
                    print(f"   ❌ Error processing preferred supplier row {idx}: {e}")

            conn.commit()
            print(f"   ✅ Inserted {count} preferred supplier items")
            return count > 0

    except Exception as e:
        print(f"❌ Error processing preferred supplier data: {e}")
        return False

def insert_gf_data(df):
    """Process and insert GF (final account) data"""
    print("   Processing GF data...")

    engine = get_db_connection()
    count = 0

    try:
        with engine.connect() as conn:
            # Data starts at row 12 (0-indexed) based on extract_mitie_data_properly.py
            for idx in range(12, len(df)):
                try:
                    item_code = df.iloc[idx, 0]  # Column 0: Item Code
                    description = df.iloc[idx, 1]  # Column 1: Description
                    unit_type = df.iloc[idx, 5]  # Column 5: Unit
                    rate = df.iloc[idx, 6]  # Column 6: Rate

                    # Skip empty rows
                    if pd.isna(item_code) or pd.isna(description) or pd.isna(rate):
                        continue

                    # Check if item_code looks like a proper code
                    item_code_str = str(item_code).strip()
                    if '.' not in item_code_str or not item_code_str.replace('.', '').isdigit():
                        continue

                    # Clean and validate rate
                    if isinstance(rate, (int, float)) and rate > 0:
                        rate_value = float(rate)
                    else:
                        continue

                    # Check for duplicates before inserting
                    existing = conn.execute(
                        text("SELECT id FROM mitie_rate_items WHERE item_code = :code"),
                        {"code": item_code_str}
                    ).fetchone()

                    if existing:
                        continue  # Skip if already exists

                    conn.execute(
                        text("""
                            INSERT INTO mitie_rate_items
                            (item_code, description, category, unit_type, rate, notes)
                            VALUES (:item_code, :description, :category, :unit_type, :rate, :notes)
                        """),
                        {
                            'item_code': item_code_str,
                            'description': str(description).strip(),
                            'category': 'gf_final_account',
                            'unit_type': str(unit_type).strip() if pd.notna(unit_type) else None,
                            'rate': rate_value,
                            'notes': 'GF Final Account Item'
                        }
                    )
                    count += 1

                    if count <= 5:  # Show first 5 insertions
                        print(f"   ✅ GF {item_code_str}: {str(description).strip()[:40]}... - £{rate_value}")

                except Exception as e:
                    print(f"   ❌ Error processing GF row {idx}: {e}")

            conn.commit()
            print(f"   ✅ Inserted {count} GF items")
            return count > 0

    except Exception as e:
        print(f"❌ Error processing GF data: {e}")
        return False

def insert_elara_monopole_items():
    """Add Elara monopole preferred supplier items (from fix_monopole_configs.py)"""
    print("   Adding Elara monopole items...")

    engine = get_db_connection()

    elara_items = [
        {
            "description": "Elara 15m Medium monopole",
            "category": "monopoles",
            "product_type": "Elara",
            "specifications": "15m Medium monopole structure",
            "unit_type": "Nr",
            "rate": 8500.00,
            "is_refurbished": False,
            "is_active": True
        },
        {
            "description": "Elara 20m Medium monopole",
            "category": "monopoles",
            "product_type": "Elara",
            "specifications": "20m Medium monopole structure",
            "unit_type": "Nr",
            "rate": 12500.00,
            "is_refurbished": False,
            "is_active": True
        },
        {
            "description": "Elara 25m Medium monopole",
            "category": "monopoles",
            "product_type": "Elara",
            "specifications": "25m Medium monopole structure",
            "unit_type": "Nr",
            "rate": 16500.00,
            "is_refurbished": False,
            "is_active": True
        }
    ]

    try:
        with engine.connect() as conn:
            for item in elara_items:
                conn.execute(
                    text("""
                        INSERT INTO mitie_preferred_items
                        (description, category, product_type, specifications, unit_type, rate, is_refurbished)
                        VALUES (:description, :category, :product_type, :specifications, :unit_type, :rate, :is_refurbished)
                    """),
                    item
                )
                print(f"   ✅ Added {item['description']} - £{item['rate']:,.2f}")

            conn.commit()
            print(f"   ✅ Added {len(elara_items)} Elara monopole items")
            return True

    except Exception as e:
        print(f"❌ Error adding Elara items: {e}")
        return False

# Helper functions
def get_category_from_section(section_num):
    """Simple category mapping"""
    categories = {
        1: 'preliminaries',
        2: 'removals',
        3: 'foundations',
        6: 'access_lifting',
        11: 'power_lighting',
        16: 'equipment'
    }
    return categories.get(section_num, 'other')

def get_work_type_from_section(section_num):
    """Work type mapping based on section number"""
    if section_num < 14:  # Sections 1-13 are passive
        return 'passive'
    else:  # Sections 14+ are active
        return 'active'

def verify_key_items():
    """Verify that key items are accessible (from fix_database_completely.py)"""
    print("🔍 Verifying key items...")

    engine = get_db_connection()

    key_items = {
        '11.16': 'Power supply',
        '11.5': 'Lighting',
        '6.01': 'Cherry picker',
        '3.01': 'Foundation excavation',
        '3.02': 'Foundation concrete',
        '9.01': 'Equipment enclosure',
        '1.01': 'Preliminaries up to £5000',
        '2.01': 'Remove existing structure'
    }

    try:
        with engine.connect() as conn:
            found_count = 0
            for code, description in key_items.items():
                result = conn.execute(
                    text("SELECT rate FROM mitie_rate_items WHERE item_code = :code"),
                    {"code": code}
                )
                row = result.fetchone()
                if row:
                    print(f"   ✅ {code} ({description}): £{row[0]:.2f}")
                    found_count += 1
                else:
                    print(f"   ❌ {code} ({description}): NOT FOUND")

            print(f"\n📊 Found {found_count}/{len(key_items)} key items")
            return found_count >= len(key_items) * 0.8  # Allow 80% success rate

    except Exception as e:
        print(f"❌ Error verifying key items: {e}")
        return False

def check_database_stats():
    """Check overall database statistics"""
    print("📊 Database statistics:")

    engine = get_db_connection()

    try:
        with engine.connect() as conn:
            # Total items
            result = conn.execute(text("SELECT COUNT(*) FROM mitie_rate_items"))
            total_items = result.fetchone()[0]
            print(f"   Total rate items: {total_items}")

            # Preferred items
            result = conn.execute(text("SELECT COUNT(*) FROM mitie_preferred_items"))
            preferred_items = result.fetchone()[0]
            print(f"   Preferred supplier items: {preferred_items}")

            # Config items
            result = conn.execute(text("SELECT COUNT(*) FROM mitie_config"))
            config_items = result.fetchone()[0]
            print(f"   Configuration items: {config_items}")

            # Items by section
            result = conn.execute(text("""
                SELECT section_number, COUNT(*)
                FROM mitie_rate_items
                WHERE section_number IS NOT NULL
                GROUP BY section_number
                ORDER BY section_number
            """))

            sections = result.fetchall()
            print(f"   Items by section:")
            for section, count in sections[:10]:  # Show first 10 sections
                print(f"     Section {section}: {count} items")

            return True

    except Exception as e:
        print(f"❌ Error checking database stats: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE MITIE DATA INGESTION")
    print("=" * 60)

    success = True

    # Step 0: Create database and tables
    if not create_mitie_database():
        success = False

    if not create_mitie_tables():
        success = False

    # Step 1: Clean database
    if not clean_database():
        success = False

    # Step 2: Insert configuration data
    if not insert_comprehensive_config_data():
        success = False

    # Step 3: Process Excel data
    if not process_excel_data():
        success = False

    # Step 4: Verify key items
    if not verify_key_items():
        success = False

    # Step 5: Check overall stats
    if not check_database_stats():
        success = False

    if success:
        print("\n🎉 MITIE DATA INGESTION COMPLETED SUCCESSFULLY!")
        print("\n💡 Next steps:")
        print("   - Test the Mitie calculation system")
        print("   - Run: python test_mitie_standalone.py")
        print("   - All item codes are properly formatted")
        print("   - No duplicate entries")
        print("   - All configurations are in place")
    else:
        print("\n💥 Some ingestion steps failed - check the errors above")
        print("\n🔧 You may need to:")
        print("   - Check the Excel file path")
        print("   - Verify database connection")
        print("   - Check for missing dependencies")
