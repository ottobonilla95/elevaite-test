#!/usr/bin/env python3
"""
Mitie Context Provider - Provides all available configurations as LLM context
"""

import json
from typing import Dict, List, Any
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from mitie_database import MitieDatabase
from sqlalchemy import text

def _get_static_rate_items() -> dict:
    """
    Static fallback rate items when database is unavailable.
    Based on known working rates from previous testing.
    """
    return {
        "power_lighting": [
            {"code": "11.16", "description": "Provide power supply to new equipment/enclosure", "rate": 806.12, "unit": "Nr"},
            {"code": "11.5", "description": "Rooftop lighting scheme with LED luminaires", "rate": 1200.0, "unit": "Nr"}
        ],
        "access_lifting": [
            {"code": "6.01", "description": "Cherry picker up to 22m platform height", "rate": 450.0, "unit": "Per Day"},
            {"code": "6.02", "description": "Crane hire for lifting operations", "rate": 800.0, "unit": "Per Day"}
        ],
        "materials_labour": [
            {"code": "3.01", "description": "Site removals and demolitions", "rate": 350.0, "unit": "Per Day"},
            {"code": "3.02", "description": "Foundation works", "rate": 1200.0, "unit": "m3"},
            {"code": "9.01", "description": "Trenches and ductwork", "rate": 85.0, "unit": "m"}
        ],
        "subcontractors": [
            {"code": "SUB_CRANE", "description": "Subcontractor crane operations", "rate": 1200.0, "unit": "Per Day"},
            {"code": "SUB_REMOVAL", "description": "Subcontractor removal services", "rate": 800.0, "unit": "Per Day"}
        ],
        "preliminaries": [
            {"code": "PRELIM", "description": "Preliminaries - passive_banded", "rate": 2258.53, "unit": "item"}
        ]
    }

def _get_static_preferred_items() -> list:
    """Static fallback preferred supplier items."""
    return [
        {"description": "Elara 15m Medium monopole", "product_type": "Elara", "specifications": "15m Medium monopole", "rate": 8500.0, "unit": "Nr"},
        {"description": "Elara 20m Medium monopole", "product_type": "Elara", "specifications": "20m Medium monopole", "rate": 12500.0, "unit": "Nr"},
        {"description": "Elara 25m Medium monopole", "product_type": "Elara", "specifications": "25m Medium monopole", "rate": 16500.0, "unit": "Nr"},
        {"description": "TSC 15m Standard monopole", "product_type": "TSC", "specifications": "15m Standard monopole", "rate": 7500.0, "unit": "Nr"},
        {"description": "TSC 20m Standard monopole", "product_type": "TSC", "specifications": "20m Standard monopole", "rate": 11000.0, "unit": "Nr"}
    ]

def _get_static_steel_configs() -> list:
    """Static fallback steel configurations."""
    return [
        {"key": "15m_monopole", "height": "15m", "tower_type": "monopole", "tonnage": 2.5, "rate_per_tonne": 1200.0, "description": "15m monopole steel structure"},
        {"key": "20m_monopole", "height": "20m", "tower_type": "monopole", "tonnage": 3.5, "rate_per_tonne": 1200.0, "description": "20m monopole steel structure"},
        {"key": "25m_monopole", "height": "25m", "tower_type": "monopole", "tonnage": 4.5, "rate_per_tonne": 1200.0, "description": "25m monopole steel structure"},
        {"key": "25m_lattice", "height": "25m", "tower_type": "lattice", "tonnage": 9.0, "rate_per_tonne": 1200.0, "description": "25m lattice tower steel structure"},
        {"key": "30m_lattice", "height": "30m", "tower_type": "lattice", "tonnage": 12.0, "rate_per_tonne": 1200.0, "description": "30m lattice tower steel structure"}
    ]

def _get_static_regional_configs() -> list:
    """Static fallback regional configurations."""
    return [
        {"region": "london", "postcodes": ["EC", "WC", "E", "N", "NW", "SE", "SW", "W"], "uplift_percentage": 25.0, "description": "London - 25% uplift"},
        {"region": "remote_rural", "postcodes": ["AB", "IV", "KW", "PA", "PH", "ZE"], "uplift_percentage": 15.0, "description": "Remote/Rural Scotland - 15% uplift"},
        {"region": "standard", "postcodes": ["YO", "HG", "BD", "LS", "M", "B", "CV"], "uplift_percentage": 0.0, "description": "Standard regions - 0% uplift"}
    ]

def get_all_available_mitie_configs() -> str:
    """
    Get all available Mitie configurations formatted for LLM context.
    Uses static data as fallback when database is unavailable.

    Returns:
        JSON string containing all available rate items, preferred items, steel configs, etc.
    """
    try:
        db = MitieDatabase()

        # Try to get rate items from database
        rate_items = {}
        categories = ["power_lighting", "access_lifting", "materials_labour", "subcontractors", "preliminaries"]

        database_available = True
        for category in categories:
            try:
                items = db.get_rate_items_by_category(category, limit=50)
                rate_items[category] = [
                    {
                        "code": item["item_code"],
                        "description": item["description"],
                        "rate": item["rate"],
                        "unit": item["unit_type"]
                    }
                    for item in items
                ]
            except Exception as e:
                print(f"⚠️ Could not load {category}: {e}")
                rate_items[category] = []
                database_available = False

        # Log what we found
        total_items = sum(len(items) for items in rate_items.values())
        print(f"📊 Loaded {total_items} rate items from database")

        # If no rate items loaded, use static fallback
        if total_items == 0:
            print("📋 Using static rate data as fallback...")
            rate_items = _get_static_rate_items()
        
        # Get preferred supplier items
        preferred_items = []
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT description, product_type, specifications, rate, unit_type
                    FROM mitie_preferred_items
                    WHERE is_active = true OR is_active IS NULL
                    ORDER BY product_type, rate
                    LIMIT 100
                """))
                preferred_items = [
                    {
                        "description": row.description,
                        "product_type": row.product_type,
                        "specifications": row.specifications,
                        "rate": float(row.rate),
                        "unit": row.unit_type
                    }
                    for row in result
                ]
                print(f"📦 Loaded {len(preferred_items)} preferred supplier items")
        except Exception as e:
            print(f"⚠️ Could not load preferred items: {e}")
            print("   This is expected if database is not available")
        
        # Get steel tonnage configurations
        steel_configs = []
        try:
            with db.engine.connect() as conn:
                # First check what config_types exist
                check_result = conn.execute(text("SELECT DISTINCT config_type FROM mitie_config"))
                existing_types = [row[0] for row in check_result]
                print(f"🔍 Available config_types: {existing_types}")

                result = conn.execute(text("""
                    SELECT config_key, config_value
                    FROM mitie_config
                    WHERE config_type = 'steel_tonnage'
                    AND (is_active = true OR is_active IS NULL)
                    ORDER BY config_key
                """))
                for row in result:
                    try:
                        # config_value is already a dict when retrieved from JSONB column
                        config_data = row.config_value if isinstance(row.config_value, dict) else json.loads(row.config_value)
                        steel_configs.append({
                            "key": row.config_key,
                            "height": config_data.get("height", ""),
                            "tower_type": config_data.get("tower_type", ""),
                            "tonnage": config_data.get("tonnage", 0),
                            "rate_per_tonne": config_data.get("rate_per_tonne", 1200),
                            "description": config_data.get("description", "")
                        })
                    except Exception as parse_e:
                        print(f"⚠️ Failed to parse steel config {row.config_key}: {parse_e}")
                print(f"🏗️ Loaded {len(steel_configs)} steel configurations")
        except Exception as e:
            print(f"⚠️ Could not load steel configs: {e}")
            print("   This is expected if database is not available")

        # Get regional uplift configurations
        regional_configs = []
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT config_key, config_value
                    FROM mitie_config
                    WHERE config_type = 'regional_uplift'
                    AND (is_active = true OR is_active IS NULL)
                    ORDER BY config_key
                """))
                for row in result:
                    try:
                        # config_value is already a dict when retrieved from JSONB column
                        config_data = row.config_value if isinstance(row.config_value, dict) else json.loads(row.config_value)
                        regional_configs.append({
                            "region": row.config_key,
                            "postcodes": config_data.get("postcodes", []),
                            "uplift_percentage": config_data.get("uplift", 0) * 100,
                            "description": config_data.get("description", "")
                        })
                    except Exception as parse_e:
                        print(f"⚠️ Failed to parse regional config {row.config_key}: {parse_e}")
                print(f"🌍 Loaded {len(regional_configs)} regional configurations")
        except Exception as e:
            print(f"⚠️ Could not load regional configs: {e}")
            print("   This is expected if database is not available")
        
        # Format for LLM context
        context = {
            "available_rate_items": rate_items,
            "available_preferred_supplier_items": preferred_items,
            "available_steel_configurations": steel_configs,
            "available_regional_uplifts": regional_configs,
            "markup_rates": {
                "materials_labour": "20%",
                "subcontractors": "15%",
                "preferred_supplier": "19%"
            },
            "preliminary_bands": {
                "£0-5,000": "£2,258.53",
                "£5,001-10,000": "£2,635.29",
                "£10,001-15,000": "£3,012.05",
                "£15,001-20,000": "£3,776.52",
                "£20,000+": "Proportional (capped at £7,500)"
            },
            "contingency_rates": {
                "standard": "5%",
                "moderate": "10%",
                "critical": "15%"
            }
        }

        # Summary logging
        total_rate_items = sum(len(items) for items in rate_items.values())
        print(f"\n📋 CONTEXT SUMMARY:")
        print(f"   Rate items: {total_rate_items}")
        print(f"   Preferred items: {len(preferred_items)}")
        print(f"   Steel configs: {len(steel_configs)}")
        print(f"   Regional configs: {len(regional_configs)}")
        print(f"   Static configs: markup rates, preliminary bands, contingency rates")

        if total_rate_items == 0 and len(preferred_items) == 0:
            print(f"   ⚠️ No dynamic data loaded - database connection issue")
            print(f"   ✅ Static configuration data is still available for LLM")
        else:
            print(f"   ✅ Full configuration data available for LLM")

        return json.dumps(context, indent=2)
        
    except Exception as e:
        print(f"❌ Error gathering configurations: {e}")
        return json.dumps({
            "error": f"Could not load configurations: {str(e)}",
            "available_rate_items": {},
            "available_preferred_supplier_items": [],
            "available_steel_configurations": [],
            "available_regional_uplifts": []
        })

if __name__ == "__main__":
    # Test the context provider
    context = get_all_available_mitie_configs()
    print("📋 Available Mitie Configurations:")
    print(context)
