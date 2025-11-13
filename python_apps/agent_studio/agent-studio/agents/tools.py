import os
import dotenv
import requests
import markdownify
from bs4 import BeautifulSoup
from utils import function_schema
from typing import Optional, Dict, Any, List
from utils import client
import pickle
import logging
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import re

# Import ServiceNow tools
from tools.servicenow.itsm_tools import (
    servicenow_itsm_create_incident,
    servicenow_itsm_get_incident,
    servicenow_itsm_update_incident
)
from tools.servicenow.csm_tools import (
    servicenow_csm_create_case,
    servicenow_csm_get_case,
    servicenow_csm_update_case
)
# Import Salesforce tools
from tools.salesforce.csm_tools import (
    salesforce_csm_create_case,
    salesforce_csm_get_case,
    salesforce_csm_update_case
)

from tools.servicenow.agent_tools import ServiceNowAgentClient

SEGMENT_NUM = 5

dotenv.load_dotenv(".env.local")

GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")
CX_ID = os.getenv("CX_ID_PERSONAL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

KEVEL_API_KEY = os.getenv("KEVEL_API_KEY")
KEVEL_API_BASE = os.getenv("KEVEL_API_BASE_URL", "https://api.kevel.co/v1")
SERVICENOW_NOW_ASSIST_USER_REFERENCE = os.getenv("SERVICENOW_NOW_ASSIST_USER_REFERENCE")
KEVEL_NETWORK_ID = 11679

EXAMPLE_DATA = [
    {"customer_id": 1111, "order_number": 1720, "location": "New York"},
    {"customer_id": 2222, "order_number": 9, "location": "Los Angeles"},
    {"customer_id": 3333, "order_number": 45, "location": "Chicago"},
    {"customer_id": 4444, "order_number": 100, "location": "Miami"},
    {"customer_id": 5555, "order_number": 200, "location": "San Francisco"},
]


# Mitie RFQ Tools
@function_schema
def extract_rfq_json(rfq_text: str) -> str:
    """
    MITIE RFQ JSON EXTRACTOR

    Extracts structured JSON data from RFQ (Request for Quote) documents.
    Identifies mandatory and optional fields for quote generation.

    Args:
        rfq_text: The RFQ document text content

    Returns:
        str: JSON string containing extracted mandatory and optional fields
    """
    try:
        # Use OpenAI to extract structured data from RFQ text
        extraction_prompt = f"""
Extract structured JSON data from this RFQ document. Return ONLY valid JSON with no additional text.

Required mandatory fields:
- rfq_number: string (unique RFQ identifier)
- client_name: string (client company name)
- project_reference: string (client's internal project reference)
- site_postcode: string (UK postcode)
- project_type: string (e.g., "Rooftop", "Monopole", "Lattice Tower")
- duration_weeks: string (expected project timeline)
- cost_base: string ("Budget" or "Final Account")
- technical_specs: object with "scope" array

Optional fields (include if found):
- region: string
- project_subtype: string
- site_conditions: object
- power_specs: object
- existing_infrastructure: object
- preferred_supplier_items: array
- steel_specs: object
- foundation_specs: object
- subcontractor_requirements: object
- compliance_requirements: object
- risk_factors: object

RFQ Document:
{rfq_text}

Return JSON:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,
            max_tokens=2000
        )

        extracted_json = response.choices[0].message.content.strip()

        # Clean markdown formatting if present
        if extracted_json.startswith('```json'):
            extracted_json = extracted_json[7:]  # Remove ```json
        if extracted_json.startswith('```'):
            extracted_json = extracted_json[3:]   # Remove ```
        if extracted_json.endswith('```'):
            extracted_json = extracted_json[:-3]  # Remove trailing ```
        extracted_json = extracted_json.strip()

        # Validate it's proper JSON
        import json
        parsed_data = json.loads(extracted_json)

        # Validate mandatory fields are present
        mandatory_fields = [
            "rfq_number", "client_name", "project_reference",
            "site_postcode", "project_type", "duration_weeks",
            "cost_base", "technical_specs"
        ]

        missing_fields = [field for field in mandatory_fields if field not in parsed_data or not parsed_data[field]]
        if missing_fields:
            return json.dumps({
                "status": "incomplete",
                "error": f"Missing mandatory fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields,
                "extracted_data": parsed_data,
                "mandatory_fields_complete": False,
                "user_action_required": "Please provide the missing information to continue with quote generation"
            })

        return json.dumps({
            "status": "success",
            "extracted_data": parsed_data,
            "mandatory_fields_complete": True
        })

    except json.JSONDecodeError as e:
        return json.dumps({
            "error": f"Invalid JSON extracted: {str(e)}",
            "raw_response": extracted_json
        })
    except Exception as e:
        return json.dumps({
            "error": f"Extraction failed: {str(e)}"
        })

# Mitie RFQ Extractor ServiceNow Agent
@function_schema
def extract_rfq_from_snow_agent(rfq_text: str) -> str:
    """
    MITIE RFQ JSON EXTRACTOR Using ServiceNow Agent

    Extracts structured JSON data from RFQ (Request for Quote) documents.
    Identifies mandatory and optional fields for quote generation.

    Args:
        rfq_text: The RFQ document text content

    Returns:
        str: JSON string containing extracted mandatory and optional fields
    """
    try:
        import asyncio
        extracted_quote_metadata = asyncio.run(ServiceNowAgentClient().trigger_quote_extraction(rfq_text, SERVICENOW_NOW_ASSIST_USER_REFERENCE))
        return json.dumps(extracted_quote_metadata)
    except Exception as e:
        return json.dumps({
            "error": f"Quote Extraction failed"
        })

    
@function_schema
def calculate_mitie_quote(extracted_data: str) -> str:
    """
    MITIE QUOTE CALCULATOR - LLM-Driven Item Selection with Database Rates

    Uses LLM to intelligently select relevant items from available configurations,
    then applies database-stored rates and business rules for accurate calculations.

    Process:
    1. Load ALL available configurations as context
    2. LLM selects relevant items based on RFQ scope
    3. Apply database rates and business rules
    4. Calculate regional uplifts, markups, preliminaries, contingency

    Features:
    - LLM-driven intelligent item selection
    - Complete rate card context provided
    - Active/Passive project classification
    - Regional uplift calculations
    - Steel tonnage calculations with engineering validation
    - Risk-based contingency (5-15%)
    - Framework account detection and discounts
    - Proper preliminaries banding logic

    Args:
        extracted_data: JSON string containing extracted RFQ data

    Returns:
        str: JSON string containing detailed cost calculations and breakdown
    """
    try:
        import json
        from .mitie_database import MitieDatabase, MitieCalculator, MitieCalculationError

        # Parse the extracted data with better error handling
        try:
            if isinstance(extracted_data, str):
                data = json.loads(extracted_data)
            else:
                data = extracted_data
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Failed to parse extracted_data JSON: {str(e)}",
                "type": "json_parse_error",
                "details": f"Error at position {e.pos if hasattr(e, 'pos') else 'unknown'}"
            })

        # Check if this is an incomplete extraction that needs user input
        if isinstance(data, dict) and data.get("status") == "incomplete":
            return json.dumps({
                "error": "Cannot calculate quote with incomplete RFQ data",
                "type": "incomplete_data_error",
                "missing_fields": data.get("missing_fields", []),
                "user_action_required": data.get("user_action_required", "Please provide missing information")
            })

        # Handle nested structure if data comes from extract_rfq_json
        if "extracted_data" in data:
            rfq_data = data["extracted_data"]
        else:
            rfq_data = data

        # Initialize database connection and calculator
        try:
            print("🔌 Initializing database connection...")
            db = MitieDatabase()
            calculator = MitieCalculator(db)
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return json.dumps({
                "error": f"Database connection failed: {str(e)}",
                "fallback": "Please check database configuration"
            })

        # 🤖 LLM-DRIVEN ITEM SELECTION
        print("🤖 Using LLM to select relevant items from available configurations...")
        try:
            from .mitie_llm_selector import select_relevant_mitie_items
            selected_items = select_relevant_mitie_items(rfq_data)
            print(f"✅ LLM selected {len(selected_items.get('selected_rate_items', []))} rate items")
            print(f"✅ LLM selected {len(selected_items.get('selected_preferred_items', []))} preferred items")

            # Use LLM selections instead of hardcoded logic
            use_llm_selections = True
        except Exception as e:
            print(f"⚠️ LLM selection failed: {e}")
            print("📋 Falling back to hardcoded logic...")
            selected_items = {}
            use_llm_selections = False

        # Validate inputs
        print("🔍 Validating inputs...")
        validation_warnings = calculator.validate_calculation_inputs(rfq_data)
        if validation_warnings:
            print(f"⚠️ Validation warnings: {validation_warnings}")

        # Extract key data
        print("📊 Extracting key data...")
        technical_scope = rfq_data.get("technical_scope", "")
        if not technical_scope:
            # Fallback to technical_specs.scope if available
            tech_specs = rfq_data.get("technical_specs", {})
            if isinstance(tech_specs.get("scope"), list):
                technical_scope = " ".join(tech_specs["scope"])
            else:
                technical_scope = str(tech_specs.get("scope", ""))

        # Also include project_type in technical scope for better classification
        project_type_from_rfq = rfq_data.get("project_type", "")
        if project_type_from_rfq and project_type_from_rfq not in technical_scope:
            technical_scope = f"{project_type_from_rfq} {technical_scope}"

        client_name = rfq_data.get("client_name", "")
        site_postcode = rfq_data.get("site_postcode", "")

        print(f"   Technical scope: {technical_scope[:100]}...")
        print(f"   Client: {client_name}")
        print(f"   Postcode: {site_postcode}")

        # 1. CLASSIFY PROJECT TYPE
        print("\n🏗️ Step 1: Classifying project type...")
        project_type = calculator.classify_project_type(technical_scope)
        print(f"   Project classified as: {project_type}")

        # 2. CHECK FRAMEWORK ACCOUNT STATUS
        print("\n🏢 Step 2: Checking framework account status...")
        is_framework = calculator.is_framework_account(client_name)
        print(f"   Framework account: {is_framework}")

        # 3. GET BASE RATES FROM DATABASE
        print("\n💰 Step 3: Getting base rates from database...")
        base_costs = {}
        line_items = []
        active_components = []
        passive_components = []

        # Define scope_lower for use in both LLM and fallback paths
        scope_lower = technical_scope.lower()

        if use_llm_selections and selected_items:
            print("   🤖 Using LLM-selected items...")

            # Add LLM-selected rate items
            for item in selected_items.get("selected_rate_items", []):
                rate = db.get_rate_item(item["code"])
                if rate:
                    rate_item = {
                        "code": item["code"],
                        "description": item["description"],
                        "rate": rate,
                        "unit": item["unit"],
                        "quantity": item.get("quantity", 1),
                        "total": rate * item.get("quantity", 1),
                        "category": "materials_labour"
                    }
                    line_items.append(rate_item)

                    # Classify as active or passive based on item type
                    if item["code"] in ["11.16", "11.5"]:  # Power/lighting are active
                        active_components.append(rate_item)
                        base_costs[item["code"].replace(".", "_")] = rate_item["total"]
                    else:
                        passive_components.append(rate_item)
                        base_costs[item["code"].replace(".", "_")] = rate_item["total"]

                    print(f"   ✅ Added {item['code']}: {item['description'][:50]}... - £{rate}")
                    print(f"      Justification: {item.get('justification', 'LLM selected')}")
                else:
                    print(f"   ❌ Rate not found for {item['code']}: {item['description']}")

            # Add LLM-selected preferred supplier items (prevent duplicates)
            added_product_types = set()
            for item in selected_items.get("selected_preferred_items", []):
                product_type = item["product_type"]

                # Skip if we already added this product type
                if product_type in added_product_types:
                    print(f"   ⚠️ Skipping duplicate {product_type} item: {item['description']}")
                    continue

                # Search for exact match first, then fallback to general search
                specifications = item.get("specifications", item.get("description", ""))
                preferred_rate = db.get_preferred_supplier_rate(product_type, specifications)

                if preferred_rate:
                    preferred_item = {
                        "code": f"PS_{product_type.upper()}",
                        "description": item["description"],
                        "rate": preferred_rate,
                        "unit": "Nr",
                        "quantity": item.get("quantity", 1),
                        "total": preferred_rate * item.get("quantity", 1),
                        "category": "preferred_supplier"
                    }
                    line_items.append(preferred_item)
                    passive_components.append(preferred_item)
                    base_costs[f"preferred_{product_type.lower()}"] = preferred_item["total"]
                    added_product_types.add(product_type)

                    print(f"   ✅ Added preferred: {item['description']} - £{preferred_rate}")
                    print(f"      Justification: {item.get('justification', 'LLM selected')}")
                else:
                    print(f"   ❌ Preferred supplier rate not found: {product_type} - {specifications}")

        else:
            print("   📋 Using hardcoded keyword matching...")
            # FALLBACK: Original hardcoded logic
            print(f"   Checking scope for keywords...")
            print(f"   Scope (lowercase): {scope_lower}")

            if "power" in scope_lower:
                print("   🔌 Power supply detected in scope")
                power_rate = db.get_rate_item("11.16")
                print(f"   Power rate (11.16): £{power_rate}" if power_rate else "   ❌ Power rate not found")
                if power_rate:
                    power_item = {
                        "code": "11.16",
                        "description": "Provide power supply to new equipment/enclosure",
                        "rate": power_rate,
                        "unit": "Nr",
                        "quantity": 1,
                        "total": power_rate,
                        "category": "materials_labour"
                    }
                    line_items.append(power_item)
                    active_components.append(power_item)
                    base_costs["power"] = power_rate
                    print(f"   ✅ Added power item: £{power_rate}")
            else:
                print("   ⚠️ No 'power' keyword found in scope")

        # Lighting (if in scope)
        if "lighting" in scope_lower:
            print("   💡 Lighting detected in scope")
            lighting_rate = db.get_rate_item("11.5")
            print(f"   Lighting rate (11.5): £{lighting_rate}" if lighting_rate else "   ❌ Lighting rate not found")
            if lighting_rate:
                lighting_item = {
                    "code": "11.5",
                    "description": "Rooftop lighting scheme with LED luminaires",
                    "rate": lighting_rate,
                    "unit": "Nr",
                    "quantity": 1,
                    "total": lighting_rate,
                    "category": "materials_labour"
                }
                line_items.append(lighting_item)
                active_components.append(lighting_item)
                base_costs["lighting"] = lighting_rate
                print(f"   ✅ Added lighting item: £{lighting_rate}")
        else:
            print("   ⚠️ No 'lighting' keyword found in scope")

        # Access & Lifting (if cherry picker required)
        subcontractor_reqs = rfq_data.get("subcontractor_requirements", {})
        if subcontractor_reqs.get("cherry_picker", False) or "cherry picker" in scope_lower or "crane" in scope_lower:
            access_rate = db.get_rate_item("6.01")
            if access_rate:
                access_item = {
                    "code": "6.01",
                    "description": "Cherry picker up to 22m platform height",
                    "rate": access_rate,
                    "unit": "Per Day",
                    "quantity": 2,  # Estimated days
                    "total": access_rate * 2,
                    "category": "subcontractors"
                }
                line_items.append(access_item)
                base_costs["access_lifting"] = access_rate * 2

        # 4. CALCULATE STEEL TONNAGE (if applicable)
        steel_cost_details = {"amount": 0}

        if use_llm_selections and selected_items.get("selected_steel_config"):
            print("   🤖 Using LLM-selected steel configuration...")
            steel_config = selected_items["selected_steel_config"]

            # Calculate steel cost using LLM-selected configuration
            tonnage = steel_config.get("tonnage", 0)
            rate_per_tonne = steel_config.get("rate_per_tonne", 1200)

            if tonnage > 0:
                base_cost = tonnage * rate_per_tonne
                marked_up_cost = base_cost * 1.20  # +20% markup

                steel_item = {
                    "code": "STEEL",
                    "description": f"{steel_config.get('height', '')} {steel_config.get('tower_type', '')} - {tonnage} tonnes",
                    "rate": rate_per_tonne,
                    "unit": "tonne",
                    "quantity": tonnage,
                    "total": marked_up_cost,
                    "category": "materials_labour",
                    "validation_required": True
                }
                line_items.append(steel_item)
                passive_components.append(steel_item)
                base_costs["steel"] = marked_up_cost
                steel_cost_details = {"amount": marked_up_cost}

                print(f"   ✅ Added steel: {steel_config.get('height', '')} {steel_config.get('tower_type', '')} - {tonnage}t × £{rate_per_tonne} = £{marked_up_cost:.2f}")
                print(f"      Justification: {steel_config.get('justification', 'LLM selected')}")

        else:
            # FALLBACK: Original steel calculation logic
            if any(keyword in scope_lower for keyword in ["lattice", "monopole", "tower", "mast"]):
                tower_specs = calculator.extract_tower_specifications(technical_scope)
                if tower_specs["tower_type"] and tower_specs["height"]:
                    steel_cost_details = calculator.calculate_steel_tonnage_cost(tower_specs)
                    if steel_cost_details["amount"] > 0:
                        steel_item = {
                            "code": "STEEL",
                            "description": steel_cost_details["description"],
                            "rate": steel_cost_details["rate_per_tonne"],
                            "unit": "tonne",
                            "quantity": steel_cost_details["tonnage"],
                            "total": steel_cost_details["marked_up_cost"],
                            "category": "materials_labour",
                            "validation_required": True
                        }
                        line_items.append(steel_item)
                        passive_components.append(steel_item)
                        base_costs["steel"] = steel_cost_details["marked_up_cost"]

        # Preferred Supplier Items (Elara, TSC, Lancaster)
        if any(product in scope_lower for product in ["elara", "tsc", "lancaster"]):
            # Try to find matching preferred supplier items
            for product_type in ["Elara", "TSC", "Lancaster"]:
                if product_type.lower() in scope_lower:
                    # Extract specifications (simplified)
                    specs = "12.5m"  # Default, should be extracted from scope
                    preferred_rate = db.get_preferred_supplier_rate(product_type, specs)
                    if preferred_rate:
                        preferred_item = {
                            "code": f"PS_{product_type.upper()}",
                            "description": f"{product_type} {specs} structure",
                            "rate": preferred_rate,
                            "unit": "Nr",
                            "quantity": 1,
                            "total": preferred_rate,
                            "category": "preferred_supplier"
                        }
                        line_items.append(preferred_item)
                        passive_components.append(preferred_item)
                        base_costs[f"preferred_{product_type.lower()}"] = preferred_rate
                    break  # Only add one preferred supplier item

        print(f"\n   📊 Base costs summary: {len(base_costs)} items, Total: £{sum(base_costs.values()):.2f}")
        for category, amount in base_costs.items():
            print(f"      {category}: £{amount:.2f}")

        # 5. APPLY CATEGORY-SPECIFIC MARKUPS (without regional uplift first)
        print(f"\n💼 Step 6: Applying category-specific markups...")
        markup_rates = calculator.get_markup_rates(is_framework)
        print(f"   Markup rates: {markup_rates}")
        marked_up_costs = {}
        markup_details = {}

        for item in line_items:
            category = item["category"]
            base_amount = item["total"]

            # Get appropriate markup rate (no regional uplift here yet)
            if category == "preferred_supplier":
                markup_rate = markup_rates["preferred_supplier"]
            elif category == "subcontractors":
                markup_rate = markup_rates["subcontractors"]
            else:
                markup_rate = markup_rates["materials_labour"]

            markup_amount = base_amount * markup_rate
            final_amount = base_amount + markup_amount

            # Update item with final amounts (no regional uplift yet)
            item["markup_rate"] = markup_rate
            item["markup_amount"] = markup_amount
            item["final_total"] = final_amount

            marked_up_costs[category] = marked_up_costs.get(category, 0) + final_amount
            if category not in markup_details:
                markup_details[category] = {"rate": markup_rate, "amount": 0}
            markup_details[category]["amount"] += markup_amount

        # 7. CALCULATE PRELIMINARIES
        work_subtotal = sum(marked_up_costs.values())
        print(f"\n📋 Step 7: Calculating preliminaries...")
        print(f"   Work subtotal: £{work_subtotal:.2f}")
        print(f"   Project type: {project_type}")
        preliminaries = calculator.calculate_preliminaries(project_type, work_subtotal)
        print(f"   Preliminaries result: {preliminaries['type']} = £{preliminaries['amount']:.2f}")

        # Add preliminaries as line item
        prelim_item = {
            "code": "PRELIM",
            "description": f"Preliminaries - {preliminaries['type']}",
            "rate": preliminaries["amount"],
            "unit": "item",
            "quantity": 1,
            "total": preliminaries["amount"],
            "final_total": preliminaries["amount"],
            "category": "preliminaries"
        }
        line_items.append(prelim_item)

        # 8. CALCULATE SUBTOTAL AFTER MARKUPS + PRELIMS
        subtotal_after_markups = work_subtotal + preliminaries["amount"]
        print(f"\n🧮 Step 8: Calculating subtotal after markups + preliminaries...")
        print(f"   Work subtotal: £{work_subtotal:.2f}")
        print(f"   Preliminaries: £{preliminaries['amount']:.2f}")
        print(f"   Subtotal after markups: £{subtotal_after_markups:.2f}")

        # 8.5. APPLY REGIONAL UPLIFTS (on the subtotal)
        print(f"\n🌍 Step 8.5: Applying regional uplifts...")
        print(f"   Site postcode: {site_postcode}")
        print(f"   Subtotal before regional uplift: £{subtotal_after_markups:.2f}")

        # Calculate regional uplift on the subtotal (not just base costs)
        regional_uplift_base = {"subtotal": subtotal_after_markups}
        regional_uplift = calculator.apply_regional_uplift(site_postcode, regional_uplift_base)
        print(f"   Regional uplift result: {regional_uplift['region']} +{regional_uplift['percentage']:.1f}% = £{regional_uplift['amount']:.2f}")

        # Apply regional uplift to subtotal
        subtotal_after_regional = subtotal_after_markups + regional_uplift["amount"]
        print(f"   Subtotal after regional uplift: £{subtotal_after_regional:.2f}")

        # 9. APPLY RISK-BASED CONTINGENCY
        print(f"\n⚠️ Step 9: Applying risk-based contingency...")

        if use_llm_selections and selected_items.get("risk_assessment"):
            print("   🤖 Using LLM risk assessment...")
            risk_assessment = selected_items["risk_assessment"]
            risk_level = risk_assessment.get("level", "standard")

            # Map risk levels to rates
            risk_rates = {"standard": 0.05, "moderate": 0.10, "critical": 0.15}
            risk_rate = risk_rates.get(risk_level, 0.05)

            contingency_amount = subtotal_after_regional * risk_rate
            contingency = {
                "risk_level": risk_level,
                "rate": risk_rate,
                "calculated_amount": contingency_amount,
                "final_amount": contingency_amount,
                "cap_applied": False,
                "cap_amount": 25000,
                "subtotal_base": subtotal_after_regional
            }

            print(f"   LLM Risk Level: {risk_level} ({risk_rate*100:.0f}%) = £{contingency_amount:.2f}")
            print(f"   Justification: {risk_assessment.get('justification', 'LLM assessed')}")
        else:
            # FALLBACK: Original risk calculation
            risk_factors = rfq_data.get("risk_factors", technical_scope)
            print(f"   Risk factors: {risk_factors[:100]}...")
            contingency = calculator.calculate_risk_contingency(risk_factors, subtotal_after_regional)
            print(f"   Contingency: {contingency['risk_level']} ({contingency['rate']*100:.0f}%) = £{contingency['final_amount']:.2f}")

        # 10. CALCULATE FINAL TOTAL
        final_total = subtotal_after_regional + contingency["final_amount"]
        print(f"\n💰 Step 10: Final total calculation...")
        print(f"   Subtotal after regional uplift: £{subtotal_after_regional:.2f}")
        print(f"   Contingency: £{contingency['final_amount']:.2f}")
        print(f"   FINAL TOTAL: £{final_total:.2f}")

        # 11. BUILD COMPREHENSIVE RESPONSE
        cost_breakdown = {
            "project_info": {
                "rfq_number": rfq_data.get("rfq_number"),
                "client_name": client_name,
                "site_postcode": site_postcode,
                "project_classification": project_type,
                "is_framework_account": is_framework
            },
            "line_items": line_items,
            "active_components": active_components,
            "passive_components": passive_components,
            "base_costs": base_costs,
            "regional_uplift": regional_uplift,
            "markups": markup_details,
            "preliminaries": preliminaries,
            "steel_tonnage": steel_cost_details,
            "subtotal_after_markups": subtotal_after_markups,
            "contingency": contingency,
            "final_total": final_total,
            "validation_warnings": validation_warnings,
            "audit_trail": [
                f"Project classified as: {project_type}",
                f"Regional uplift: {regional_uplift['region']} +{regional_uplift['percentage']:.1f}%",
                f"Preliminaries: {preliminaries['type']} - £{preliminaries['amount']:.2f}",
                f"Contingency: {contingency['risk_level']} risk ({contingency['rate']*100:.0f}%)",
                f"Framework account: {'Yes' if is_framework else 'No'}"
            ]
        }

        # Calculate rule-based risk assessment
        risk_assessment = _calculate_rule_based_risk(
            total_cost=final_total,
            duration_weeks=rfq_data.get("duration_weeks", ""),
            complexity=technical_scope,
            contingency_rate=contingency.get("rate", 0.05)
        )

        # Add steel validation warning if applicable
        if steel_cost_details.get("validation_required"):
            cost_breakdown["audit_trail"].append("⚠️ Steel tonnage estimate requires engineering validation")

        # Add risk assessment to cost breakdown
        cost_breakdown["risk_assessment"] = risk_assessment

        return json.dumps({
            "status": "success",
            "cost_breakdown": cost_breakdown,
            "summary": {
                "total_cost": f"£{final_total:,.2f}",
                "base_cost": f"£{sum(base_costs.values()):,.2f}",
                "regional_uplift": f"£{regional_uplift['amount']:,.2f}",
                "markups": f"£{sum(details['amount'] for details in markup_details.values()):,.2f}",
                "preliminaries": f"£{preliminaries['amount']:,.2f}",
                "contingency": f"£{contingency['final_amount']:,.2f}",
                "risk_category": risk_assessment["category"]
            }
        })

    except MitieCalculationError as e:
        return json.dumps({
            "error": f"Mitie calculation error: {str(e)}",
            "type": "calculation_error"
        })
    except Exception as e:
        return json.dumps({
            "error": f"Quote calculation failed: {str(e)}",
            "type": "system_error"
        })


@function_schema
def generate_mitie_pdf(extracted_data: str, cost_calculations: str) -> str:
    """
    MITIE PDF QUOTE GENERATOR

    Generates a professional PDF quote document using Google Drive template integration.
    Creates a formatted quote with cost breakdown and project details using template variables.

    Args:
        extracted_data: JSON string containing extracted RFQ data
        cost_calculations: JSON string containing cost breakdown

    Returns:
        str: JSON string containing PDF generation result and Google Drive link
    """
    try:
        import json
        import os
        import random
        from datetime import datetime, timedelta
        from typing import Dict, Any

        # Get template ID from environment variables
        MITIE_TEMPLATE_ID = os.getenv("MITIE_TEMPLATE_ID")
        if not MITIE_TEMPLATE_ID:
            return json.dumps({
                "error": "MITIE_TEMPLATE_ID environment variable not set"
            })

        # Parse input data with better error handling
        try:
            if isinstance(extracted_data, str):
                rfq_data = json.loads(extracted_data)
            else:
                rfq_data = extracted_data
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Failed to parse extracted_data JSON: {str(e)}",
                "details": f"Error at position {e.pos}"
            })

        try:
            if isinstance(cost_calculations, str):
                # Debug: Log the length and end of the string
                print(f"🔍 cost_calculations length: {len(cost_calculations)}")
                print(f"🔍 Last 100 chars: {cost_calculations[-100:]}")

                # Clean the JSON string first
                cost_calculations_clean = cost_calculations.strip()

                # Find the last complete JSON object
                brace_count = 0
                last_valid_pos = -1
                for i, char in enumerate(cost_calculations_clean):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i
                            break

                if last_valid_pos != -1:
                    cost_calculations_clean = cost_calculations_clean[:last_valid_pos + 1]
                    print(f"🔍 Cleaned to position {last_valid_pos}, new length: {len(cost_calculations_clean)}")

                cost_data = json.loads(cost_calculations_clean)
            else:
                cost_data = cost_calculations
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"Failed to parse cost_calculations JSON: {str(e)}",
                "details": f"Error at position {e.pos}",
                "length": len(cost_calculations) if isinstance(cost_calculations, str) else "not string",
                "sample_start": cost_calculations[:200] + "..." if isinstance(cost_calculations, str) and len(cost_calculations) > 200 else str(cost_calculations),
                "sample_end": "..." + cost_calculations[-200:] if isinstance(cost_calculations, str) and len(cost_calculations) > 200 else ""
            })

        # Handle nested structure
        if "extracted_data" in rfq_data:
            rfq_info = rfq_data["extracted_data"]
        else:
            rfq_info = rfq_data

        if "cost_breakdown" in cost_data:
            costs = cost_data["cost_breakdown"]
            summary = cost_data.get("summary", {})
        else:
            costs = cost_data
            summary = {}

        # Get Google credentials and services
        creds = _get_google_credentials()
        if not creds:
            return json.dumps({
                "error": "Google credentials not available"
            })

        drive_service = build("drive", "v3", credentials=creds)
        docs_service = build("docs", "v1", credentials=creds)

        # Prepare template variables
        current_date = datetime.now()
        quote_date = current_date.strftime("%d %B %Y")
        validity_date = (current_date + timedelta(days=30)).strftime("%d %B %Y")

        customer_name = rfq_info.get('client_name', 'N/A')
        customer_details = rfq_info.get('project_reference', 'N/A')

        # Build cost tables using proper table structure (like Salesforce approach)
        mitie_cost_table = _build_mitie_cost_table_data(costs)

        # Create document title
        doc_title = f"Mitie Quote - {rfq_info.get('rfq_number', 'Unknown')} - {current_date.strftime('%Y-%m-%d')}"

        # Copy template to create new document
        copy_body = {
            "name": doc_title
        }

        copied_doc = drive_service.files().copy(
            fileId=MITIE_TEMPLATE_ID,
            body=copy_body
        ).execute()

        doc_id = copied_doc.get("id")

        # Prepare template variables for regular text replacements
        template_variables = {
            "Date": quote_date,
            "Customer_Name": customer_name,
            "Customer_Details": customer_details,
            "Quoatation_Validity_Date": validity_date,
            "mitie_cost_table": mitie_cost_table,
            "CR_Source": str(random.randint(10000000, 99999999))
        }

        # Use the same approach as Salesforce insertion order for proper table formatting
        result = _generate_pdf_with_media_plan_table(
            drive_service,
            docs_service,
            MITIE_TEMPLATE_ID,
            None,  # No folder needed since we already copied the doc
            doc_title,
            template_variables,
            existing_doc_id=doc_id  # Pass existing doc_id to avoid re-copying
        )

        # Extract result information
        if isinstance(result, str):
            result_data = json.loads(result)
        else:
            result_data = result

        # Share the document and PDF with iopex.com domain for edit access (without notifications)
        document_id = result_data.get("document_id")
        pdf_file_id = result_data.get("pdf_file_id")

        if document_id:
            try:
                # Share document with iopex.com domain without sending notifications
                permission = {"type": "domain", "role": "writer", "domain": "iopex.com"}
                drive_service.permissions().create(
                    fileId=document_id,
                    body=permission,
                    supportsAllDrives=True,
                    sendNotificationEmail=False
                ).execute()
                print(f"✅ Shared document {document_id} with iopex.com domain (no notifications)")
            except Exception as e:
                print(f"⚠️ Warning: Failed to share document: {str(e)}")

        if pdf_file_id:
            try:
                # Share PDF with iopex.com domain without sending notifications
                permission = {"type": "domain", "role": "writer", "domain": "iopex.com"}
                drive_service.permissions().create(
                    fileId=pdf_file_id,
                    body=permission,
                    supportsAllDrives=True,
                    sendNotificationEmail=False
                ).execute()
                print(f"✅ Shared PDF {pdf_file_id} with iopex.com domain (no notifications)")
            except Exception as e:
                print(f"⚠️ Warning: Failed to share PDF: {str(e)}")

        # Calculate total for summary
        final_total = costs.get("final_total", 0)

        # Get URLs from result
        document_url = result_data.get("document_url")
        pdf_url = result_data.get("pdf_url")
        pdf_link = result_data.get("pdf_link")  # Alternative PDF link
        document_id = result_data.get("document_id")

        # Log the URLs for debugging
        print(f"🔗 MITIE PDF GENERATION COMPLETE:")
        print(f"📄 Document URL: {document_url}")
        print(f"📋 PDF Export URL: {pdf_url}")
        print(f"📎 PDF File Link: {pdf_link}")
        print(f"🆔 Document ID: {document_id}")

        return json.dumps({
            "status": "success",
            "document_id": document_id,
            "document_title": doc_title,
            "document_url": document_url,
            "pdf_url": pdf_url,
            "pdf_link": pdf_link,  # Include both PDF links
            "quote_summary": {
                "rfq_number": rfq_info.get('rfq_number'),
                "total_cost": f"£{final_total:,.2f}",
                "project_type": rfq_info.get('project_type'),
                "duration": rfq_info.get('duration_weeks'),
                "validity_date": validity_date
            }
        })

    except Exception as e:
        return json.dumps({
            "error": f"PDF generation failed: {str(e)}"
        })


def _calculate_rule_based_risk(total_cost: float, duration_weeks: str, complexity: str, contingency_rate: float) -> Dict[str, Any]:
    """
    Calculate rule-based risk assessment based on project parameters.

    Risk Categories:
    - LOW: total_cost ≤ £15,000 AND duration_weeks ≤ 10 AND complexity ∈ {standard_rooftop}; contingency ≤ 5%
    - MODERATE: NOT Cat 3 AND (15,001–40,000 OR 11–15 weeks OR complexity ∈ {monopole, moderate}); contingency ≤ 10%
    - HIGH: total_cost > £40,000 OR duration_weeks > 15 OR complexity ∈ {lattice, complex} OR contingency ≥ 10%

    Args:
        total_cost: Final project cost in GBP
        duration_weeks: Project duration as string (e.g., "8", "12-15")
        complexity: Technical scope description
        contingency_rate: Contingency rate as decimal (e.g., 0.05 for 5%)

    Returns:
        Dictionary with risk assessment details
    """
    # Parse duration weeks
    try:
        if not duration_weeks or duration_weeks.strip() == "":
            duration_numeric = 0  # Default to 0 if not provided
        else:
            # Handle ranges like "12-15" by taking the maximum
            if "-" in duration_weeks:
                duration_parts = duration_weeks.split("-")
                duration_numeric = max(int(part.strip()) for part in duration_parts if part.strip().isdigit())
            else:
                # Extract numeric part from strings like "8 weeks" or "8"
                import re
                numbers = re.findall(r'\d+', duration_weeks)
                duration_numeric = int(numbers[0]) if numbers else 0
    except (ValueError, IndexError):
        duration_numeric = 0

    # Determine complexity level from technical scope
    complexity_lower = complexity.lower()

    # High complexity indicators
    high_complexity_keywords = ["lattice", "complex", "tower", "steelwork", "foundation", "crane"]

    # Standard/low complexity indicators (check these BEFORE moderate to give rooftop priority)
    standard_complexity_keywords = ["rooftop", "standard rooftop", "rooftop equipment", "rooftop enclosure"]

    # Moderate complexity indicators
    moderate_complexity_keywords = ["monopole", "moderate", "upgrade", "installation", "removal"]

    if any(keyword in complexity_lower for keyword in high_complexity_keywords):
        complexity_level = "complex"
    elif any(keyword in complexity_lower for keyword in standard_complexity_keywords):
        complexity_level = "standard_rooftop"
    elif any(keyword in complexity_lower for keyword in moderate_complexity_keywords):
        complexity_level = "moderate"
    else:
        complexity_level = "moderate"  # Default to moderate if unclear

    # Apply risk rules
    contingency_percentage = contingency_rate * 100

    # Category 3 (HIGH) - Check first as it takes precedence
    if (total_cost > 40000 or
        duration_numeric > 15 or
        complexity_level in ["lattice", "complex"] or
        contingency_percentage >= 10):
        category = "HIGH"
        reasons = []
        if total_cost > 40000:
            reasons.append(f"Total cost £{total_cost:,.2f} > £35,000")
        if duration_numeric > 15:
            reasons.append(f"Duration {duration_numeric} weeks > 15 weeks")
        if complexity_level in ["lattice", "complex"]:
            reasons.append(f"High complexity: {complexity_level}")
        if contingency_percentage >= 10:
            reasons.append(f"Contingency {contingency_percentage:.1f}% ≥ 10%")

    # Category 1 (LOW)
    elif (total_cost <= 15000 and
          duration_numeric <= 10 and
          complexity_level == "standard_rooftop" and
          contingency_percentage <= 5):
        category = "LOW"
        reasons = [
            f"Total cost £{total_cost:,.2f} ≤ £15,000",
            f"Duration {duration_numeric} weeks ≤ 10 weeks",
            f"Standard rooftop complexity",
            f"Contingency {contingency_percentage:.1f}% ≤ 5%"
        ]

    # Category 2 (MODERATE) - Everything else
    else:
        category = "MODERATE"
        reasons = []
        if 15001 <= total_cost <= 40000:
            reasons.append(f"Total cost £{total_cost:,.2f} in moderate range (£15,001-£35,000)")
        if 11 <= duration_numeric <= 15:
            reasons.append(f"Duration {duration_numeric} weeks in moderate range (11-15 weeks)")
        if complexity_level in ["monopole", "moderate"]:
            reasons.append(f"Moderate complexity: {complexity_level}")
        if contingency_percentage <= 10:
            reasons.append(f"Contingency {contingency_percentage:.1f}% ≤ 10%")

        # Add fallback reason if no specific reasons identified
        if not reasons:
            reasons.append("Does not meet LOW or HIGH criteria")

    return {
        "category": category,
        "total_cost": total_cost,
        "duration_weeks": duration_numeric,
        "complexity_level": complexity_level,
        "contingency_percentage": contingency_percentage,
        "reasons": reasons,
        "raw_duration_input": duration_weeks
    }


def _build_mitie_cost_table_data(costs: dict) -> Dict[str, Any]:
    """
    Build Mitie cost table data structure for proper Google Docs table insertion.
    Uses the same approach as Salesforce insertion order for consistent formatting.

    Args:
        costs: Cost data dictionary from calculate_mitie_quote

    Returns:
        Dict containing headers and rows for table creation
    """
    # Extract data from cost calculations
    passive_components = costs.get("passive_components", [])
    active_components = costs.get("active_components", [])
    preliminaries = costs.get("preliminaries", {})
    final_total = costs.get("final_total", 0)

    # Debug logging
    print(f"🔍 PDF Debug - passive_components count: {len(passive_components)}")
    print(f"🔍 PDF Debug - active_components count: {len(active_components)}")
    print(f"🔍 PDF Debug - final_total: {final_total}")
    if passive_components:
        print(f"🔍 PDF Debug - first passive component: {passive_components[0]}")
    if active_components:
        print(f"🔍 PDF Debug - first active component: {active_components[0]}")

    # Build table rows
    table_rows = []

    # Add passive components section header
    table_rows.append(["PASSIVE COSTS", " "])

    # Add preliminaries first
    prelim_amount = preliminaries.get("amount", 0)
    if prelim_amount > 0:
        table_rows.append(["PRELIMINARIES", f"£{prelim_amount:,.2f}"])

    # Add passive components
    for component in passive_components:
        desc = component.get("description", "PASSIVE COMPONENT").upper()
        amount = component.get("final_total", component.get("total", 0))
        table_rows.append([desc, f"£{amount:,.2f}"])

    # Add standard passive categories with zero values if not present
    standard_passive_categories = [
        "SITE REMOVALS / DEMOLITIONS & ALTERATIONS",
        "FOUNDATIONS",
        "TRENCHES & DUCTWORK",
        "COMPOUNDS, FENCING and GATES",
        "ACCESS & LIFTING",
        "STRUCTURES & ENCLOSURES/CABINETS",
        "ROOF-MOUNTED STEEL FRAMES INCLUDING POLES & ANCILLARY ITEMS",
        "MISCELLANEOUS SITE CONSTRUCTION ITEMS",
        "CABLE MANAGEMENT",
        "POWER",
        "LIGHTNING PROTECTION",
        "MARK UP ON PREFERRED SUPPLIER ITEMS",
        "NON-SCHEDULED WORKS",
        "PREFERRED SUPPLIER ITEMS - STRUCTURE COSTS (INCLUDING APP)",
        "PREFERRED SUPPLIER ITEMS - ENCLOSURE COSTS (INCLUDING APP)"
    ]

    # Add missing categories with zero values
    existing_descriptions = [row[0] for row in table_rows if len(row) > 1]
    for category in standard_passive_categories:
        if not any(category in desc for desc in existing_descriptions):
            table_rows.append([category, "£0.00"])

    # Calculate passive total
    passive_total = sum(
        float(row[1].replace('£', '').replace(',', ''))
        for row in table_rows[1:]
        if len(row) > 1 and row[1] not in ["", " "] and row[1].startswith('£')
    )
    table_rows.append(["Passive Total", f"£{passive_total:,.2f}"])

    # Add active components section header
    table_rows.append(["ACTIVE COSTS", " "])

    # Add active components
    for component in active_components:
        desc = component.get("description", "ACTIVE COMPONENT").upper()
        amount = component.get("final_total", component.get("total", 0))
        table_rows.append([desc, f"£{amount:,.2f}"])

    # Add standard active categories with zero values if not present
    standard_active_categories = [
        "PRELIMINARIES",
        "FEEDER CABLES & ANCILLARIES",
        "MARK UP ON PREFERRED SUPPLIER ITEMS",
        "NON-SCHEDULED WORKS",
        "PREFERRED SUPPLIER ITEMS (INCLUDING APP ITEMS)"
    ]

    # Add missing active categories with zero values
    active_existing = [row[0] for row in table_rows if "ACTIVE" in str(row)]
    for category in standard_active_categories:
        if not any(category in desc for desc in active_existing):
            table_rows.append([category, "£0.00"])

    # Calculate active total
    active_start_idx = next(i for i, row in enumerate(table_rows) if row[0] == "ACTIVE COSTS") + 1
    active_total = sum(
        float(row[1].replace('£', '').replace(',', ''))
        for row in table_rows[active_start_idx:]
        if len(row) > 1 and row[1] != " " and row[0] != ""
    )
    table_rows.append(["Active Total", f"£{active_total:,.2f}"])

    # Add subtotal before regional uplift (work + preliminaries)
    subtotal_before_regional = costs.get("subtotal_after_markups", 0)
    if subtotal_before_regional > 0:
        table_rows.append(["SUBTOTAL (Before Regional Uplift)", f"£{subtotal_before_regional:,.2f}"])

    # Always add regional uplift line (even if 0%)
    regional_uplift = costs.get("regional_uplift", {})
    regional_amount = regional_uplift.get("amount", 0)
    region_name = regional_uplift.get("region", "Standard")
    percentage = regional_uplift.get("percentage", 0)

    if percentage > 0:
        table_rows.append([f"REGIONAL UPLIFT ({region_name}) +{percentage:.0f}%", f"£{regional_amount:,.2f}"])
    else:
        table_rows.append([f"REGIONAL UPLIFT ({region_name}) {percentage:.0f}%", f"£{regional_amount:,.2f}"])

    # Add subtotal after regional uplift
    subtotal_after_regional = subtotal_before_regional + regional_amount
    table_rows.append(["SUBTOTAL (After Regional Uplift)", f"£{subtotal_after_regional:,.2f}"])

    # Add contingency if present (markups are already included in subtotal)
    contingency = costs.get("contingency", {})
    contingency_amount = contingency.get("final_amount", contingency.get("calculated_amount", 0))
    if contingency_amount > 0:
        risk_level = contingency.get("risk_level", "standard")
        rate = contingency.get("rate", 0)
        table_rows.append([f"CONTINGENCY ({risk_level.title()} Risk {rate*100:.0f}%)", f"£{contingency_amount:,.2f}"])

    # Add final total
    table_rows.append(["TOTAL SITE COST", f"£{final_total:,.2f}"])

    return {
        "headers": ["Description", "Budget TEF Total"],  # Put back headers
        "rows": table_rows
    }


def _build_cost_table_from_data(table_title: str, costs: dict, component_type: str) -> str:
    """
    Build cost table content using actual calculated data.
    Creates formatted cost breakdown tables for passive and active components.

    Args:
        table_title: Title for the cost table section
        costs: Cost data dictionary from calculate_mitie_quote
        component_type: Type of components (passive/active)

    Returns:
        str: Formatted table content with actual calculated values
    """
    if component_type.lower() == "passive":
        return _build_passive_costs_from_data(costs)
    elif component_type.lower() == "active":
        return _build_active_costs_from_data(costs)
    else:
        return f"{table_title}: No data available"


def _build_passive_costs_from_data(costs: dict) -> str:
    """Build the passive costs table using actual calculated data."""

    # Extract data from our calculation results
    passive_components = costs.get("passive_components", [])
    preliminaries = costs.get("preliminaries", {})

    # Build passive cost items from actual data
    passive_items = []

    # Add preliminaries first
    prelim_amount = preliminaries.get("amount", 0)
    if prelim_amount > 0:
        passive_items.append(("PRELIMINARIES", prelim_amount))

    # Add passive components (these should already have final_total calculated)
    for component in passive_components:
        desc = component.get("description", "PASSIVE COMPONENT").upper()
        amount = component.get("final_total", component.get("total", 0))
        if amount > 0:
            passive_items.append((desc, amount))

    # Add standard categories with zero values if not present
    standard_categories = [
        "SITE REMOVALS / DEMOLITIONS & ALTERATIONS",
        "FOUNDATIONS",
        "TRENCHES & DUCTWORK",
        "COMPOUNDS, FENCING and GATES",
        "ACCESS & LIFTING",
        "STRUCTURES & ENCLOSURES/CABINETS",
        "ROOF-MOUNTED STEEL FRAMES INCLUDING POLES & ANCILLARY ITEMS",
        "MISCELLANEOUS SITE CONSTRUCTION ITEMS",
        "CABLE MANAGEMENT",
        "LIGHTNING PROTECTION",
        "MARK UP ON PREFERRED SUPPLIER ITEMS",
        "NON-SCHEDULED WORKS",
        "PREFERRED SUPPLIER ITEMS - STRUCTURE COSTS (INCLUDING APP)",
        "PREFERRED SUPPLIER ITEMS - ENCLOSURE COSTS (INCLUDING APP)"
    ]

    # Add missing categories with zero values (but avoid duplicates)
    existing_descriptions = [item[0] for item in passive_items]
    for category in standard_categories:
        if not any(category in desc for desc in existing_descriptions):
            passive_items.append((category, 0.00))

    # Calculate total
    passive_total = sum(amount for _, amount in passive_items)

    # Build table content
    table_content = "Passive Costs\n\n"
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"

    # Add each item in table format
    for description, amount in passive_items:
        padded_desc = description.ljust(60)
        table_content += f"{padded_desc}\t£{amount:,.2f}\n"

    # Add total row
    table_content += "=" * 80 + "\n"
    table_content += f"{'Passive Total'.ljust(60)}\t£{passive_total:,.2f}\n"

    return table_content


def _build_active_costs_from_data(costs: dict) -> str:
    """Build the active costs table using actual calculated data."""

    # Extract data from our calculation results
    active_components = costs.get("active_components", [])

    # Build active cost items from actual data
    active_items = []

    # Add active components (these should already have final_total calculated)
    for component in active_components:
        desc = component.get("description", "ACTIVE COMPONENT").upper()
        amount = component.get("final_total", component.get("total", 0))
        if amount > 0:
            active_items.append((desc, amount))

    # Add standard active categories with zero values if not present
    standard_active_categories = [
        "PRELIMINARIES",
        "FEEDER CABLES & ANCILLARIES",
        "MARK UP ON PREFERRED SUPPLIER ITEMS",
        "NON-SCHEDULED WORKS",
        "PREFERRED SUPPLIER ITEMS (INCLUDING APP ITEMS)"
    ]

    # Add missing categories with zero values
    existing_descriptions = [item[0] for item in active_items]
    for category in standard_active_categories:
        if not any(category in desc for desc in existing_descriptions):
            active_items.append((category, 0.00))

    # Calculate total
    active_total = sum(amount for _, amount in active_items)

    # Build table content
    table_content = "Active Costs\n\n"
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"

    # Add each item in table format
    for description, amount in active_items:
        padded_desc = description.ljust(60)
        table_content += f"{padded_desc}\t£{amount:,.2f}\n"

    # Add total row
    table_content += "=" * 80 + "\n"
    table_content += f"{'Active Total'.ljust(60)}\t£{active_total:,.2f}\n"

    return table_content


def _build_total_cost_section_from_data(costs: dict) -> str:
    """Build the total site cost section using actual calculated data."""

    # Get the final total from our calculations
    final_total = costs.get("final_total", 0)

    # Build total cost section
    table_content = "\n\nTotal Site Cost\n\n"
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"
    table_content += f"{'Total Site Cost'.ljust(60)}\t£{final_total:,.2f}\n"

    return table_content


def _build_cost_table(table_title: str, costs: dict, component_type: str) -> str:
    """
    Build cost table content for template replacement.
    Creates formatted cost breakdown tables for passive and active components.

    Args:
        table_title: Title for the cost table section
        costs: Cost data dictionary
        component_type: Type of components (passive/active)

    Returns:
        str: Formatted table content matching the required structure
    """
    # For now, using placeholder data structure - will be updated when calc function provides proper data
    if component_type.lower() == "passive":
        return _build_passive_costs_table()
    elif component_type.lower() == "active":
        return _build_active_costs_table()
    else:
        return f"{table_title}: No data available"


def _build_passive_costs_table() -> str:
    """Build the passive costs table with proper table formatting."""
    # Passive cost items (placeholder data - will be replaced with actual calc data)
    passive_items = [
        ("PRELIMINARIES", 9289.99),
        ("SITE REMOVALS / DEMOLITIONS & ALTERATIONS", 4878.12),
        ("FOUNDATIONS", 0.00),
        ("TRENCHES & DUCTWORK", 0.00),
        ("COMPOUNDS, FENCING and GATES", 0.00),
        ("ACCESS & LIFTING", 5580.00),
        ("STRUCTURES & ENCLOSURES/CABINETS", 2336.45),
        ("ROOF-MOUNTED STEEL FRAMES INCLUDING POLES & ANCILLARY ITEMS", 0.00),
        ("MISCELLANEOUS SITE CONSTRUCTION ITEMS", 0.00),
        ("CABLE MANAGEMENT", 0.00),
        ("POWER", 351.00),
        ("LIGHTNING PROTECTION", 420.93),
        ("MARK UP ON PREFERRED SUPPLIER ITEMS", 0.00),
        ("NON-SCHEDULED WORKS", 501.18),
        ("PREFERRED SUPPLIER ITEMS - STRUCTURE COSTS (INCLUDING APP)", 0.00),
        ("PREFERRED SUPPLIER ITEMS - ENCLOSURE COSTS (INCLUDING APP)", 0.00)
    ]

    # Calculate total
    passive_total = sum(amount for _, amount in passive_items)

    # Build table content
    table_content = "Passive Costs\n\n"

    # Create table header
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"

    # Add each item in table format
    for description, amount in passive_items:
        # Pad description to align values
        padded_desc = description.ljust(60)
        table_content += f"{padded_desc}\t£{amount:,.2f}\n"

    # Add total row
    table_content += "=" * 80 + "\n"
    table_content += f"{'Passive Total'.ljust(60)}\t£{passive_total:,.2f}\n"

    return table_content


def _build_active_costs_table() -> str:
    """Build the active costs table with proper table formatting."""
    # Active cost items (placeholder data - will be replaced with actual calc data)
    active_items = [
        ("PRELIMINARIES", 13704.28),
        ("FEEDER CABLES & ANCILLARIES", 20015.75),
        ("MARK UP ON PREFERRED SUPPLIER ITEMS", 0.00),
        ("NON-SCHEDULED WORKS", 2455.57),
        ("PREFERRED SUPPLIER ITEMS (INCLUDING APP ITEMS)", 0.00)
    ]

    # Calculate total
    active_total = sum(amount for _, amount in active_items)

    # Build table content
    table_content = "Active Costs\n\n"

    # Create table header
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"

    # Add each item in table format
    for description, amount in active_items:
        # Pad description to align values
        padded_desc = description.ljust(60)
        table_content += f"{padded_desc}\t£{amount:,.2f}\n"

    # Add total row
    table_content += "=" * 80 + "\n"
    table_content += f"{'Active Total'.ljust(60)}\t£{active_total:,.2f}\n"

    return table_content


def _calculate_total_site_cost() -> float:
    """Calculate the total site cost (placeholder implementation)."""
    # Placeholder calculation - will be updated when calc function provides proper data
    passive_total = 23357.67  # Sum of all passive costs
    active_total = 36175.61   # Sum of all active costs
    return passive_total + active_total


def _build_total_cost_section() -> str:
    """Build the total site cost section with proper table formatting."""
    total_cost = _calculate_total_site_cost()

    table_content = "\n\nTotal Site Cost\n\n"
    table_content += "Description\t\t\t\t\t\tBudget TEF Total\n"
    table_content += "=" * 80 + "\n"
    table_content += f"{'Total Site Cost'.ljust(60)}\t£{total_cost:,.2f}\n"

    return table_content


@function_schema
def add_numbers(a: int, b: int) -> str:
    """
    Adds two numbers and returns the sum.
    """
    return f"The sum of {a} and {b} is {a + b}"


@function_schema
def get_customer_order(customer_id: int) -> str:
    """ "
    Returns the order number for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        order_number = [
            i["order_number"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id
        ][0]
        return f"The order number for customer ID {customer_id} is {order_number}"
    return f"No order found for customer ID {customer_id}"


@function_schema
def get_customer_location(customer_id: int) -> str:
    """ "
    Returns the location for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        location = [
            i["location"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id
        ][0]
        return f"The location for customer ID {customer_id} is {location}"
    return f"No location found for customer ID {customer_id}"


@function_schema
def add_customer(customer_id: int, order_number: int, location: str) -> str:
    """ "
    Adds a new customer to the database."""
    EXAMPLE_DATA.append(
        {"customer_id": customer_id, "order_number": order_number, "location": location}
    )
    return f"Customer ID {customer_id} added successfully."


@function_schema
def weather_forecast(location: str) -> str:
    """ "
    Returns the weather forecast for a given location. Only give one city at a time.
    """
    url = f"http://api.weatherstack.com/current?access_key={WEATHER_API_KEY}&query={location}"
    response = requests.get(url)

    if response.status_code != 200:
        return f"Error: Can't fetch weather data for {location}"
    else:
        data = response.json()
        return str(data)


@function_schema
def url_to_markdown(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("body")

        if content:
            markdown_content = markdownify.markdownify(
                str(content), heading_style="ATX"
            )
            return markdown_content[:20000]
        else:
            return "No content found in the webpage body."

    except requests.RequestException as e:
        return f"Error fetching URL: {e}"


@function_schema
def web_search(query: str, num: Optional[int] = 2) -> str:
    """
    You can use this tool to get any information from the web. Just type in your query and get the results.
    """
    num = 1
    # try:
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API}&cx={CX_ID}&num={num}"
    response = requests.get(url)
    print(response)
    urls = [i["link"] for i in response.json()["items"]]
    print(urls)
    text = "\n".join([url_to_markdown(i) for i in urls])
    # print(text)
    prompt = f"Use the following text to answer the given: {query} \n\n ---BEGIN WEB TEXT --- {text} ---BEGIN WEB TEXT --- "
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You're a web search agent."},
            {"role": "user", "content": prompt},
        ],
    )
    if response.choices[0].message.content is not None:
        return response.choices[0].message.content
    return ""


@function_schema
def print_to_console(text: str) -> str:
    """ "
    Prints the given text to the console.
    """
    print(text)
    return f"Printed {text} to the console."


@function_schema
def query_retriever2(query: str) -> list:
    """ "
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: "AC01548000"
    Example: "4348"
    Example: "What is TAL"
    Example: "assembly name for part number 3AC01548000"
    Example: "TAL parts list"
    """
    RETRIEVER_URL = os.getenv("RETRIEVER_URL")
    if RETRIEVER_URL is None:
        raise ValueError(
            "RETRIEVER_URL not found. Please set it in the environment variables."
        )
    url = RETRIEVER_URL + "/query-chunks"
    params = {"query": query, "top_k": 60}

    # Make the POST request
    response = requests.post(url, params=params)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    sources = []
    segments = response.json()["selected_segments"][:4]
    for i, segment in enumerate(segments):
        res += "*" * 5 + f"\n\nSegment {i}" + "\n" + "Contextual Header: "
        contextual_header = segment["chunks"][0].get("contextual_header", "")
        skip_length = len(contextual_header) if contextual_header else 0
        res += (
            contextual_header
            if contextual_header
            else "No contextual header" + "\n" + "Context: " + "\n"
        )
        # print(segment["score"])
        print("Segment Done")
        references = ""
        for j, chunk in enumerate(segment["chunks"]):
            # res += f"Contextual Header: {chunk['contextual_header']}\n"
            res += chunk["chunk_text"][skip_length:]
            references += f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n"
            sources.append(f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n")
            # res += "\n"
        res += f"References: {references}"
    res += "\n\n" + "-" * 5 + "\n\n"
    print(res)
    return [res, sources]


@function_schema
def media_context_retriever(
    query: str,
    collection_name: str = "media_data_standardized_v2",
    limit: Optional[int] = 10,
    filter_params: Optional[str] = None,
) -> str:
    """
    MEDIA CONTEXT RETRIEVER TOOL

    Use this tool to retrieve relevant media campaign context and data using semantic search.
    Searches through historical media campaigns, creatives, and performance data to find similar contexts.

    Args:
        query: The search query text for finding relevant media context
        collection_name: Name of the media data collection to search (default: 'media_data_standardized_v2')
        limit: Maximum number of results to return (default: 10)
        filter_params: Optional JSON string with filter parameters (e.g., '{"brand": "nike", "industry": "Fashion & Retail"}')

    EXAMPLES:
    Example: media_context_retriever("high performing fashion campaigns")
    Example: media_context_retriever("summer beverage ads", "media_data_standardized_v2", 10, '{"season": "summer", "industry": "Food & Beverage"}')
    Example: media_context_retriever("Nike campaigns with high CTR", "media_data_standardized_v2", 8, '{"brand": "nike"}')
    """

    try:
        from qdrant_client import QdrantClient

        # Get environment variables
        QDRANT_HOST = os.getenv("QDRANT_HOST", "http://3.101.65.253")
        QDRANT_PORT = os.getenv("QDRANT_PORT", "5333")
        COLLECTION_NAME = os.getenv("COLLECTION_NAME", "media_data_standardized_v2")

        # Use provided collection_name or default
        collection = collection_name or COLLECTION_NAME

        # Initialize Qdrant client
        qdrant_url = f"{QDRANT_HOST}:{QDRANT_PORT}"
        qdrant_client = QdrantClient(url=qdrant_url)

        # Get embedding for query using OpenAI
        embedding_response = client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_vector = embedding_response.data[0].embedding

        # Parse filter parameters - temporarily disabled due to Qdrant compatibility issues
        # filter_dict = None
        # if filter_params:
        #     try:
        #         filter_dict = json.loads(filter_params)
        #     except json.JSONDecodeError:
        #         print(f"Warning: Invalid filter_params JSON: {filter_params}")

        # Perform search without filters for now
        search_results = qdrant_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            # query_filter=filter_dict,  # Temporarily disabled
            with_payload=True,
        )

        # Format results
        if search_results is None or not search_results:
            return f"No results found for query: '{query}' in collection '{collection}'"

        result_text = (
            f"QDRANT SEARCH RESULTS for '{query}' (Collection: {collection}):\n\n"
        )
        for i, result in enumerate(search_results):
            payload = result.payload
            score = result.score

            # Handle case where payload might be None
            if payload is None:
                result_text += f"Result {i+1} (Score: {round(score, 3)}):\n"
                result_text += "No payload data available\n"
                result_text += "-" * 50 + "\n"
                continue

            result_text += f"Result {i+1} (Score: {round(score, 3)}):\n"

            # Use correct field names based on AdCreative model
            result_text += f"Campaign Folder: {payload.get('campaign_folder', 'Unknown Campaign')}\n"
            result_text += f"File Name: {payload.get('file_name', 'Unknown File')}\n"
            result_text += f"Brand: {payload.get('brand', 'Unknown Brand')}\n"
            result_text += f"Industry: {payload.get('industry', 'Unknown Industry')}\n"
            result_text += f"File Type: {payload.get('file_type', 'Unknown')}\n"
            result_text += f"Duration: {payload.get('duration(days)', 0)} days\n"
            result_text += (
                f"Duration Category: {payload.get('duration_category', 'Unknown')}\n"
            )
            result_text += (
                f"Season/Holiday: {payload.get('season_holiday', 'Unknown')}\n"
            )
            result_text += f"Ad Objective: {payload.get('ad_objective', 'Unknown')}\n"
            result_text += f"Targeting: {payload.get('targeting', 'Unknown')}\n"
            result_text += f"Tone/Mood: {payload.get('tone_mood', 'Unknown')}\n"

            # Performance metrics
            booked_impressions = payload.get("booked_measure_impressions", 0)
            delivered_impressions = payload.get("delivered_measure_impressions", 0)
            clicks = payload.get("clicks", 0)
            conversion = payload.get("conversion", 0)

            # Calculate budget as 0.05 * booked_impressions
            budget = 0.05 * booked_impressions if booked_impressions else 0

            result_text += f"Booked Impressions: {booked_impressions:,}\n"
            result_text += f"Delivered Impressions: {delivered_impressions:,}\n"
            result_text += f"Clicks: {clicks:,}\n"
            result_text += f"Conversion: {conversion}\n"
            result_text += f"Budget: ${budget:,.2f}\n"

            # Calculate CTR if we have the data
            if delivered_impressions > 0 and clicks > 0:
                ctr = (clicks / delivered_impressions) * 100
                result_text += f"CTR: {ctr:.2f}%\n"
            else:
                result_text += f"CTR: N/A\n"

            result_text += "-" * 50 + "\n"

        return result_text

    except Exception as e:
        print(f"Qdrant search error: {e}")
        import traceback

        traceback.print_exc()
        # Fallback to mock data for development
        mock_results = [
            {
                "campaign_name": "Nike Summer Collection 2024",
                "brand": "Nike",
                "industry": "Fashion & Retail",
                "budget": 45000,
                "duration": 30,
                "ctr": 2.1,
                "conversion_rate": 1.8,
                "impressions": 850000,
                "score": 0.95,
            },
            {
                "campaign_name": "Adidas Athletic Wear Campaign",
                "brand": "Adidas",
                "industry": "Fashion & Retail",
                "budget": 38000,
                "duration": 25,
                "ctr": 1.9,
                "conversion_rate": 1.6,
                "impressions": 720000,
                "score": 0.87,
            },
        ]

        result_text = (
            f"QDRANT SEARCH RESULTS for '{query}' (MOCK DATA - Connection Error):\n\n"
        )
        for i, result in enumerate(mock_results[:limit]):
            result_text += f"Result {i+1} (Score: {result['score']}):\n"
            result_text += f"Campaign: {result['campaign_name']}\n"
            result_text += f"Brand: {result['brand']}\n"
            result_text += f"Industry: {result['industry']}\n"
            result_text += f"Budget: ${result['budget']:,}\n"
            result_text += f"Duration: {result['duration']} days\n"
            result_text += f"CTR: {result['ctr']}%\n"
            result_text += f"Conversion Rate: {result['conversion_rate']}%\n"
            result_text += f"Impressions: {result['impressions']:,}\n"
            result_text += "-" * 50 + "\n"

        return result_text


@function_schema
def redis_cache_operation(
    operation: str, key: str, value: Optional[str] = None, ttl: Optional[int] = None
) -> str:
    """
    REDIS CACHE TOOL

    Use this tool to perform Redis cache operations for storing and retrieving data.

    Args:
        operation: The Redis operation to perform ('get', 'set', 'delete', 'exists', 'keys')
        key: The Redis key to operate on
        value: The value to set (required for 'set' operation)
        ttl: Time to live in seconds for 'set' operation (optional)

    EXAMPLES:
    Example: redis_cache_operation("set", "campaign:nike:performance", '{"ctr": 0.045, "clicks": 15420}', 3600)
    Example: redis_cache_operation("get", "campaign:nike:performance")
    Example: redis_cache_operation("delete", "campaign:nike:performance")
    Example: redis_cache_operation("keys", "campaign:*")
    Example: redis_cache_operation("exists", "user:session:12345")
    """
    # Mock implementation - in real scenario this would connect to Redis
    print(f"Redis operation: {operation} on key: {key}")

    if operation == "set":
        if value is None:
            return "Error: Value is required for SET operation"
        ttl_info = f" with TTL {ttl}s" if ttl else ""
        print(f"Setting key '{key}' = '{value}'{ttl_info}")
        return f"Successfully set key '{key}' in Redis{ttl_info}"

    elif operation == "get":
        # Mock cached data
        mock_cache = {
            "campaign:nike:performance": '{"ctr": 0.045, "clicks": 15420, "impressions": 342000}',
            "campaign:cocacola:metrics": '{"ctr": 0.038, "clicks": 12800, "impressions": 337000}',
            "user:session:12345": '{"user_id": 12345, "login_time": "2024-01-15T10:30:00Z"}',
            "targeting:config:tech_professionals": '{"age_range": ["25-44"], "interests": ["Technology"]}',
        }

        if key in mock_cache:
            return f"Retrieved from Redis - Key: '{key}', Value: {mock_cache[key]}"
        else:
            return f"Key '{key}' not found in Redis cache"

    elif operation == "delete":
        print(f"Deleting key '{key}' from Redis")
        return f"Successfully deleted key '{key}' from Redis"

    elif operation == "exists":
        # Mock existence check
        existing_keys = [
            "campaign:nike:performance",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]
        exists = key in existing_keys
        return f"Key '{key}' {'exists' if exists else 'does not exist'} in Redis"

    elif operation == "keys":
        # Mock pattern matching
        mock_keys = [
            "campaign:nike:performance",
            "campaign:cocacola:metrics",
            "campaign:disney:analytics",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]

        if "*" in key:
            pattern = key.replace("*", "")
            matching_keys = [k for k in mock_keys if k.startswith(pattern)]
            return f"Keys matching pattern '{key}': {matching_keys}"
        else:
            return f"Exact key search: {[key] if key in mock_keys else []}"

    else:
        return f"Error: Unsupported Redis operation '{operation}'. Supported: get, set, delete, exists, keys"


@function_schema
def postgres_query(
    query_type: str,
    table: str,
    conditions: Optional[str] = None,
    data: Optional[str] = None,
    limit: Optional[int] = 10,
) -> str:
    """
    POSTGRES DATABASE TOOL

    Use this tool to perform PostgreSQL database operations for campaign and user data.

    Args:
        query_type: Type of SQL operation ('select', 'insert', 'update', 'delete', 'count')
        table: Database table name (e.g., 'campaigns', 'users', 'targeting_configs', 'performance_metrics')
        conditions: WHERE clause conditions (e.g., 'brand = "nike" AND season = "summer"')
        data: JSON string with data for insert/update operations
        limit: Maximum number of results for select queries (default: 10)

    EXAMPLES:
    Example: postgres_query("select", "campaigns", "brand = 'nike' AND conversion_rate > 0.04", limit=5)
    Example: postgres_query("insert", "campaigns", data='{"name": "Summer Campaign", "brand": "nike", "budget": 25000}')
    Example: postgres_query("update", "campaigns", "id = 123", '{"status": "completed", "end_date": "2024-01-15"}')
    Example: postgres_query("count", "campaigns", "industry = 'Fashion & Retail'")
    Example: postgres_query("delete", "campaigns", "id = 456")
    """
    # Mock implementation - in real scenario this would connect to PostgreSQL
    print(f"PostgreSQL {query_type.upper()} operation on table '{table}'")
    if conditions:
        print(f"Conditions: {conditions}")
    if data:
        print(f"Data: {data}")

    # Mock database tables and data
    mock_campaigns = [
        {
            "id": 1,
            "name": "Summer Fashion 2024",
            "brand": "nike",
            "industry": "Fashion & Retail",
            "conversion_rate": 0.045,
            "budget": 25000,
            "status": "active",
        },
        {
            "id": 2,
            "name": "Holiday Beverages",
            "brand": "coca-cola",
            "industry": "Food & Beverage",
            "conversion_rate": 0.038,
            "budget": 18000,
            "status": "completed",
        },
        {
            "id": 3,
            "name": "Tech Innovation",
            "brand": "apple",
            "industry": "Technology & Telecommunications",
            "conversion_rate": 0.052,
            "budget": 35000,
            "status": "active",
        },
        {
            "id": 4,
            "name": "Automotive Excellence",
            "brand": "toyota",
            "industry": "Automotive",
            "conversion_rate": 0.041,
            "budget": 22000,
            "status": "paused",
        },
    ]

    mock_users = [
        {
            "id": 101,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "campaign_manager",
            "created_at": "2024-01-10",
        },
        {
            "id": 102,
            "username": "jane_smith",
            "email": "jane@example.com",
            "role": "analyst",
            "created_at": "2024-01-12",
        },
    ]

    if query_type == "select":
        if table == "campaigns":
            results = mock_campaigns[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Name: {row['name']}, Brand: {row['brand']}, CTR: {row['conversion_rate']}, Budget: ${row['budget']}\n"
            return result_text
        elif table == "users":
            results = mock_users[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Username: {row['username']}, Email: {row['email']}, Role: {row['role']}\n"
            return result_text
        else:
            return f"Mock data not available for table '{table}'"

    elif query_type == "insert":
        return (
            f"Successfully inserted new record into '{table}' table with data: {data}"
        )

    elif query_type == "update":
        return f"Successfully updated records in '{table}' table where {conditions} with data: {data}"

    elif query_type == "delete":
        return f"Successfully deleted records from '{table}' table where {conditions}"

    elif query_type == "count":
        if table == "campaigns":
            count = len(mock_campaigns)
        elif table == "users":
            count = len(mock_users)
        else:
            count = 0
        return f"COUNT result for '{table}' table: {count} records"

    else:
        return f"Error: Unsupported query type '{query_type}'. Supported: select, insert, update, delete, count"


@function_schema
def image_generation(
    prompt: str,
    operation_type: str,
    dimensions: Optional[str] = "1024x1024",
    reference_image_url: Optional[str] = None,
    aspect_ratio: Optional[str] = "1:1",
    count: Optional[int] = 1,
    iab_size: Optional[str] = None,
) -> str:
    """
    IMAGE GENERATION TOOL

    Use this tool to generate, resize, or manipulate images for marketing campaigns and creative content.

    Args:
        prompt: Text description for image generation or operation details
        operation_type: Type of operation ('generate', 'resize', 'multi_generate', 'resize_to_iab')
        dimensions: Image dimensions in 'widthxheight' format (e.g., '1024x1024', '1920x1080')
        reference_image_url: URL of reference image for resize operations (optional)
        aspect_ratio: Aspect ratio for generation ('1:1', '3:4', '4:3', '9:16', '16:9')
        count: Number of images to generate for multi_generate (1-4, default: 1)
        iab_size: IAB standard size name for resize_to_iab operation

    Supported Operations:
    - 'generate': Create new image from text prompt
    - 'resize': Resize existing image to new dimensions
    - 'multi_generate': Generate multiple variations of an image
    - 'resize_to_iab': Resize to standard IAB advertising sizes

    Standard Dimensions:
    - Square: 1024x1024, 512x512
    - Portrait: 768x1024, 576x1024
    - Landscape: 1024x768, 1024x576
    - Social Media: 1080x1080 (Instagram), 1200x630 (Facebook)

    IAB Standard Sizes:
    - Banner: 728x90, Leaderboard: 728x90
    - Rectangle: 300x250, Large Rectangle: 336x280
    - Skyscraper: 160x600, Wide Skyscraper: 300x600
    - Mobile Banner: 320x50, Large Mobile Banner: 320x100

    EXAMPLES:
    Example: image_generation("Modern minimalist product showcase with clean lighting", "generate", "1024x1024", aspect_ratio="1:1")
    Example: image_generation("Fashion brand summer campaign", "multi_generate", "1080x1080", count=3)
    Example: image_generation("Resize campaign image", "resize", "728x90", reference_image_url="https://example.com/image.jpg")
    Example: image_generation("Convert to banner", "resize_to_iab", iab_size="Banner")
    """
    # Mock implementation - in real scenario this would connect to image generation API
    print(f"Image Generation: {operation_type} operation")
    print(f"Prompt: {prompt}")
    print(f"Dimensions: {dimensions}")
    print(f"Aspect Ratio: {aspect_ratio}")

    # Mock response based on operation type
    if operation_type == "generate":
        mock_image_url = (
            f"https://mock-api.com/generated-image-{hash(prompt) % 10000}.jpg"
        )
        return f"Successfully generated image with prompt: '{prompt}'\nDimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\nGenerated Image URL: {mock_image_url}\nImage ID: IMG_{hash(prompt) % 100000}"

    elif operation_type == "multi_generate":
        mock_urls = []
        for i in range(min(count, 4)):
            mock_urls.append(
                f"https://mock-api.com/generated-image-{hash(prompt) % 10000}-variant-{i+1}.jpg"
            )

        result = f"Successfully generated {len(mock_urls)} image variations with prompt: '{prompt}'\n"
        result += f"Dimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\n"
        result += "Generated Images:\n"
        for i, url in enumerate(mock_urls):
            result += (
                f"  Variant {i+1}: {url} (ID: IMG_{hash(prompt + str(i)) % 100000})\n"
            )
        return result

    elif operation_type == "resize":
        if reference_image_url:
            mock_resized_url = f"https://mock-api.com/resized-image-{hash(reference_image_url) % 10000}.jpg"
            return f"Successfully resized image from: {reference_image_url}\nNew Dimensions: {dimensions}\nResized Image URL: {mock_resized_url}\nImage ID: IMG_{hash(reference_image_url) % 100000}_resized"
        else:
            return "Error: Reference image URL is required for resize operation"

    elif operation_type == "resize_to_iab":
        if not iab_size:
            return "Error: IAB size is required for resize_to_iab operation"

        # Mock IAB size mappings
        iab_dimensions = {
            "Banner": "728x90",
            "Leaderboard": "728x90",
            "Rectangle": "300x250",
            "Large Rectangle": "336x280",
            "Skyscraper": "160x600",
            "Wide Skyscraper": "300x600",
            "Mobile Banner": "320x50",
            "Large Mobile Banner": "320x100",
        }

        if iab_size in iab_dimensions:
            actual_dimensions = iab_dimensions[iab_size]
            mock_iab_url = f"https://mock-api.com/iab-resized-{iab_size.lower().replace(' ', '-')}-{hash(prompt) % 10000}.jpg"
            return f"Successfully resized image to IAB standard: {iab_size}\nDimensions: {actual_dimensions}\nIAB Resized Image URL: {mock_iab_url}\nImage ID: IMG_{hash(prompt + iab_size) % 100000}_iab"
        else:
            return f"Error: Unsupported IAB size '{iab_size}'. Supported sizes: {', '.join(iab_dimensions.keys())}"

    else:
        return f"Error: Unsupported operation type '{operation_type}'. Supported: generate, resize, multi_generate, resize_to_iab"


def _get_google_credentials():
    """Get OAuth credentials from token.pickle with automatic refresh"""
    logger = logging.getLogger(__name__)

    creds = None
    if os.path.exists("token.pickle"):
        try:
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)

        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return None

    return creds


def _create_google_drive_folder(
    service, folder_name: str, parent_folder_id: str
) -> Dict[str, Any]:
    """Create a folder in Google Drive"""
    try:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }

        folder = (
            service.files()
            .create(
                body=file_metadata, supportsAllDrives=True, fields="id, webViewLink"
            )
            .execute()
        )

        return {"id": folder.get("id"), "link": folder.get("webViewLink")}
    except Exception as e:
        raise Exception(f"Failed to create folder: {str(e)}")


def _share_folder_with_users(service, folder_id: str, emails: List[str]):
    """Share a folder with iopex.com domain (ignores individual emails)"""
    try:
        # Share with entire iopex.com domain instead of individual emails
        permission = {"type": "domain", "role": "writer", "domain": "iopex.com"}
        service.permissions().create(
            fileId=folder_id, body=permission, supportsAllDrives=True
        ).execute()
        logging.getLogger(__name__).info(
            f"Shared folder {folder_id} with iopex.com domain"
        )
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Failed to share with iopex.com domain: {str(e)}"
        )


def _extract_targeting_info_from_placement(
    placement_info: Dict[str, Any],
) -> Dict[str, str]:
    """Extract targeting information from placement data"""
    # Default values
    targeting_info = {
        "age_range": "Not specified",
        "gender": "Not specified",
        "income_level": "Not specified",
        "interests": "Not specified",
        "location": "Not specified",
        "behavioral_data": "Not specified",
    }

    # Check for simple targeting format
    if "targeting" in placement_info:
        targeting = placement_info["targeting"]
        if isinstance(targeting, dict):
            targeting_info.update(
                {
                    "age_range": targeting.get("age_range", "Not specified"),
                    "gender": targeting.get("gender", "Not specified"),
                    "income_level": targeting.get("income_level", "Not specified"),
                    "interests": targeting.get("interests", "Not specified"),
                    "location": targeting.get("location", "Not specified"),
                    "behavioral_data": targeting.get(
                        "behavioral_data", "Not specified"
                    ),
                }
            )
        elif isinstance(targeting, str):
            # If targeting is a string, use it for all fields
            targeting_info = {
                "age_range": targeting,
                "gender": targeting,
                "income_level": targeting,
                "interests": targeting,
                "location": targeting,
                "behavioral_data": targeting,
            }

    return targeting_info


def _generate_pdf_with_media_plan_table(
    drive_service,
    docs_service,
    template_id: str,
    folder_id: str,
    filename: str,
    template_variables: Dict[str, Any],
    existing_doc_id: str = None
) -> Dict[str, Any]:
    """Generate PDF from template with Media Plan table support"""
    try:
        # Copy the template document (as Google Doc first)
        copied_doc = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": f"{filename}_temp_doc", "parents": [folder_id]},
                supportsAllDrives=True,
            )
            .execute()
        )

        doc_id = copied_doc["id"]

        # Handle regular text replacements first (excluding media_plan_table)
        requests = []
        table_data = None

        for key, value in template_variables.items():
            if key in ["media_plan_table", "mitie_cost_table"]:
                # Store table data for special handling
                table_data = value
            else:
                # Regular text replacement
                requests.append(
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{" + key + "}}",
                                "matchCase": True,
                            },
                            "replaceText": str(value),
                        }
                    }
                )

        # Execute regular text replacements first
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        # Handle table insertion if media_plan_table data exists
        if table_data:
            _insert_media_plan_table_simple(docs_service, doc_id, table_data)

        # Export the Google Doc as PDF
        pdf_export_url = (
            f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
        )

        # Download the PDF content
        import io
        from googleapiclient.http import MediaIoBaseDownload

        request = drive_service.files().export_media(
            fileId=doc_id, mimeType="application/pdf"
        )
        pdf_content = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_content, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Upload the PDF content as a new file
        pdf_content.seek(0)
        from googleapiclient.http import MediaIoBaseUpload

        media = MediaIoBaseUpload(pdf_content, mimetype="application/pdf")
        pdf_file = (
            drive_service.files()
            .create(
                body={"name": f"{filename}.pdf", "parents": [folder_id]},
                media_body=media,
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        # Generate URLs
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        pdf_url = f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"

        # Don't delete the document if we're using an existing one
        if not existing_doc_id:
            # Delete the temporary Google Doc only if we created it
            drive_service.files().delete(fileId=doc_id, supportsAllDrives=True).execute()

        return {
            "pdf_file_id": pdf_file["id"],
            "pdf_link": pdf_file["webViewLink"],
            "document_id": doc_id,
            "document_url": doc_url,
            "pdf_url": pdf_url
        }

    except Exception as e:
        raise Exception(f"Failed to generate PDF: {str(e)}")


def _insert_media_plan_table_simple(
    docs_service, doc_id: str, table_data: Dict[str, Any]
):
    """Insert a proper Google Docs table using the approach from tanaikech's implementation"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting media plan table insertion...")

        # Prepare table data
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        if not headers or not rows:
            logger.warning("No table headers or rows provided for media_plan_table")
            _fallback_text_replacement(docs_service, doc_id, table_data)
            return

        logger.info(
            f"Creating table with {len(headers)} columns and {len(rows) + 1} rows"
        )
        logger.info(f"Headers: {headers}")

        # Find the table placeholder (try both media_plan_table and mitie_cost_table)
        placeholder_text = "{{media_plan_table}}"
        placeholder_index = _find_placeholder_index(
            docs_service, doc_id, placeholder_text
        )

        if placeholder_index is None:
            # Try mitie_cost_table placeholder
            placeholder_text = "{{mitie_cost_table}}"
            placeholder_index = _find_placeholder_index(
                docs_service, doc_id, placeholder_text
            )

        if placeholder_index is None:
            logger.warning("No table placeholder found in document")
            _fallback_text_replacement(docs_service, doc_id, table_data)
            return

        logger.info(f"Found placeholder at index {placeholder_index}")

        # Create and populate table
        _create_and_populate_table(
            docs_service, doc_id, placeholder_index, placeholder_text, headers, rows
        )

    except Exception as e:
        logging.getLogger(__name__).error(f"Error inserting media plan table: {str(e)}")
        # Fallback to simple text replacement
        _fallback_text_replacement(docs_service, doc_id, table_data)


def _find_placeholder_index(docs_service, doc_id: str, placeholder_text: str) -> int:
    """Find the index of the placeholder text in the document"""
    doc = docs_service.documents().get(documentId=doc_id).execute()

    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            paragraph = element["paragraph"]
            for text_element in paragraph.get("elements", []):
                if "textRun" in text_element:
                    text_content = text_element["textRun"].get("content", "")
                    if placeholder_text in text_content:
                        return text_element.get("startIndex")
    return None


def _create_and_populate_table(
    docs_service,
    doc_id: str,
    placeholder_index: int,
    placeholder_text: str,
    headers: list,
    rows: list,
):
    """Create table and populate it using the Tanaikech approach with calculated indices"""
    try:
        logger = logging.getLogger(__name__)

        # Handle the new structure where headers might be empty
        if headers:
            # Traditional approach with headers
            num_rows = len(rows) + 1  # +1 for header row
            num_cols = len(headers)
            all_table_data = [headers] + rows
        else:
            # New approach without headers
            num_rows = len(rows)
            num_cols = max(len(row) for row in rows) if rows else 2
            all_table_data = rows

        logger.info(f"Creating table with {num_rows} rows and {num_cols} columns")

        # Create requests using the Tanaikech approach
        requests = _create_table_requests(
            placeholder_index, placeholder_text, all_table_data
        )

        # Execute all requests in one batch
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

        logger.info(
            f"Successfully created and populated table with {len(headers)} headers and {len(rows)} data rows"
        )

    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error creating and populating table: {str(e)}"
        )
        raise


def _create_table_requests(
    placeholder_index: int, placeholder_text: str, table_data: list
):
    """Create requests for table creation and population using the Tanaikech approach"""
    try:
        logger = logging.getLogger(__name__)
        if not table_data or not table_data[0]:
            return []

        num_rows = len(table_data)
        max_cols = max(len(row) for row in table_data)

        logger.info(
            f"Creating table requests for {num_rows} rows and {max_cols} columns"
        )

        # Start with deleting the placeholder and creating the table
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": placeholder_index,
                        "endIndex": placeholder_index + len(placeholder_text),
                    }
                }
            },
            {
                "insertTable": {
                    "location": {"index": placeholder_index},
                    "rows": num_rows,
                    "columns": max_cols,
                }
            },
        ]



        # Calculate cell indices and create insertion requests using the improved Tanaikech approach
        table_index = placeholder_index
        index = table_index + 5  # Table starts at index + 5

        cell_requests = []

        # Process each row to calculate indices correctly
        for row_idx, row_data in enumerate(table_data):
            row_index = (
                index + (0 if row_idx == 0 else 3) - 1
            )  # First row: index, subsequent rows: index + 3 - 1

            # Process each cell in the row
            for col_idx, cell_value in enumerate(row_data):
                cell_index = row_index + col_idx * 2
                cell_value_str = str(cell_value)

                logger.info(
                    f"Adding cell [{row_idx}][{col_idx}] = '{cell_value_str}' at index {cell_index}"
                )

                # Add text insertion request
                cell_requests.append(
                    {
                        "insertText": {
                            "text": cell_value_str,
                            "location": {"index": cell_index},
                        }
                    }
                )

                # Make header row bold
                if row_idx == 0:
                    cell_requests.append(
                        {
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": cell_index,
                                    "endIndex": cell_index + len(cell_value_str),
                                },
                                "textStyle": {"bold": True},
                                "fields": "bold",
                            }
                        }
                    )

                index = cell_index + 1

            # Adjust index for missing columns in this row
            if len(row_data) < max_cols:
                index += (max_cols - len(row_data)) * 2

        # Reverse the cell requests (insert from bottom-right to top-left)
        cell_requests.reverse()

        # Add cell requests to the main requests
        requests.extend(cell_requests)

        logger.info(
            f"Created {len(requests)} total requests for table creation and population"
        )
        return requests

    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating table requests: {str(e)}")
        raise


def _fallback_text_replacement(docs_service, doc_id: str, table_data: Dict[str, Any]):
    """Fallback method to replace {{media_plan_table}} with formatted text if table insertion fails"""
    try:
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        if not headers or not rows:
            fallback_text = "No table data available"
        else:
            # Create a simple text table
            lines = []

            # Add headers
            lines.append(" | ".join(str(header) for header in headers))
            lines.append("-" * 50)  # Separator line

            # Add rows
            for row in rows:
                if isinstance(row, list):
                    lines.append(" | ".join(str(cell) for cell in row))
                else:
                    lines.append(str(row))

            fallback_text = "\n".join(lines)

        # Replace the placeholder with formatted text
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{media_plan_table}}", "matchCase": True},
                    "replaceText": fallback_text,
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error in fallback text replacement: {str(e)}"
        )


def _create_sheet_from_template(
    drive_service,
    sheets_service,
    folder_id: str,
    sheet_name: str,
    template_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new sheet by copying a template and populating it with data"""
    try:
        # Copy the template to create a new sheet
        copied_sheet = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": sheet_name, "parents": [folder_id]},
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        sheet_id = copied_sheet["id"]

        # Get the template headers from row 1
        header_result = (
            sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=sheet_id,
                range="A1:AA1",  # Headers from A to AA
                majorDimension="ROWS",
            )
            .execute()
        )

        headers = (
            header_result.get("values", [[]])[0] if header_result.get("values") else []
        )

        # Create a mapping of data to column positions
        updates = []
        for col_index, header in enumerate(headers):
            if header.lower().replace(" ", "_") in data:
                col_letter = chr(65 + col_index)  # Convert to A, B, C, etc.
                cell_range = f"{col_letter}2"  # Row 2 for data
                value = str(data[header.lower().replace(" ", "_")])
                updates.append({"range": cell_range, "values": [[value]]})

        # Batch update the sheet
        if updates:
            body = {"valueInputOption": "RAW", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id, body=body
            ).execute()

        return {"sheet_id": sheet_id, "sheet_link": copied_sheet["webViewLink"]}
    except Exception as e:
        raise Exception(f"Failed to create sheet from template: {str(e)}")


def _generate_pdf_from_template(
    drive_service,
    docs_service,
    template_id: str,
    output_folder_id: str,
    filename: str,
    template_variables: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate PDF from Google Docs template"""
    try:
        # Create a copy of the template
        copied_doc = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": f"{filename}_temp_doc", "parents": [output_folder_id]},
                supportsAllDrives=True,
            )
            .execute()
        )

        doc_id = copied_doc["id"]

        # Replace placeholders in the document
        requests_list = []
        for placeholder, value in template_variables.items():
            requests_list.append(
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": f"{{{{{placeholder}}}}}",  # {{placeholder}} format
                            "matchCase": False,
                        },
                        "replaceText": str(value),
                    }
                }
            )

        if requests_list:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests_list}
            ).execute()

        # Export as PDF
        pdf_export = (
            drive_service.files()
            .export(fileId=doc_id, mimeType="application/pdf")
            .execute()
        )

        # Create PDF file in Drive
        pdf_metadata = {"name": f"{filename}.pdf", "parents": [output_folder_id]}

        # Upload PDF content
        from googleapiclient.http import MediaIoBaseUpload
        import io

        pdf_file = (
            drive_service.files()
            .create(
                body=pdf_metadata,
                media_body=MediaIoBaseUpload(
                    io.BytesIO(pdf_export), mimetype="application/pdf"
                ),
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        # Delete the temporary document
        drive_service.files().delete(fileId=doc_id, supportsAllDrives=True).execute()

        return {"pdf_file_id": pdf_file["id"], "pdf_link": pdf_file["webViewLink"]}
    except Exception as e:
        raise Exception(f"Failed to generate PDF: {str(e)}")


@function_schema
def create_insertion_order(
    order_number: str,
    campaign_name: str,
    brand: str,
    customer_approver: str,
    customer_approver_email: str,
    sales_owner: str,
    sales_owner_email: str,
    fulfillment_owner: str,
    fulfillment_owner_email: str,
    objective_description: str,
    placement_data: str,
    base_folder_id: Optional[str] = None,
    sheet_template_id: Optional[str] = None,
    pdf_template_id: Optional[str] = None,
) -> str:
    """
    CREATE INSERTION ORDER IN GOOGLE DRIVE

    Creates a complete insertion order with Google Drive folder, Google Sheet, and PDF document.
    This tool automates the entire insertion order creation process including:
    - Creating a campaign folder in Google Drive
    - Generating a Google Sheet from a template with order details
    - Creating a PDF document from a template with Media Plan table
    - Sharing all resources with stakeholders

    Args:
        order_number: The insertion order number (e.g., "IO-340371-3439")
        campaign_name: Name of the marketing campaign
        brand: Brand name for the campaign
        customer_approver: Name of the customer approver
        customer_approver_email: Email address of the customer approver
        sales_owner: Name of the sales owner
        sales_owner_email: Email address of the sales owner
        fulfillment_owner: Name of the fulfillment owner
        fulfillment_owner_email: Email address of the fulfillment owner
        objective_description: Description of the campaign objectives
        placement_data: JSON string containing placement information with COMPLETE targeting data structure
        base_folder_id: Google Drive folder ID where campaign folder will be created (optional, uses env var if not provided)
        sheet_template_id: Google Sheets template ID to copy (optional, uses env var if not provided)
        pdf_template_id: Google Docs template ID for PDF generation (optional, uses env var if not provided)

    CRITICAL: For Media Plan table to populate correctly, placement_data MUST include targeting configuration:

    PLACEMENT DATA STRUCTURE (JSON string):
    [
        {
            "name": "Social Media Campaign",
            "destination": "Instagram",
            "start_date": "2024-06-01",
            "end_date": "2024-08-31",
            "metrics": {
                "impressions": 500000,
                "clicks": 25000
            },
            "bid_rate": {
                "cpm": 2.50,
                "cpc": 0.75
            },
            "budget": {
                "amount": 100000.00
            },
            "targeting": {
                "age_range": "18-34",
                "gender": "Male, Female",
                "income_level": "Middle Income",
                "location": "United States, Canada",
                "interests": "Technology, Gaming",
                "behavioral_data": "Tech Enthusiasts, Early Adopters"
            }
        }
    ]

    EXAMPLES:
    Example: create_insertion_order("IO-123456", "Summer Campaign 2024", "Example Brand", "John Smith", "john@company.com", "Launch summer product line", '[{"name": "Social Media", "destination": "Instagram", "start_date": "2024-06-01", "end_date": "2024-08-31", "metrics": {"impressions": 500000, "clicks": 25000}, "bid_rate": {"cpm": 2.50, "cpc": 0.75}, "budget": {"amount": 100000.00}, "targeting": {"age_range": "18-24", "gender": "Male, Female", "income_level": "Middle Income", "location": "United States", "interests": "Technology", "behavioral_data": "Tech Enthusiasts"}}]')
    """
    logger = logging.getLogger(__name__)

    try:
        # Get credentials
        credentials = _get_google_credentials()
        if not credentials:
            return "Error: Google OAuth credentials not found. Please ensure token.pickle file exists and contains valid credentials."

        # Build Google services
        drive_service = build("drive", "v3", credentials=credentials)
        sheets_service = build("sheets", "v4", credentials=credentials)
        docs_service = build("docs", "v1", credentials=credentials)

        # Get configuration from environment variables or use provided values
        base_folder = base_folder_id or os.getenv("BASE_GOOGLE_DRIVE_FOLDER_ID")
        sheet_template = sheet_template_id or os.getenv("GOOGLE_SHEET_TEMPLATE_ID")
        pdf_template = pdf_template_id or os.getenv("PDF_GENERATION_TEMPLATE_ID")

        if not base_folder:
            return "Error: BASE_GOOGLE_DRIVE_FOLDER_ID not configured. Please set environment variable or provide base_folder_id parameter."
        if not sheet_template:
            return "Error: GOOGLE_SHEET_TEMPLATE_ID not configured. Please set environment variable or provide sheet_template_id parameter."
        if not pdf_template:
            return "Error: PDF_GENERATION_TEMPLATE_ID not configured. Please set environment variable or provide pdf_template_id parameter."

        # Parse placement data - FIX: Handle array of placements
        try:
            placement_list = (
                json.loads(placement_data)
                if isinstance(placement_data, str)
                else placement_data
            )
            if not isinstance(placement_list, list):
                return (
                    "Error: placement_data must be a JSON array of placement objects."
                )
        except json.JSONDecodeError:
            return "Error: Invalid placement_data JSON format."

        # Create campaign folder
        folder_name = f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}"
        campaign_folder = _create_google_drive_folder(
            drive_service, folder_name, base_folder
        )

        # Create PDF subfolder
        pdf_folder = _create_google_drive_folder(
            drive_service, "PDF Files", campaign_folder["id"]
        )

        # Share folders with stakeholders
        stakeholder_emails = [
            customer_approver_email,
            sales_owner_email,
            fulfillment_owner_email,
        ]
        _share_folder_with_users(
            drive_service, campaign_folder["id"], stakeholder_emails
        )

        # Prepare data for sheet (use first placement for sheet data)
        first_placement = placement_list[0] if placement_list else {}
        sheet_data = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "objective_description": objective_description,
            "placement_name": first_placement.get("name", ""),
            "placement_destination": first_placement.get("destination", ""),
            "start_date": first_placement.get("start_date", ""),
            "end_date": first_placement.get("end_date", ""),
        }

        # Create Google Sheet from template
        sheet_result = _create_sheet_from_template(
            drive_service,
            sheets_service,
            campaign_folder["id"],
            f"Order_{order_number}",
            sheet_template,
            sheet_data,
        )

        # NEW: Prepare Media Plan table data and PDF variables with proper targeting info
        media_plan_table_rows = []
        placement_details = []
        total_impressions = 0
        total_clicks = 0
        total_budget = 0

        for i, placement_info in enumerate(placement_list, 1):
            # Extract placement data
            name = placement_info.get("name", f"Placement {i}")
            destination = placement_info.get("destination", "")
            start_date = placement_info.get("start_date", "")
            end_date = placement_info.get("end_date", "")

            # Extract metrics
            metrics = placement_info.get("metrics", {})
            impressions = metrics.get("impressions", 0)
            clicks = metrics.get("clicks", 0)

            # Extract bid rates
            bid_rate = placement_info.get("bid_rate", {})
            cpm = bid_rate.get("cpm", 0.0)
            cpc = bid_rate.get("cpc", 0.0)

            # Extract budget
            budget = placement_info.get("budget", {})
            amount = budget.get("amount", 0.0)

            # Add to totals
            total_impressions += impressions
            total_clicks += clicks
            total_budget += amount

            # Extract targeting information - FIX: Handle targeting properly
            targeting_info = _extract_targeting_info_from_placement(placement_info)

            # Create detailed placement description
            placement_detail = f"""
Placement {i}: {name}
  Destination: {destination}
  Duration: {start_date} - {end_date}
  Metrics: {impressions:,} impressions, {clicks:,} clicks
  Bid Rate: ${cpm} CPM
  CPC: ${cpc}
  Budget: ${amount:,.2f}
  Target Audience:
    - Age Range: {targeting_info['age_range']}
    - Gender: {targeting_info['gender']}
    - Income Level: {targeting_info['income_level']}
    - Interests: {targeting_info['interests']}
    - Location: {targeting_info['location']}
    - Behavioral Data: {targeting_info['behavioral_data']}
            """.strip()
            placement_details.append(placement_detail)

            # Create table row for media plan table
            targeting_summary = f"{targeting_info['age_range']}, {targeting_info['gender']}, {targeting_info['income_level']}, {targeting_info['location']}, {targeting_info['interests']}, {targeting_info['behavioral_data']}"

            table_row = [
                f"${amount:,.2f}",  # budget
                start_date,  # start date
                end_date,  # end date
                name,  # placement name
                destination,  # placement destination
                targeting_summary,  # targeting
                objective_description,  # objective description
                f"{impressions:,}",  # target impressions
                f"{clicks:,}",  # target clicks
                f"${cpm}",  # cpm
                f"${cpc}",  # cpc
            ]
            media_plan_table_rows.append(table_row)

        # Get overall date range
        start_dates = [
            p.get("start_date", "") for p in placement_list if p.get("start_date")
        ]
        end_dates = [p.get("end_date", "") for p in placement_list if p.get("end_date")]
        earliest_start = min(start_dates) if start_dates else ""
        latest_end = max(end_dates) if end_dates else ""

        # Create media plan table data structure
        media_plan_table = {
            "headers": [
                "Budget",
                "Start Date",
                "End Date",
                "Placement Name",
                "Placement Destination",
                "Targeting",
                "Objective Description",
                "Target Impressions",
                "Target Clicks",
                "CPM",
                "CPC",
            ],
            "rows": media_plan_table_rows,
        }

        # Prepare enhanced PDF template variables with Media Plan table
        pdf_variables = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "start_date": earliest_start,
            "end_date": latest_end,
            "placement_details": "\n\n".join(placement_details),
            "media_plan_table": media_plan_table,  # This is the key addition!
            "impressions": str(total_impressions),
            "clicks": str(total_clicks),
            "cpm": "Multiple CPM rates (see placement details)",
            "cpc": "Multiple CPC rates (see placement details)",
            "budget_amount": str(total_budget),
            "age_range": "Multiple (see placement details)",
            "gender": "Multiple (see placement details)",
            "income_level": "Multiple (see placement details)",
            "interests": "Multiple (see placement details)",
            "location": "Multiple (see placement details)",
            "audience_segments": "Multiple (see placement details)",
            "device_targeting": "All Devices",
            "objective_description": objective_description,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Generate PDF with Media Plan table support
        pdf_result = _generate_pdf_with_media_plan_table(
            drive_service,
            docs_service,
            pdf_template,
            pdf_folder["id"],
            f"{order_number}_v0",
            pdf_variables,
        )

        return (
            f"✅ Insertion order created successfully!\n\n"
            f"📁 Campaign Folder: {campaign_folder['link']}\n"
            f"📊 Google Sheet: {sheet_result['sheet_link']}\n"
            f"📄 PDF Document: {pdf_result['pdf_link']}\n\n"
            f"Order Number: {order_number}\n"
            f"Campaign: {campaign_name}\n"
            f"All stakeholders have been granted access to the resources."
        )

    except Exception as e:
        logger.error(f"Error creating insertion order: {str(e)}")
        return f"❌ Error creating insertion order: {str(e)}"


def _connect_to_salesforce():
    """Connect to Salesforce using simple-salesforce library"""
    try:
        from simple_salesforce import Salesforce

        # Get Salesforce credentials from environment
        username = os.getenv("SALESFORCE_USERNAME")
        password = os.getenv("SALESFORCE_PASSWORD")
        security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        domain = os.getenv(
            "SALESFORCE_DOMAIN", "test"
        )  # test for sandbox, login for production

        if not all([username, password, security_token]):
            raise Exception(
                "Missing Salesforce credentials. Please set SALESFORCE_USERNAME, SALESFORCE_PASSWORD, and SALESFORCE_SECURITY_TOKEN environment variables."
            )

        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

        return sf
    except ImportError:
        raise Exception(
            "simple-salesforce library not installed. Please install it with: pip install simple-salesforce"
        )
    except Exception as e:
        raise Exception(f"Failed to connect to Salesforce: {str(e)}")


def _create_salesforce_insertion_order_direct(
    sf, order_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create insertion order record directly in Salesforce (replicating connector service logic)"""
    try:
        # Prepare the insertion order record data - using only core fields that should exist
        sf_data = {
            "Name": f"{order_data['Brand']} - {order_data['CampaignName']}",
            "Order_Number__c": order_data["OrderNo"],
            "Brand__c": order_data["Brand"],
            "Campaign_Name__c": order_data["CampaignName"],
            "Customer_Approver__c": order_data["CustomerApprover"],
            "Customer_Approver_Email__c": order_data["CustomerApproverEmail"],
            "Sales_Owner__c": order_data["SalesOwner"],
            "Sales_Owner_Email__c": order_data["SalesOwnerEmail"],
            "Fulfillment_Owner__c": order_data["FulfillmentOwner"],
            "Fulfillment_Owner_Email__c": order_data["FulfillmentOwnerEmail"],
            "Objective_Description__c": order_data["ObjectiveDetails"]["Description"],
            "Status__c": "Draft",
        }

        # Add lookup fields - only if valid Salesforce IDs and accessible
        # Try to add Account lookup, but continue if it fails due to permissions
        if order_data.get("account_id") and _is_valid_salesforce_id(
            order_data["account_id"]
        ):
            try:
                # Test if we can access this account first
                sf.Account.get(order_data["account_id"])
                sf_data["Account__c"] = order_data["account_id"]
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Cannot access Account {order_data['account_id']}: {str(e)}"
                )
                # Continue without the Account lookup

        # Try to add Opportunity lookup, but continue if it fails due to permissions
        if order_data.get("opportunity_id") and _is_valid_salesforce_id(
            order_data["opportunity_id"]
        ):
            try:
                # Test if we can access this opportunity first
                sf.Opportunity.get(order_data["opportunity_id"])
                sf_data["Opportunity__c"] = order_data["opportunity_id"]
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Cannot access Opportunity {order_data['opportunity_id']}: {str(e)}"
                )
                # Continue without the Opportunity lookup

        # Add PDF link if available
        if order_data.get("PDF_View_Link_c"):
            sf_data["PDF_View_Link__c"] = order_data["PDF_View_Link_c"]

        # Create the main insertion order record
        result = sf.Insertion_Order__c.create(sf_data)
        io_id = result["id"]

        # Create placement records for each placement (replicating connector service logic)
        for placement in order_data.get("Placement", []):
            _create_placement_record_direct(sf, io_id, placement)

        return {
            "id": io_id,
            "success": result["success"],
            "message": "Insertion order created successfully in Salesforce",
        }

    except Exception as e:
        raise Exception(f"Failed to create Salesforce insertion order: {str(e)}")


def _create_placement_record_direct(
    sf, insertion_order_id: str, placement_data: Dict[str, Any]
):
    """Create placement record linked to insertion order (replicating connector service logic)"""
    try:
        placement_record = {
            "Name": placement_data.get("Name", "Placement"),
            "Insertion_Order__c": insertion_order_id,
            "Destination__c": placement_data.get("Destination"),
            "Start_Date__c": placement_data.get("StartDate"),
            "End_Date__c": placement_data.get("EndDate"),
        }

        # Add metrics if available
        if placement_data.get("Metrics"):
            metrics = placement_data["Metrics"]
            if metrics.get("Impressions"):
                placement_record["Impressions__c"] = metrics["Impressions"]
            if metrics.get("Clicks"):
                placement_record["Clicks__c"] = metrics["Clicks"]

        # Add budget if available
        if placement_data.get("Budget") and placement_data["Budget"].get("Amount"):
            placement_record["Budget_Amount__c"] = placement_data["Budget"]["Amount"]

        # Add bid rates if available
        if placement_data.get("BidRate"):
            bid_rate = placement_data["BidRate"]
            if bid_rate.get("CPM"):
                placement_record["CPM__c"] = bid_rate["CPM"]
            if bid_rate.get("CPC"):
                placement_record["CPC__c"] = bid_rate["CPC"]

        # Add targeting configuration if available
        if placement_data.get("targeting"):
            targeting = placement_data["targeting"]
            if targeting.get("age_range"):
                placement_record["target_audience_age_range__c"] = targeting[
                    "age_range"
                ]
            if targeting.get("gender"):
                placement_record["target_audience_gender__c"] = targeting["gender"]
            if targeting.get("income_level"):
                placement_record["target_audience_income_level__c"] = targeting[
                    "income_level"
                ]
            if targeting.get("location"):
                placement_record["target_audience_location__c"] = targeting["location"]
            if targeting.get("interests"):
                placement_record["target_audience_interests__c"] = targeting[
                    "interests"
                ]
            if targeting.get("behavioral_data"):
                placement_record["target_audience_behavioral_data__c"] = ", ".join(
                    targeting["behavioral_data"]
                )

        # Create the placement record
        result = sf.Placement__c.create(placement_record)
        return result

    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Failed to create placement record: {str(e)}"
        )
        # Don't fail the entire operation if placement creation fails
        return None


def _is_valid_salesforce_id(sf_id: str) -> bool:
    """Check if a string is a valid Salesforce ID format"""
    if not sf_id or not isinstance(sf_id, str):
        return False
    # Salesforce IDs are 15 or 18 characters long and alphanumeric
    return len(sf_id) in [15, 18] and sf_id.isalnum()


@function_schema
def get_salesforce_accounts() -> str:
    """
    GET SALESFORCE ACCOUNTS

    Retrieves a list of all Salesforce Accounts for dropdown population or selection.
    This tool uses direct Salesforce API calls to fetch account data.

    Returns:
        A formatted string containing account information including:
        - Account ID
        - Account Name
        - Total number of accounts found

    EXAMPLES:
    Example: get_salesforce_accounts()
    """
    logger = logging.getLogger(__name__)

    try:
        # Connect to Salesforce directly
        logger.info("Connecting to Salesforce to retrieve accounts")
        sf = _connect_to_salesforce()

        # Query for accounts
        query = "SELECT Id, Name, Type, Industry FROM Account ORDER BY Name LIMIT 1000"
        result = sf.query(query)

        accounts = result["records"]
        logger.info(f"Retrieved {len(accounts)} Salesforce accounts")

        if not accounts:
            return "No Salesforce accounts found."

        # Format the results for display
        response = f"✅ Found {len(accounts)} Salesforce Accounts:\n\n"

        for i, account in enumerate(accounts, 1):
            account_id = account.get("Id", "N/A")
            account_name = account.get("Name", "N/A")
            account_type = account.get("Type", "N/A")
            industry = account.get("Industry", "N/A")

            response += f"{i:3d}. {account_name}\n"
            response += f"     ID: {account_id}\n"
            response += f"     Type: {account_type}\n"
            response += f"     Industry: {industry}\n\n"

            # Limit display to first 20 accounts to avoid overwhelming output
            if i >= 20:
                remaining = len(accounts) - 20
                if remaining > 0:
                    response += f"... and {remaining} more accounts\n\n"
                break

        response += f"📊 Total Accounts: {len(accounts)}\n"
        response += f"🔗 Use Account IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(f"Error retrieving Salesforce accounts: {str(e)}")
        return f"❌ Error retrieving Salesforce accounts: {str(e)}"


@function_schema
def get_salesforce_opportunities() -> str:
    """
    GET SALESFORCE OPPORTUNITIES

    Retrieves a list of all Salesforce Opportunities with key details.
    This tool uses direct Salesforce API calls to fetch opportunity data.

    Returns:
        A formatted string containing opportunity information including:
        - Opportunity ID
        - Opportunity Name
        - Stage Name
        - Amount
        - Close Date
        - Associated Account

    EXAMPLES:
    Example: get_salesforce_opportunities()
    """
    logger = logging.getLogger(__name__)

    try:
        # Connect to Salesforce directly
        logger.info("Connecting to Salesforce to retrieve opportunities")
        sf = _connect_to_salesforce()

        # Query for opportunities with account information
        query = """SELECT Id, Name, StageName, Amount, CloseDate, Type, Description,
                          AccountId, Account.Name, Account__c, Account__r.Name
                   FROM Opportunity
                   ORDER BY CloseDate DESC, Name
                   LIMIT 1000"""
        result = sf.query(query)

        opportunities = result["records"]
        logger.info(f"Retrieved {len(opportunities)} Salesforce opportunities")

        if not opportunities:
            return "No Salesforce opportunities found."

        # Format the results for display
        response = f"✅ Found {len(opportunities)} Salesforce Opportunities:\n\n"

        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get("Id", "N/A")
            opp_name = opp.get("Name", "N/A")
            stage = opp.get("StageName", "N/A")
            amount = opp.get("Amount", 0)
            close_date = opp.get("CloseDate", "N/A")
            opp_type = opp.get("Type", "N/A")

            # Get account name and ID (try different fields)
            account_name = "N/A"
            account_id = "N/A"
            if opp.get("Account") and opp["Account"].get("Name"):
                account_name = opp["Account"]["Name"]
                account_id = opp.get("AccountId", "N/A")
            elif opp.get("Account__r") and opp["Account__r"].get("Name"):
                account_name = opp["Account__r"]["Name"]
                account_id = opp.get("Account__c", "N/A")
            else:
                account_id = opp.get("AccountId") or opp.get("Account__c", "N/A")

            # Format amount
            amount_str = f"${amount:,.2f}" if amount else "N/A"

            response += f"{i:3d}. {opp_name}\n"
            response += f"     ID: {opp_id}\n"
            response += f"     Account: {account_name} (ID: {account_id})\n"
            response += f"     Stage: {stage}\n"
            response += f"     Amount: {amount_str}\n"
            response += f"     Close Date: {close_date}\n"
            response += f"     Type: {opp_type}\n\n"

            # Limit display to first 15 opportunities to avoid overwhelming output
            if i >= 15:
                remaining = len(opportunities) - 15
                if remaining > 0:
                    response += f"... and {remaining} more opportunities\n\n"
                break

        response += f"📊 Total Opportunities: {len(opportunities)}\n"
        response += f"🔗 Use Opportunity IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(f"Error retrieving Salesforce opportunities: {str(e)}")
        return f"❌ Error retrieving Salesforce opportunities: {str(e)}"


@function_schema
def get_salesforce_opportunities_by_account(account_id: str) -> str:
    """
    GET SALESFORCE OPPORTUNITIES BY ACCOUNT

    Retrieves Salesforce Opportunities associated with a specific Account.
    This tool uses direct Salesforce API calls to fetch filtered opportunity data.

    Args:
        account_id: The Salesforce Account ID to filter opportunities by

    Returns:
        A formatted string containing opportunity information for the specified account including:
        - Opportunity ID
        - Opportunity Name
        - Stage Name
        - Amount
        - Close Date
        - Account Name

    EXAMPLES:
    Example: get_salesforce_opportunities_by_account("001XX000003DHP0YAO")
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate account ID format
        if not _is_valid_salesforce_id(account_id):
            return f"❌ Invalid Salesforce Account ID format: {account_id}. Expected 15 or 18 character alphanumeric ID."

        # Connect to Salesforce directly
        logger.info(
            f"Connecting to Salesforce to retrieve opportunities for account: {account_id}"
        )
        sf = _connect_to_salesforce()

        # First, try to get the account name to verify it exists
        account_name = "Unknown Account"
        try:
            account_result = sf.Account.get(account_id)
            account_name = account_result.get("Name", "Unknown Account")
        except Exception as account_error:
            logger.warning(
                f"Could not retrieve account details for {account_id}: {str(account_error)}"
            )

        # Query for opportunities using both standard AccountId and custom Account__c lookup field
        query = f"""SELECT Id, Name, StageName, Amount, CloseDate, Type, Description,
                           AccountId, Account.Name, Account__c, Account__r.Name
                    FROM Opportunity
                    WHERE AccountId = '{account_id}' OR Account__c = '{account_id}'
                    ORDER BY CloseDate DESC, Name
                    LIMIT 1000"""
        result = sf.query(query)

        opportunities = result["records"]
        logger.info(
            f"Retrieved {len(opportunities)} Salesforce opportunities for account: {account_id}"
        )

        if not opportunities:
            return (
                f"No opportunities found for Account: {account_name} (ID: {account_id})"
            )

        # Format the results for display
        response = (
            f"✅ Found {len(opportunities)} Opportunities for Account: {account_name}\n"
        )
        response += f"🏢 Account ID: {account_id}\n\n"

        total_amount = 0
        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get("Id", "N/A")
            opp_name = opp.get("Name", "N/A")
            stage = opp.get("StageName", "N/A")
            amount = opp.get("Amount", 0)
            close_date = opp.get("CloseDate", "N/A")
            opp_type = opp.get("Type", "N/A")

            # Add to total amount if numeric
            if isinstance(amount, (int, float)) and amount > 0:
                total_amount += amount

            # Format amount
            amount_str = f"${amount:,.2f}" if amount else "N/A"

            response += f"{i:3d}. {opp_name}\n"
            response += f"     ID: {opp_id}\n"
            response += f"     Stage: {stage}\n"
            response += f"     Amount: {amount_str}\n"
            response += f"     Close Date: {close_date}\n"
            response += f"     Type: {opp_type}\n\n"

        # Add summary information
        response += f"📊 Summary:\n"
        response += f"   • Total Opportunities: {len(opportunities)}\n"
        response += f"   • Total Pipeline Value: ${total_amount:,.2f}\n"
        response += f"   • Account: {account_name}\n\n"
        response += f"🔗 Use Opportunity IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(
            f"Error retrieving opportunities for account {account_id}: {str(e)}"
        )
        return f"❌ Error retrieving opportunities for account {account_id}: {str(e)}"


@function_schema
def create_salesforce_insertion_order(
    order_number: str,
    campaign_name: str,
    brand: str,
    customer_approver: str,
    customer_approver_email: str,
    sales_owner: str,
    sales_owner_email: str,
    fulfillment_owner: str,
    fulfillment_owner_email: str,
    objective_description: str,
    placement_data: str,
    salesforce_account: str,
    salesforce_opportunity_id: str,
    salesforce_base_url: Optional[str] = None,
    base_folder_id: Optional[str] = None,
    pdf_template_id: Optional[str] = None,
) -> str:
    """
    CREATE INSERTION ORDER IN SALESFORCE (DIRECT API)

    Creates a complete insertion order in Salesforce with PDF documentation in Google Drive.
    This tool uses direct Salesforce API calls (no external connector service required) and automates:
    - Creating a PDF document in Google Drive with Media Plan table
    - Creating an insertion order record directly in Salesforce via API
    - Creating placement records with targeting and budget data
    - Linking the PDF to the Salesforce record
    - Returning URLs for both Salesforce record and PDF document

    Args:
        order_number: The insertion order number (e.g., "IO-340371-3439")
        campaign_name: Name of the marketing campaign
        brand: Brand name for the campaign
        customer_approver: Name of the customer approver
        customer_approver_email: Email address of the customer approver
        sales_owner: Name of the sales owner
        sales_owner_email: Email address of the sales owner
        fulfillment_owner: Name of the fulfillment owner
        fulfillment_owner_email: Email address of the fulfillment owner
        objective_description: Description of the campaign objectives
        placement_data: JSON string containing placement information with COMPLETE targeting data structure
        salesforce_account: Salesforce Account ID for the insertion order
        salesforce_opportunity_id: Salesforce Opportunity ID for the insertion order
        salesforce_base_url: Base URL for Salesforce Lightning (optional, uses env var if not provided)
        base_folder_id: Google Drive folder ID where PDF will be created (optional, uses env var if not provided)
        pdf_template_id: Google Docs template ID for PDF generation (optional, uses env var if not provided)

    CRITICAL: For Media Plan table to populate correctly, placement_data MUST include targeting configuration:

    PLACEMENT DATA STRUCTURE (JSON string):
    [
        {
            "name": "Social Media Campaign",
            "destination": "Instagram",
            "start_date": "2024-06-01",
            "end_date": "2024-08-31",
            "metrics": {
                "impressions": 500000,
                "clicks": 25000
            },
            "bid_rate": {
                "cpm": 2.50,
                "cpc": 0.75
            },
            "budget": {
                "amount": 100000.00
            },
            "targeting": {
                "age_range": "18-34",
                "gender": "Male, Female",
                "income_level": "Middle Income",
                "location": "United States, Canada",
                "interests": "Technology, Gaming",
                "behavioral_data": "Tech Enthusiasts, Early Adopters"
            }
        }
    ]

    EXAMPLES:
    Example: create_salesforce_insertion_order("IO-123456", "Summer Campaign 2024", "Example Brand", "John Smith", "john@company.com", "Launch summer product line", '[{"name": "Social Media", "destination": "Instagram", "start_date": "2024-06-01", "end_date": "2024-08-31", "metrics": {"impressions": 500000, "clicks": 25000}, "bid_rate": {"cpm": 2.50, "cpc": 0.75}, "budget": {"amount": 100000.00}, "targeting": {"age_range": "18-24", "gender": "Male, Female", "income_level": "Middle Income", "location": "United States", "interests": "Technology", "behavioral_data": "Tech Enthusiasts"}}]', "001XX000003DHP0", "006XX000004TMi2")
    """
    logger = logging.getLogger(__name__)

    try:
        # Get credentials for Google Drive PDF generation
        credentials = _get_google_credentials()
        if not credentials:
            return "Error: Google OAuth credentials not found. Please ensure token.pickle file exists and contains valid credentials."

        # Build Google services
        drive_service = build("drive", "v3", credentials=credentials)
        docs_service = build("docs", "v1", credentials=credentials)

        # Get configuration from environment variables or use provided values
        base_folder = base_folder_id or os.getenv("BASE_GOOGLE_DRIVE_FOLDER_ID")
        pdf_template = pdf_template_id or os.getenv("PDF_GENERATION_TEMPLATE_ID")
        sf_base_url = salesforce_base_url or os.getenv(
            "SALESFORCE_BASE_URL", "https://flow-business-5971.lightning.force.com"
        )

        if not base_folder:
            return "Error: BASE_GOOGLE_DRIVE_FOLDER_ID not configured. Please set environment variable or provide base_folder_id parameter."
        if not pdf_template:
            return "Error: PDF_GENERATION_TEMPLATE_ID not configured. Please set environment variable or provide pdf_template_id parameter."

        # Parse placement data - FIX: Handle array of placements
        try:
            placement_list = (
                json.loads(placement_data)
                if isinstance(placement_data, str)
                else placement_data
            )
            if not isinstance(placement_list, list):
                return (
                    "Error: placement_data must be a JSON array of placement objects."
                )
        except json.JSONDecodeError:
            return "Error: Invalid placement_data JSON format."

        # Step 1: Create PDF documentation in Google Drive
        logger.info("Creating Salesforce PDF documentation")

        # Create campaign folder for Salesforce
        folder_name = f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}_Salesforce"
        campaign_folder = _create_google_drive_folder(
            drive_service, folder_name, base_folder
        )

        # Create PDF subfolder
        pdf_folder = _create_google_drive_folder(
            drive_service, "PDF Files", campaign_folder["id"]
        )

        # Share folders with stakeholders
        stakeholder_emails = [
            customer_approver_email,
            sales_owner_email,
            fulfillment_owner_email,
        ]
        _share_folder_with_users(
            drive_service, campaign_folder["id"], stakeholder_emails
        )

        # NEW: Prepare Media Plan table data and PDF variables with proper targeting info
        media_plan_table_rows = []
        placement_details = []
        total_impressions = 0
        total_clicks = 0
        total_budget = 0

        for i, placement_info in enumerate(placement_list, 1):
            # Extract placement data
            name = placement_info.get("name", f"Placement {i}")
            destination = placement_info.get("destination", "")
            start_date = placement_info.get("start_date", "")
            end_date = placement_info.get("end_date", "")

            # Extract metrics
            metrics = placement_info.get("metrics", {})
            impressions = metrics.get("impressions", 0)
            clicks = metrics.get("clicks", 0)

            # Extract bid rates
            bid_rate = placement_info.get("bid_rate", {})
            cpm = bid_rate.get("cpm", 0.0)
            cpc = bid_rate.get("cpc", 0.0)

            # Extract budget
            budget = placement_info.get("budget", {})
            amount = budget.get("amount", 0.0)

            # Add to totals
            total_impressions += impressions
            total_clicks += clicks
            total_budget += amount

            # Extract targeting information
            targeting_info = _extract_targeting_info_from_placement(placement_info)

            # Create detailed placement description
            placement_detail = f"""
Placement {i}: {name}
  Destination: {destination}
  Duration: {start_date} - {end_date}
  Metrics: {impressions:,} impressions, {clicks:,} clicks
  Bid Rate: ${cpm} CPM
  CPC: ${cpc}
  Budget: ${amount:,.2f}
  Target Audience:
    - Age Range: {targeting_info['age_range']}
    - Gender: {targeting_info['gender']}
    - Income Level: {targeting_info['income_level']}
    - Interests: {targeting_info['interests']}
    - Location: {targeting_info['location']}
    - Behavioral Data: {targeting_info['behavioral_data']}
            """.strip()
            placement_details.append(placement_detail)

            # Create table row for media plan table
            targeting_summary = f"{targeting_info['age_range']}, {targeting_info['gender']}, {targeting_info['income_level']}, {targeting_info['location']}, {targeting_info['interests']}, {targeting_info['behavioral_data']}"

            table_row = [
                f"${amount:,.2f}",  # budget
                start_date,  # start date
                end_date,  # end date
                name,  # placement name
                destination,  # placement destination
                targeting_summary,  # targeting
                objective_description,  # objective description
                f"{impressions:,}",  # target impressions
                f"{clicks:,}",  # target clicks
                f"${cpm}",  # cpm
                f"${cpc}",  # cpc
            ]
            media_plan_table_rows.append(table_row)

        # Get overall date range
        start_dates = [
            p.get("start_date", "") for p in placement_list if p.get("start_date")
        ]
        end_dates = [p.get("end_date", "") for p in placement_list if p.get("end_date")]
        earliest_start = min(start_dates) if start_dates else ""
        latest_end = max(end_dates) if end_dates else ""

        # Create media plan table data structure
        media_plan_table = {
            "headers": [
                "Budget",
                "Start Date",
                "End Date",
                "Placement Name",
                "Placement Destination",
                "Targeting",
                "Objective Description",
                "Target Impressions",
                "Target Clicks",
                "CPM",
                "CPC",
            ],
            "rows": media_plan_table_rows,
        }

        # Prepare enhanced PDF template variables with Media Plan table
        pdf_variables = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "start_date": earliest_start,
            "end_date": latest_end,
            "placement_details": "\n\n".join(placement_details),
            "media_plan_table": media_plan_table,  # This is the key addition!
            "impressions": str(total_impressions),
            "clicks": str(total_clicks),
            "cpm": "Multiple CPM rates (see placement details)",
            "cpc": "Multiple CPC rates (see placement details)",
            "budget_amount": str(total_budget),
            "age_range": "Multiple (see placement details)",
            "gender": "Multiple (see placement details)",
            "income_level": "Multiple (see placement details)",
            "interests": "Multiple (see placement details)",
            "location": "Multiple (see placement details)",
            "audience_segments": "Multiple (see placement details)",
            "device_targeting": "All Devices",
            "objective_description": objective_description,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Generate PDF with Media Plan table support
        pdf_result = _generate_pdf_with_media_plan_table(
            drive_service,
            docs_service,
            pdf_template,
            pdf_folder["id"],
            f"{order_number}_Salesforce_v0",
            pdf_variables,
        )

        logger.info(f"PDF created successfully: {pdf_result['pdf_file_id']}")

        # Step 2: Prepare Salesforce data with PDF link
        salesforce_data = {
            "account_id": salesforce_account,
            "opportunity_id": salesforce_opportunity_id,
            "OrderNo": order_number,
            "Brand": brand,
            "CampaignName": campaign_name,
            "CustomerApprover": customer_approver,
            "CustomerApproverEmail": customer_approver_email,
            "SalesOwner": sales_owner,
            "SalesOwnerEmail": sales_owner_email,
            "FulfillmentOwner": fulfillment_owner,
            "FulfillmentOwnerEmail": fulfillment_owner_email,
            "ObjectiveDetails": {"Description": objective_description},
            "Placement": placement_list,  # Use the full placement list
            "PDF_View_Link_c": pdf_result["pdf_link"],  # Include the PDF link
        }

        # Step 3: Connect to Salesforce and create insertion order directly
        logger.info("Connecting to Salesforce and creating insertion order record")
        try:
            sf = _connect_to_salesforce()
            salesforce_response = _create_salesforce_insertion_order_direct(
                sf, salesforce_data
            )
        except Exception as sf_error:
            logger.error(f"Salesforce integration error: {str(sf_error)}")
            return f"❌ Error creating Salesforce insertion order: {str(sf_error)}"

        logger.info(f"Salesforce insertion order created: {salesforce_response}")

        # Step 4: Generate Salesforce Lightning URL
        salesforce_record_id = salesforce_response.get("id", "")
        salesforce_record_url = (
            f"{sf_base_url}/lightning/r/Insertion_Order__c/{salesforce_record_id}/view"
        )

        # Prepare success response
        return (
            f"✅ Salesforce insertion order created successfully!\n\n"
            f"🏢 Salesforce Record: {salesforce_record_url}\n"
            f"📄 PDF Document: {pdf_result['pdf_link']}\n"
            f"📁 Campaign Folder: {campaign_folder['link']}\n\n"
            f"Order Number: {order_number}\n"
            f"Campaign: {campaign_name}\n"
            f"Salesforce Account: {salesforce_account}\n"
            f"Salesforce Opportunity: {salesforce_opportunity_id}\n"
            f"Record ID: {salesforce_record_id}"
        )

    except Exception as e:
        logger.error(f"Error creating Salesforce insertion order: {str(e)}")
        return f"❌ Error creating Salesforce insertion order: {str(e)}"


@function_schema
def query_retriever(query: str, machine_types: Optional[List[str]] = None) -> list:
    """
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    If the user enters a machine type, add it to the machine_types list. For example, if the user asks "What is the part number for the Motorized Controller on the 6800?", add "6800" to the machine_types list.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="What is TAL"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"

    Example: query="diagnostic code X is 0 Y is 2"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".

    DO NOT ADD MACHINE TYPES TO THE QUERY. ONLY USE THE MACHINE TYPES LIST.
    FOR EXAMPLE, IF THE USER ASKS "What is the part number for the Motorized Controller on the 6800 System 7?",
    ADD "6800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller System 7"
    NOTICE HOW THE MACHINE NAME "SYSTEM 7" IS INCLUDED IN THE QUERY.

    INCLUDE THE MODEL NUMBER AND NAME IN THE QUERY IF AVAILABLE.
    FOR EXAMPLE, IF THE USER ASKS "SureBase (Machine Type: 4800 Model: 0xx) SLO motor part"
    ADD "4800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller for SureBase model 100".
    NOTICE HOW THE MACHINE NAME "SureBase" IS INCLUDED IN THE QUERY.

    VALID MACHINE TYPES:

    1. 2001
    2. 2011
    3. 4612
    4. 4613
    5. 4614
    6. 4615
    7. 4674
    8. 4683
    9. 4693
    10. 4694
    11. 4695
    12. 4750
    13. 4800
    14. 4810
    15. 4818
    16. 4825
    17. 4828
    18. 4835
    19. 4836
    20. 4838
    21. 4840
    22. 4845
    23. 4846
    24. 4851
    25. 4852
    26. 4855
    27. 4888
    28. 4900
    29. 4901
    30. 4910
    31. 6140
    32. 6183
    33. 6200
    34. 6201
    35. 6225
    36. 6700
    37. 6800
    38. 6900
    39. 7054
    40. 8368
    41. 4610
    42. 4679
    43. 4685
    44. 4698
    45. 4689
    46. 4820
    47. 6145
    48. 6149
    49. 6150
    50. 6160
    51. 6180
    52. 6260
    53. 9338

    If no machine types are provided, query without the machine type.
    """

    def get_response(url, params):
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            print("^" * 100)
            print("Response")
            print(response.json())
            print("^" * 100)
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i, segment in enumerate(segments):
                res += (
                    "*" * 5 + f"\n\nSegment Begins: " + "\n"
                )  # +"Contextual Header: "
                references = ""
                for j, chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: " + chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk["page_info"]))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"] + f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += (
                                f"{filename} page {page}" + f" [aws_id: {filename}]\n"
                            )
                        else:
                            res += (
                                f"{filename} page {page}"
                                + f" [aws_id: {filename}_page_{page}]\n"
                            )
                    if "page" in filename:
                        sources.append(
                            f"{filename}"
                            + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]"
                        )
                    else:
                        sources.append(
                            f"{filename} page {page}"
                            + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]"
                        )
            res += "Segment Ends\n" + "-" * 5 + "\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["", []]

    url = os.getenv("TGCS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60,
        "machine_types": machine_types,
        "collection_id": "toshiba_demo_4",
    }
    try:
        first_response, sources = get_response(url, params)
        print("-" * 100)
        print("\nGot response")
        print(first_response[:200])
        print(sources)
        print("-" * 100)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["", []]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "machine_types": machine_types
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["", []]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res + first_response + second_response)
    return [res + first_response + second_response, sources + second_sources]


@function_schema
def customer_query_retriever(query: str, collection_id: str) -> list:
    """ "
    TOSHIBA CUSTOMER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba's Customer knowledge base.
    This tool is only used for customer-specific information.
    List of customers and their collection_ids:
    1. Walgreens: toshiba_walgreens
    2. Kroger: toshiba_kroger (Note that Harris Teeter is also included in this collection)
    3. Sam's Club: toshiba_sams_club
    4. Tractor Supply: toshiba_tractor_supply
    5. Dollar General: toshiba_dollar_general
    6. Wegmans: toshiba_wegmans
    7. Ross: toshiba_ross
    8. Costco: toshiba_costco
    9. Whole Foods: toshiba_whole_foods
    10. BJs: toshiba_bjs
    11. Alex Lee: toshiba_alex_lee
    12. Badger: toshiba_badger
    13. Best Buy: toshiba_best_buy
    14. GNC: toshiba_GNC
    15. Coach: toshiba_coach
    16. QuickChek: toshiba_quickchek
    16. CAM: toshiba_cameras_al
    17. Hudson News: toshiba_hudson_news
    18. IDKIDS: toshiba_idkids

    Use toshiba_demo_4 if the customer retriever fails to return any relevant results

    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"

    Essentially, if the user asks "Walgreens <question>" then the query should be "<question>" and the collection_id should be "toshiba_walgreens"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
        # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i, segment in enumerate(segments):
                res += (
                    "*" * 5 + f"\n\nSegment Begins: " + "\n"
                )  # +"Contextual Header: "
                references = ""
                for j, chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: " + chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk["page_info"]))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        # print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += (
                                f"{filename} page {page}"
                                + f" [aws_id: {filename}_page_{page}]\n"
                            )
                    if "page" in filename:
                        sources.append(
                            f"{filename}"
                            + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]"
                        )
                    else:
                        sources.append(
                            f"{filename} page {page}"
                            + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]"
                        )

            res += "Segment Ends\n" + "-" * 5 + "\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["", []]

    url = os.getenv("CUSTOMER_RETRIEVER_URL") + "/query-chunks"
    params = {"query": query, "top_k": 60, "collection_id": collection_id}
    first_response, sources = ["", []]
    try:
        first_response, sources = get_response(url, params)
        print("-" * 100)
        print("\nGot response")
        print(first_response[:200])
        print(sources)
        print("-" * 100)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["", []]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res + first_response)
    return [res + first_response, sources]


@function_schema
def sql_database(query: str) -> list:
    """ "
    SQL DATABASE TOOL
    Any query that has "SQL: <question>" MUST use this tool.

    Use this tool to query the Toshiba Service Request database.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    query = "Which SRs closed in Florida and who handled them?"
    query = "What tickets were handled by Jason Hechler?"
    """
    st_url = os.getenv("SQL_RETRIEVER_URL") + "/query"
    params = {"query": query}
    try:
        print(st_url)
        print(params)
        response = requests.post(st_url, params=params)
        print(response.json())
        res = response.json()["response"]
        return [res, []]
    except Exception as e:
        print(f"Failed to call SR database: {e}")
        return []


@function_schema
def vectorizer_conversative_search(
    query: str,
    top_k: Optional[int] = 5,
    score_threshold: Optional[float] = 0.7,
) -> str:
    """
    VECTORIZER CONVERSATIVE SEARCH TOOL

    Uses the real ingestion config (python_packages/elevaite_ingestion/config.json) to:
    - Read Qdrant host/port/collection
    - Read default embedding model
    - Perform a semantic search over the existing vectorized PDF data

    Args:
        query: The search query
        top_k: Number of results to retrieve
        score_threshold: Minimum similarity score

    Returns:
        A formatted string containing retrieved chunks with source metadata.
    """
    import os
    import json
    from pathlib import Path

    try:
        from qdrant_client import QdrantClient
    except Exception:
        return "Error: Qdrant client not installed. Please install with: pip install qdrant-client"

    try:
        # Locate repo root relative to this file and load config.json
        current_dir = Path(__file__).resolve().parent
        repo_root = current_dir.parents[
            3
        ]  # up from python_apps/agent_studio/agent-studio/agents
        cfg_path = repo_root / "python_packages" / "elevaite_ingestion" / "config.json"
        with open(cfg_path, "r") as f:
            cfg = json.load(f)

        qdrant_cfg = cfg.get("vector_db", {}).get("databases", {}).get("qdrant", {})
        host = qdrant_cfg.get("host", "http://localhost")
        port = qdrant_cfg.get("port", 6333)
        collection_name = qdrant_cfg.get("collection_name", "rag_documents")

        # Build Qdrant client URL
        host = str(host)
        if host.startswith("http://") or host.startswith("https://"):
            qdrant_url = f"{host}:{port}"
        else:
            qdrant_url = f"http://{host}:{port}"
        qdrant_client = QdrantClient(url=qdrant_url)

        # Explicit debug printout for verification
        print(
            f"[VectorizerConversative] Using Qdrant URL: {qdrant_url} | Collection: {collection_name}"
        )

        # Choose embedding model from config to match indexed vectors
        embedding_default = (
            cfg.get("embedding", {}).get("default_model") or "text-embedding-ada-002"
        )

        # Generate embedding
        embedding_response = client.embeddings.create(
            model=embedding_default,
            input=query,
        )
        query_vector = embedding_response.data[0].embedding

        # Perform vector search
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k or 5,
            score_threshold=score_threshold,
            with_payload=True,
        )

        if not results:
            return f"No relevant documents found for '{query}' in collection '{collection_name}'"

        # Format response conservatively with citations
        out = []
        out.append(
            f"QDRANT SEARCH RESULTS (Collection: {collection_name}, TopK: {top_k}, Threshold: {score_threshold})\n"
        )
        for i, r in enumerate(results, 1):
            payload = r.payload or {}
            text = (
                payload.get("chunk_text")
                or payload.get("text")
                or payload.get("content")
                or payload.get("page_content")
                or ""
            )
            filename = payload.get("filename") or payload.get("source") or "Unknown"
            page = (
                payload.get("page")
                or payload.get("page_number")
                or payload.get("page_info")
                or "-"
            )
            out.append(f"Result {i} (score={getattr(r, 'score', 0):.3f})\n")
            out.append(f"Source: {filename} | Page: {page}\n")
            out.append(f"Content:\n{text}\n")
            out.append("-" * 80 + "\n")

        return "".join(out)

    except Exception as e:
        return f"Error in vectorizer_conversative_search: {str(e)}"


@function_schema
def document_search(
    query: str,
    collection_name: str = "rag_documents",
    top_k: Optional[int] = 5,
    score_threshold: Optional[float] = 0.7,
) -> str:
    """
    DOCUMENT SEARCH TOOL

    Use this tool to search through processed documents using vector similarity.
    Perfect for RAG (Retrieval-Augmented Generation) workflows where you need to find
    relevant document chunks to answer user questions.

    Args:
        query: The search query to find relevant document chunks
        collection_name: Name of the Qdrant collection containing documents (default: 'rag_documents')
        top_k: Number of most relevant chunks to retrieve (default: 5)
        score_threshold: Minimum similarity score for results (default: 0.7)

    EXAMPLES:
        Example: document_search("What is machine learning?")
        Example: document_search("AI applications in healthcare", "medical_docs", 3, 0.8)
        Example: document_search("transformer architecture", "research_papers", 10, 0.6)

    Returns:
        Formatted string with relevant document chunks and their metadata
    """

    try:
        from qdrant_client import QdrantClient

        # Get environment variables with fallbacks
        QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
        QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")

        # Initialize Qdrant client
        qdrant_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
        qdrant_client = QdrantClient(url=qdrant_url)

        # Generate embedding for the query
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small", input=query  # Using newer, better model
        )
        query_vector = embedding_response.data[0].embedding

        # Perform vector search
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )

        # Handle no results
        if not search_results:
            return f"No relevant documents found for query: '{query}' in collection '{collection_name}' with score threshold {score_threshold}"

        # Format results for RAG usage
        result_text = f"DOCUMENT SEARCH RESULTS for '{query}':\n"
        result_text += (
            f"Collection: {collection_name} | Found: {len(search_results)} chunks\n"
        )
        result_text += "=" * 80 + "\n\n"

        for i, result in enumerate(search_results, 1):
            payload = result.payload or {}
            score = result.score

            result_text += f"📄 CHUNK {i} (Similarity: {score:.3f})\n"
            result_text += "-" * 40 + "\n"

            # Extract common document metadata
            filename = payload.get(
                "filename", payload.get("source", "Unknown Document")
            )
            chunk_text = payload.get(
                "text",
                payload.get(
                    "content", payload.get("page_content", "No content available")
                ),
            )
            page_number = payload.get("page", payload.get("page_number", "Unknown"))
            chunk_id = payload.get("chunk_id", payload.get("id", f"chunk_{i}"))

            result_text += f"📁 Source: {filename}\n"
            result_text += f"📖 Page: {page_number}\n"
            result_text += f"🔗 Chunk ID: {chunk_id}\n"
            result_text += f"📝 Content:\n{chunk_text}\n"
            result_text += "\n" + "=" * 80 + "\n\n"

        return result_text

    except ImportError:
        return "Error: Qdrant client not installed. Please install with: pip install qdrant-client"
    except Exception as e:
        return f"Error searching documents: {str(e)}"


@function_schema
def document_metadata_search(
    filename: Optional[str] = None,
    date_range: Optional[dict] = None,
    collection_name: str = "rag_documents",
    limit: Optional[int] = 10,
) -> str:
    """
    DOCUMENT METADATA SEARCH TOOL

    Search documents by metadata filters (filename, upload date, etc.) without using vector similarity.
    Useful for finding specific documents or filtering by document properties.

    Args:
        filename: Filter by specific filename (partial matches supported)
        date_range: Filter by date range, e.g., {"start": "2024-01-01", "end": "2024-12-31"}
        collection_name: Name of the Qdrant collection (default: 'rag_documents')
        limit: Maximum number of documents to return (default: 10)

    EXAMPLES:
        Example: document_metadata_search(filename="research_paper.pdf")
        Example: document_metadata_search(date_range={"start": "2024-01-01", "end": "2024-06-30"})
        Example: document_metadata_search(filename="AI", limit=5)

    Returns:
        List of documents matching the metadata criteria
    """

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models

        # Get environment variables
        QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
        QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")

        # Initialize Qdrant client
        qdrant_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
        qdrant_client = QdrantClient(url=qdrant_url)

        # Build filters
        filters = []

        if filename:
            # Use partial match for filename
            filters.append(
                models.FieldCondition(
                    key="filename", match=models.MatchText(text=filename)
                )
            )

        # Note: Date filtering would require proper date field setup in Qdrant
        # This is a placeholder for future implementation
        if date_range:
            # Would need to implement date range filtering based on your date field structure
            pass

        # Perform scroll search (metadata-only search)
        if filters:
            filter_condition = models.Filter(must=filters)
        else:
            filter_condition = None

        scroll_result = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=limit,
            with_payload=True,
        )

        points = scroll_result[0]  # scroll returns (points, next_page_offset)

        if not points:
            return f"No documents found matching the criteria in collection '{collection_name}'"

        # Format results
        result_text = f"DOCUMENT METADATA SEARCH RESULTS:\n"
        result_text += (
            f"Collection: {collection_name} | Found: {len(points)} documents\n"
        )
        result_text += "=" * 80 + "\n\n"

        for i, point in enumerate(points, 1):
            payload = point.payload or {}

            result_text += f"📄 DOCUMENT {i}\n"
            result_text += "-" * 40 + "\n"

            filename = payload.get(
                "filename", payload.get("source", "Unknown Document")
            )
            upload_date = payload.get(
                "upload_date", payload.get("created_at", "Unknown Date")
            )
            file_size = payload.get("file_size", "Unknown Size")
            chunk_count = payload.get("chunk_count", "Unknown")

            result_text += f"📁 Filename: {filename}\n"
            result_text += f"📅 Upload Date: {upload_date}\n"
            result_text += f"📊 File Size: {file_size}\n"
            result_text += f"🔢 Chunks: {chunk_count}\n"
            result_text += f"🆔 Point ID: {point.id}\n"
            result_text += "\n" + "=" * 80 + "\n\n"

        return result_text

    except ImportError:
        return "Error: Qdrant client not installed. Please install with: pip install qdrant-client"
    except Exception as e:
        return f"Error searching document metadata: {str(e)}"


@function_schema
def arlo_api(query: str) -> str:
    """
    Use this tool to ask questions to the Arlo customer support agent.
    """
    url = "https://elevaite-arlocb-api.iopex.ai/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "message": query,
        "session_id": "3973740a-404d-4924-9cf4-c71cf9ffd219",
        "user_id": "Jojo",
        "chat_history": [
            {"actor": "user", "content": "Hello"},
            {"actor": "assistant", "content": "How are you"},
        ],
        "enable_web_search": True,
        "fetched_knowledge": "",
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()["response"]


# ==================== SERVICENOW ITSM TOOL ====================

@function_schema
def ServiceNow_ITSM(
    operation: str,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = "3",
    impact: Optional[str] = "3",
    urgency: Optional[str] = "3",
    category: Optional[str] = "inquiry",
    subcategory: Optional[str] = None,
    assignment_group: Optional[str] = None,
    assigned_to: Optional[str] = None,
    caller_id: Optional[str] = None,
    location: Optional[str] = None,
    business_service: Optional[str] = None,
    cmdb_ci: Optional[str] = None,
    contact_type: Optional[str] = "phone",
    sys_id: Optional[str] = None,
    identifier: Optional[str] = None,
    identifier_type: Optional[str] = "sys_id",
    state: Optional[str] = None,
    work_notes: Optional[str] = None,
    close_notes: Optional[str] = None
) -> str:
    """
    SERVICENOW ITSM (IT SERVICE MANAGEMENT) TOOL

    This tool provides comprehensive ServiceNow ITSM incident management capabilities.
    It handles creating, reading, and updating incidents in ServiceNow through a single interface.
    The tool determines the specific action based on the 'operation' parameter.

    OPERATIONS SUPPORTED:
    1. "create" - Create a new incident
    2. "read" or "get" - Retrieve an existing incident
    3. "update" - Update an existing incident

    OPERATION: CREATE
    Use when users report IT issues, outages, or service disruptions.
    Required: operation="create", short_description
    Optional: description, priority, impact, urgency, category, subcategory, assignment_group, assigned_to, caller_id, location, business_service, cmdb_ci, contact_type

    OPERATION: READ/GET
    Use when users ask about incident status or need incident details.
    Required: operation="read" or "get", identifier (sys_id or incident number)
    Optional: identifier_type ("sys_id" or "number")

    OPERATION: UPDATE
    Use when updating incident status, adding notes, or modifying incident details.
    Required: operation="update", sys_id
    Optional: short_description, description, priority, impact, urgency, state, work_notes, close_notes

    IMPORTANT FOR UPDATES: To update an incident, you MUST have the sys_id (not the incident number).
    If you only have the incident number (e.g., INC0000123), you must FIRST use operation="read"
    with the incident number to get the sys_id, then use that sys_id for the update operation.

    UPDATE WORKFLOW:
    1. Get incident number from user (e.g., "INC0000123")
    2. Use operation="read", identifier="INC0000123", identifier_type="number" to get incident details
    3. Extract the sys_id from the response
    4. Use operation="update", sys_id="extracted_sys_id" with your update parameters

    PRIORITY GUIDELINES:
    - "1" (Critical): Complete service outage affecting multiple users
    - "2" (High): Significant impact on business operations
    - "3" (Moderate): Standard issues with workarounds available
    - "4" (Low): Minor issues or enhancement requests
    - "5" (Planning): Future planning items

    IMPACT GUIDELINES:
    - "1" (High): Affects large number of users or critical business functions
    - "2" (Medium): Affects department or specific business function
    - "3" (Low): Affects individual user or non-critical function

    URGENCY GUIDELINES:
    - "1" (High): Immediate attention required
    - "2" (Medium): Response needed within business hours
    - "3" (Low): Can be addressed in normal queue

    ⚠️  CRITICAL: SERVICENOW PRIORITY AUTO-CALCULATION MATRIX ⚠️
    ServiceNow automatically calculates Priority based on Impact + Urgency combination.
    Setting priority alone will NOT work - it will be overridden by the system.

    To achieve a specific priority, use these Impact + Urgency combinations:

    FOR CRITICAL PRIORITY (1): impact="1" + urgency="1"
    FOR HIGH PRIORITY (2): impact="1" + urgency="2" OR impact="2" + urgency="1"
    FOR MODERATE PRIORITY (3): impact="2" + urgency="2" OR impact="3" + urgency="1"
    FOR LOW PRIORITY (4): impact="2" + urgency="3" OR impact="3" + urgency="2"
    FOR PLANNING PRIORITY (5): impact="3" + urgency="3"

    Complete Matrix:
    Impact 1 (High) + Urgency 1 (High) = Priority 1 (Critical)
    Impact 1 (High) + Urgency 2 (Medium) = Priority 2 (High)
    Impact 2 (Medium) + Urgency 1 (High) = Priority 2 (High)
    Impact 2 (Medium) + Urgency 2 (Medium) = Priority 3 (Moderate)
    Impact 2 (Medium) + Urgency 3 (Low) = Priority 4 (Low)
    Impact 3 (Low) + Urgency 1 (High) = Priority 3 (Moderate)
    Impact 3 (Low) + Urgency 2 (Medium) = Priority 4 (Low)
    Impact 3 (Low) + Urgency 3 (Low) = Priority 5 (Planning)

    STATE VALUES (for updates):
    - "1" (New): Newly created incident
    - "2" (In Progress): Work has started on the incident
    - "3" (On Hold): Incident is temporarily paused
    - "6" (Resolved): Issue has been resolved
    - "7" (Closed): Incident is closed and complete

    EXAMPLES:

    Create incident:
    operation="create", short_description="Email server down", description="Users cannot access email", impact="2", urgency="2"

    Get incident by number:
    operation="read", identifier="INC0000123", identifier_type="number"

    Get incident by sys_id:
    operation="get", identifier="a1b2c3d4e5f6789012345678901234567890abcd", identifier_type="sys_id"

    Update incident to Critical priority (CORRECT WAY):
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", impact="1", urgency="1", work_notes="Escalating to critical priority"

    Update incident to High priority (CORRECT WAY):
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", impact="1", urgency="2", work_notes="Setting to high priority"

    Update incident status:
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", state="2", work_notes="Started investigating the issue"

    Close incident:
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", state="6", close_notes="Issue resolved by restarting email service"

    Update incident using incident number (two-step process):
    Step 1: operation="read", identifier="INC0000123", identifier_type="number"
    Step 2: operation="update", sys_id="sys_id_from_step1_response", state="2", work_notes="Started working on this"
    """

    # Validate operation parameter
    if operation.lower() not in ["create", "read", "get", "update"]:
        return json.dumps({
            "success": False,
            "message": f"Invalid operation: {operation}. Must be 'create', 'read', 'get', or 'update'",
            "error": "Invalid operation parameter"
        }, indent=2)

    # Handle CREATE operation
    if operation.lower() == "create":
        if not short_description:
            return json.dumps({
                "success": False,
                "message": "short_description is required for create operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_itsm_create_incident(
            short_description=short_description,
            description=description,
            priority=priority,
            impact=impact,
            urgency=urgency,
            category=category,
            subcategory=subcategory,
            assignment_group=assignment_group,
            assigned_to=assigned_to,
            caller_id=caller_id,
            location=location,
            business_service=business_service,
            cmdb_ci=cmdb_ci,
            contact_type=contact_type
        )
        return json.dumps(result, indent=2)

    # Handle READ/GET operation
    elif operation.lower() in ["read", "get"]:
        if not identifier:
            return json.dumps({
                "success": False,
                "message": "identifier is required for read/get operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_itsm_get_incident(
            identifier=identifier,
            identifier_type=identifier_type or "sys_id"
        )
        return json.dumps(result, indent=2)

    # Handle UPDATE operation
    elif operation.lower() == "update":
        if not sys_id:
            return json.dumps({
                "success": False,
                "message": "sys_id is required for update operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_itsm_update_incident(
            sys_id=sys_id,
            short_description=short_description,
            description=description,
            priority=priority,
            impact=impact,
            urgency=urgency,
            state=state,
            work_notes=work_notes,
            close_notes=close_notes
        )
        return json.dumps(result, indent=2)


# ==================== SERVICENOW CSM TOOL ====================

@function_schema
def ServiceNow_CSM(
    operation: str,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = "4",
    impact: Optional[str] = "3",
    urgency: Optional[str] = "3",
    category: Optional[str] = "inquiry",
    subcategory: Optional[str] = None,
    assignment_group: Optional[str] = None,
    assigned_to: Optional[str] = None,
    contact: Optional[str] = None,
    consumer: Optional[str] = None,
    account: Optional[str] = None,
    contact_type: Optional[str] = "phone",
    origin: Optional[str] = "phone",
    escalation: Optional[str] = "0",
    sys_id: Optional[str] = None,
    identifier: Optional[str] = None,
    identifier_type: Optional[str] = "sys_id",
    state: Optional[str] = None,
    work_notes: Optional[str] = None,
    close_notes: Optional[str] = None
) -> str:
    """
    SERVICENOW CSM (CUSTOMER SERVICE MANAGEMENT) TOOL

    This tool provides comprehensive ServiceNow CSM case management capabilities.
    It handles creating, reading, and updating customer service cases in ServiceNow through a single interface.
    The tool determines the specific action based on the 'operation' parameter.

    OPERATIONS SUPPORTED:
    1. "create" - Create a new case
    2. "read" or "get" - Retrieve an existing case
    3. "update" - Update an existing case

    OPERATION: CREATE
    Use when customers contact support with questions, issues, or service requests.
    Required: operation="create", short_description
    Optional: description, priority, impact, urgency, category, subcategory, assignment_group, assigned_to, contact, consumer, account, contact_type, origin, escalation

    OPERATION: READ/GET
    Use when customers ask about case status or need case details.
    Required: operation="read" or "get", identifier (sys_id or case number)
    Optional: identifier_type ("sys_id" or "number")

    OPERATION: UPDATE
    Use when updating case status, adding notes, escalating, or modifying case details.
    Required: operation="update", sys_id
    Optional: short_description, description, priority, impact, urgency, state, work_notes, close_notes, escalation

    IMPORTANT FOR UPDATES: To update a case, you MUST have the sys_id (not the case number).
    If you only have the case number (e.g., CS0000123), you must FIRST use operation="read"
    with the case number to get the sys_id, then use that sys_id for the update operation.

    UPDATE WORKFLOW:
    1. Get case number from user (e.g., "CS0000123")
    2. Use operation="read", identifier="CS0000123", identifier_type="number" to get case details
    3. Extract the sys_id from the response
    4. Use operation="update", sys_id="extracted_sys_id" with your update parameters

    PRIORITY GUIDELINES:
    - "1" (Critical): Urgent customer issue affecting business operations
    - "2" (High): Important customer issue requiring prompt attention
    - "3" (Moderate): Standard customer inquiry or request
    - "4" (Low): General questions or minor requests

    IMPACT GUIDELINES:
    - "1" (High): Affects large number of customers or critical business functions
    - "2" (Medium): Affects specific customer segment or business function
    - "3" (Low): Affects individual customer or non-critical function

    URGENCY GUIDELINES:
    - "1" (High): Immediate attention required
    - "2" (Medium): Response needed within business hours
    - "3" (Low): Can be addressed in normal queue

    STATE VALUES (for updates):
    - "1" (Open): Case is open and awaiting action
    - "2" (Work in Progress): Work has started on the case
    - "3" (Resolved): Issue has been resolved
    - "4" (Closed): Case is closed and complete

    ESCALATION LEVELS:
    - "0" (Normal): Standard case handling
    - "1" (Manager): Escalated to management level
    - "2" (Executive): Escalated to executive level

    ORIGIN TYPES:
    - "phone": Customer called support
    - "email": Customer sent email
    - "web": Customer used web portal
    - "walk-in": Customer visited in person
    - "chat": Customer used chat support

    EXAMPLES:

    Create case:
    operation="create", short_description="Billing inquiry", description="Customer has questions about charges", priority="3", category="billing", origin="email"

    Get case by number:
    operation="read", identifier="CS0000123", identifier_type="number"

    Get case by sys_id:
    operation="get", identifier="a1b2c3d4e5f6789012345678901234567890abcd", identifier_type="sys_id"

    Update case status:
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", state="2", work_notes="Started investigating customer issue"

    Escalate case:
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", escalation="1", work_notes="Escalating to manager due to customer request"

    Close case:
    operation="update", sys_id="a1b2c3d4e5f6789012345678901234567890abcd", state="3", close_notes="Customer issue resolved successfully"

    Update case using case number (two-step process):
    Step 1: operation="read", identifier="CS0000123", identifier_type="number"
    Step 2: operation="update", sys_id="sys_id_from_step1_response", state="2", work_notes="Started investigating customer issue"
    """

    # Validate operation parameter
    if operation.lower() not in ["create", "read", "get", "update"]:
        return json.dumps({
            "success": False,
            "message": f"Invalid operation: {operation}. Must be 'create', 'read', 'get', or 'update'",
            "error": "Invalid operation parameter"
        }, indent=2)

    # Handle CREATE operation
    if operation.lower() == "create":
        if not short_description:
            return json.dumps({
                "success": False,
                "message": "short_description is required for create operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_csm_create_case(
            short_description=short_description,
            description=description,
            priority=priority,
            impact=impact,
            urgency=urgency,
            category=category,
            subcategory=subcategory,
            assignment_group=assignment_group,
            assigned_to=assigned_to,
            contact=contact,
            consumer=consumer,
            account=account,
            contact_type=contact_type,
            origin=origin,
            escalation=escalation
        )
        return json.dumps(result, indent=2)

    # Handle READ/GET operation
    elif operation.lower() in ["read", "get"]:
        if not identifier:
            return json.dumps({
                "success": False,
                "message": "identifier is required for read/get operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_csm_get_case(
            identifier=identifier,
            identifier_type=identifier_type or "sys_id"
        )
        return json.dumps(result, indent=2)

    # Handle UPDATE operation
    elif operation.lower() == "update":
        if not sys_id:
            return json.dumps({
                "success": False,
                "message": "sys_id is required for update operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = servicenow_csm_update_case(
            sys_id=sys_id,
            short_description=short_description,
            description=description,
            priority=priority,
            impact=impact,
            urgency=urgency,
            state=state,
            work_notes=work_notes,
            close_notes=close_notes,
            escalation=escalation
        )
        return json.dumps(result, indent=2)


# ==================== SALESFORCE CSM TOOL ====================

@function_schema
def Salesforce_CSM(
    operation: str,
    status: Optional[str] = "New",
    case_origin: Optional[str] = "Email",
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    account_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    email_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    case_sub_type: Optional[str] = None,
    case_type: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = "Medium",
    case_reason: Optional[str] = None,
    symptoms: Optional[str] = None,
    rootcause: Optional[str] = None,
    ux_version: Optional[str] = None,
    case_summary: Optional[str] = None,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    internal_comments: Optional[str] = None,
    web_email: Optional[str] = None,
    web_company: Optional[str] = None,
    web_name: Optional[str] = None,
    web_phone: Optional[str] = None,
    case_id: Optional[str] = None,
    identifier: Optional[str] = None,
    identifier_type: Optional[str] = "case_id"
) -> str:
    """
    SALESFORCE CSM (CUSTOMER SERVICE MANAGEMENT) TOOL

    This tool provides comprehensive Salesforce CSM case management capabilities.
    It handles creating, reading, and updating customer service cases in Salesforce through a single interface.
    The tool determines the specific action based on the 'operation' parameter.

    OPERATIONS SUPPORTED:
    1. "create" - Create a new case
    2. "read" or "get" - Retrieve an existing case
    3. "update" - Update an existing case

    OPERATION: CREATE
    Use when customers contact support with questions, issues, or service requests.
    Required: operation="create", first_name, last_name
    STRONGLY RECOMMENDED: email_address (helps find existing contacts and avoid duplicates)
    Optional: status, case_origin, account_id, contact_id, contact_phone, case_sub_type, case_type, type, priority, case_reason, symptoms, rootcause, ux_version, case_summary, subject, description, internal_comments, web_email, web_company, web_name, web_phone

    OPERATION: READ/GET
    Use when customers ask about case status or need case details.
    Required: operation="read" or "get", identifier (Salesforce case ID or case number)
    Optional: identifier_type ("case_id" or "case_number")

    OPERATION: UPDATE
    Use when updating case status, adding notes, escalating, or modifying case details.
    Required: operation="update", case_id (Salesforce case ID)
    Optional: status, priority, case_reason, symptoms, rootcause, case_summary, subject, description, internal_comments, case_sub_type, case_type, type, ux_version

    IMPORTANT FOR CASE CREATION: Always include email_address when creating cases as it helps:
    - Find existing contacts and avoid duplicates
    - Link cases to the correct customer records
    - Prevent DUPLICATES_DETECTED errors

    IMPORTANT FOR UPDATES: To update a case, you MUST have the Salesforce case_id (not the case number).
    If you only have the case number (e.g., 00001234), you must FIRST use operation="read"
    with the case number to get the case_id, then use that case_id for the update operation.

    UPDATE WORKFLOW:
    1. Get case number from user (e.g., "00001234")
    2. Use operation="read", identifier="00001234", identifier_type="case_number" to get case details
    3. Extract the case_id from the response
    4. Use operation="update", case_id="extracted_case_id" with your update parameters

    STATUS VALUES:
    - "New": Case is newly created and awaiting assignment
    - "In Progress": Work has started on the case
    - "Escalated": Case has been escalated to higher level support
    - "On Hold": Case is temporarily on hold waiting for customer or internal response
    - "Closed": Case is resolved and closed

    PRIORITY VALUES:
    - "High": Urgent customer issue requiring immediate attention
    - "Medium": Standard customer inquiry or request (default)
    - "Low": General questions or minor requests

    CASE ORIGIN VALUES:
    - "Email": Customer sent email (default)
    - "Phone": Customer called support
    - "Web": Customer used web portal
    - "Chat": Customer used chat support
    - "Social Media": Customer contacted via social media

    CASE TYPE VALUES:
    - "Problem": Technical issue or bug
    - "Question": General inquiry
    - "Feature Request": Request for new functionality

    CASE REASON VALUES:
    - "Bug": Software defect or error
    - "Enhancement": Request for improvement
    - "Question": General inquiry
    - "Complaint": Customer complaint

    EXAMPLES:

    Create case (ALWAYS include email_address when available):
    operation="create", first_name="John", last_name="Smith", email_address="john.smith@company.com", case_origin="Email", priority="High", case_reason="Bug", subject="Login issue", description="User cannot log into the application"

    NOTE: All operations return a case_link field containing a direct URL to view the case in Salesforce.

    Get case by case number:
    operation="read", identifier="00001234", identifier_type="case_number"

    Get case by Salesforce case ID:
    operation="get", identifier="5001234567890AB", identifier_type="case_id"

    Update case status:
    operation="update", case_id="5001234567890AB", status="In Progress", internal_comments="Started investigating the login issue"

    Close case with resolution:
    operation="update", case_id="5001234567890AB", status="Closed", rootcause="Fixed JavaScript authentication bug", internal_comments="Issue resolved and deployed to production"

    Update case using case number (two-step process):
    Step 1: operation="read", identifier="00001234", identifier_type="case_number"
    Step 2: operation="update", case_id="case_id_from_step1_response", status="In Progress", internal_comments="Started working on customer issue"
    """

    # Validate operation parameter
    if operation.lower() not in ["create", "read", "get", "update"]:
        return json.dumps({
            "success": False,
            "message": f"Invalid operation: {operation}. Must be 'create', 'read', 'get', or 'update'",
            "error": "Invalid operation parameter"
        }, indent=2)

    # Handle CREATE operation
    if operation.lower() == "create":
        if not first_name or not last_name:
            return json.dumps({
                "success": False,
                "message": "first_name and last_name are required for create operation",
                "error": "Missing required parameters"
            }, indent=2)

        result = salesforce_csm_create_case(
            status=status,
            case_origin=case_origin,
            first_name=first_name,
            last_name=last_name,
            account_id=account_id,
            contact_id=contact_id,
            email_address=email_address,
            contact_phone=contact_phone,
            case_sub_type=case_sub_type,
            case_type=case_type,
            type=type,
            priority=priority,
            case_reason=case_reason,
            symptoms=symptoms,
            rootcause=rootcause,
            ux_version=ux_version,
            case_summary=case_summary,
            subject=subject,
            description=description,
            internal_comments=internal_comments,
            web_email=web_email,
            web_company=web_company,
            web_name=web_name,
            web_phone=web_phone
        )
        return json.dumps(result, indent=2)

    # Handle READ/GET operation
    elif operation.lower() in ["read", "get"]:
        if not identifier:
            return json.dumps({
                "success": False,
                "message": "identifier is required for read/get operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = salesforce_csm_get_case(
            identifier=identifier,
            identifier_type=identifier_type or "case_id"
        )
        return json.dumps(result, indent=2)

    # Handle UPDATE operation
    elif operation.lower() == "update":
        if not case_id:
            return json.dumps({
                "success": False,
                "message": "case_id is required for update operation",
                "error": "Missing required parameter"
            }, indent=2)

        result = salesforce_csm_update_case(
            case_id=case_id,
            status=status,
            priority=priority,
            case_reason=case_reason,
            symptoms=symptoms,
            rootcause=rootcause,
            case_summary=case_summary,
            subject=subject,
            description=description,
            internal_comments=internal_comments,
            case_sub_type=case_sub_type,
            case_type=case_type,
            type=type,
            ux_version=ux_version
        )
        return json.dumps(result, indent=2)


tool_store = {
    "add_numbers": add_numbers,
    "weather_forecast": weather_forecast,
    "url_to_markdown": url_to_markdown,
    "web_search": web_search,
    "get_customer_order": get_customer_order,
    "get_customer_location": get_customer_location,
    "add_customer": add_customer,
    "print_to_console": print_to_console,
    "query_retriever2": query_retriever2,
    "media_context_retriever": media_context_retriever,
    "redis_cache_operation": redis_cache_operation,
    "postgres_query": postgres_query,
    "image_generation": image_generation,
    "create_insertion_order": create_insertion_order,
    "create_salesforce_insertion_order": create_salesforce_insertion_order,
    "get_salesforce_accounts": get_salesforce_accounts,
    "get_salesforce_opportunities": get_salesforce_opportunities,
    "get_salesforce_opportunities_by_account": get_salesforce_opportunities_by_account,
    # RAG and Document Search Tools
    "document_search": document_search,
    "document_metadata_search": document_metadata_search,
    "vectorizer_conversative_search": vectorizer_conversative_search,
    # Backward compatibility aliases for renamed functions
    "qdrant_search": media_context_retriever,  # Alias for backward compatibility
    "query_retriever": query_retriever,
    "customer_query_retriever": customer_query_retriever,
    "sql_database": sql_database,
    "arlo_api": arlo_api,
    # ServiceNow Tools
    "ServiceNow_ITSM": ServiceNow_ITSM,
    "ServiceNow_CSM": ServiceNow_CSM,
    # Salesforce Tools
    "Salesforce_CSM": Salesforce_CSM,
    # Mitie Tools
    "extract_rfq_json": extract_rfq_json,
    "extract_rfq_from_snow_agent": extract_rfq_from_snow_agent,
    "calculate_mitie_quote": calculate_mitie_quote,
    "generate_mitie_pdf": generate_mitie_pdf,
}



# Kevel Tools
@function_schema
def kevel_get_sites() -> str:
    """
    Get all available sites from Kevel network 11679.

    This tool retrieves all sites configured in the Kevel network that can be used
    for ad placement. Each site has a unique ID and name that you'll need for generating ad code.

    Returns:
        str: JSON string containing list of sites with their IDs, names, and domains

    Example response:
        {
            "success": true,
            "sites": [
                {"Id": 123, "Name": "My Website", "Domain": "example.com"},
                {"Id": 124, "Name": "Mobile Site", "Domain": "m.example.com"}
            ]
        }
    """
    try:
        if not KEVEL_API_KEY:
            return json.dumps({
                "success": False,
                "message": "Kevel API key not configured",
                "error": "Missing KEVEL_API_KEY in environment variables"
            })

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json"
        }

        # Try different possible endpoints for sites
        endpoints_to_try = [
            f"{KEVEL_API_BASE}/site",
            f"{KEVEL_API_BASE}/network/{KEVEL_NETWORK_ID}/site",
            f"{KEVEL_API_BASE}/advertiser/site"
        ]

        last_error = None
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )

                # Log the response for debugging
                print(f"🔍 KEVEL SITES API Response: Endpoint={endpoint}, Status={response.status_code}, Content={response.text[:500]}...")

                if response.status_code == 200:
                    break
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                last_error = str(e)
                continue
        else:
            # If we get here, all endpoints failed
            return json.dumps({
                "success": False,
                "message": "Failed to retrieve sites from all attempted endpoints",
                "error": f"Last error: {last_error}",
                "attempted_endpoints": endpoints_to_try
            })

        if response.status_code == 200:
            sites = response.json()
            return json.dumps({
                "success": True,
                "message": f"Retrieved {len(sites)} sites from network {KEVEL_NETWORK_ID}",
                "sites": sites
            })
        else:
            return json.dumps({
                "success": False,
                "message": f"Failed to retrieve sites: HTTP {response.status_code}",
                "error": response.text
            })

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error connecting to Kevel API",
            "error": str(e)
        })


@function_schema
def kevel_get_ad_types() -> str:
    """
    Get all available ad types (sizes) from Kevel network 11679 with unique element IDs.

    This tool retrieves all ad types/sizes configured in the Kevel network and generates
    unique element IDs for each ad type that can be used in HTML ad placements.
    Ad types define the dimensions and format of ad placements (e.g., 300x250, 728x90).
    You'll need the ad type ID and element ID for generating ad code.

    Returns:
        str: JSON string containing list of ad types with their IDs, names, dimensions, and unique element IDs

    Example response:
        {
            "success": true,
            "ad_types": [
                {
                    "Id": 5,
                    "Name": "Medium Rectangle",
                    "Width": 300,
                    "Height": 250,
                    "element_id": "azk12345"
                },
                {
                    "Id": 6,
                    "Name": "Leaderboard",
                    "Width": 728,
                    "Height": 90,
                    "element_id": "azk67890"
                }
            ]
        }
    """
    try:
        import uuid

        if not KEVEL_API_KEY:
            return json.dumps({
                "success": False,
                "message": "Kevel API key not configured",
                "error": "Missing KEVEL_API_KEY in environment variables"
            })

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{KEVEL_API_BASE}/adtypes",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            response_data = response.json()

            # Extract the items array from the response
            if isinstance(response_data, dict) and "items" in response_data:
                ad_types = response_data["items"]
            else:
                ad_types = response_data  # Fallback for direct array response

            # Add unique element IDs to each ad type
            for ad_type in ad_types:
                # Generate unique element ID using uuid (first 8 characters)
                unique_id = str(uuid.uuid4())[:8]
                ad_type["element_id"] = f"azk{unique_id}"

            return json.dumps({
                "success": True,
                "message": f"Retrieved {len(ad_types)} ad types from network {KEVEL_NETWORK_ID} with unique element IDs",
                "ad_types": ad_types
            })
        else:
            return json.dumps({
                "success": False,
                "message": f"Failed to retrieve ad types: HTTP {response.status_code}",
                "error": response.text
            })

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error connecting to Kevel API",
            "error": str(e)
        })


@function_schema
def kevel_debug_api() -> str:
    """
    Debug tool to explore Kevel API endpoints and help troubleshoot connectivity issues.

    This tool tests various API endpoints to help identify the correct API structure
    and diagnose connectivity issues with the Kevel API.

    Returns:
        str: JSON string containing debug information about API endpoints
    """
    try:
        if not KEVEL_API_KEY:
            return json.dumps({
                "success": False,
                "message": "Kevel API key not configured",
                "error": "Missing KEVEL_API_KEY in environment variables"
            })

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json"
        }

        # Test various endpoints
        endpoints_to_test = [
            "/",
            "/network",
            f"/network/{KEVEL_NETWORK_ID}",
            "/site",
            f"/network/{KEVEL_NETWORK_ID}/site",
            "/adtype",
            f"/network/{KEVEL_NETWORK_ID}/adtype",
            "/advertiser",
            "/channel"
        ]

        results = []
        for endpoint in endpoints_to_test:
            try:
                url = f"{KEVEL_API_BASE}{endpoint}"
                response = requests.get(url, headers=headers, timeout=5)
                results.append({
                    "endpoint": endpoint,
                    "url": url,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_size": len(response.text),
                    "error": None if response.status_code == 200 else response.text[:200]
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "url": f"{KEVEL_API_BASE}{endpoint}",
                    "status_code": None,
                    "success": False,
                    "response_size": 0,
                    "error": str(e)
                })

        return json.dumps({
            "success": True,
            "message": f"Tested {len(endpoints_to_test)} endpoints",
            "api_base": KEVEL_API_BASE,
            "network_id": KEVEL_NETWORK_ID,
            "results": results
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Error during API debug",
            "error": str(e)
        })


# Add Kevel tools to the tool_store dictionary
tool_store.update({
    "kevel_get_sites": kevel_get_sites,
    "kevel_get_ad_types": kevel_get_ad_types,
    "kevel_debug_api": kevel_debug_api,
})




tool_schemas = {
    "add_numbers": add_numbers.openai_schema,
    "weather_forecast": weather_forecast.openai_schema,
    "url_to_markdown": url_to_markdown.openai_schema,
    "web_search": web_search.openai_schema,
    "get_customer_order": get_customer_order.openai_schema,
    "get_customer_location": get_customer_location.openai_schema,
    "add_customer": add_customer.openai_schema,
    "print_to_console": print_to_console.openai_schema,
    "query_retriever2": query_retriever2.openai_schema,
    "media_context_retriever": media_context_retriever.openai_schema,
    "redis_cache_operation": redis_cache_operation.openai_schema,
    "postgres_query": postgres_query.openai_schema,
    "image_generation": image_generation.openai_schema,
    "create_insertion_order": create_insertion_order.openai_schema,
    "create_salesforce_insertion_order": create_salesforce_insertion_order.openai_schema,
    "get_salesforce_accounts": get_salesforce_accounts.openai_schema,
    "get_salesforce_opportunities": get_salesforce_opportunities.openai_schema,
    "get_salesforce_opportunities_by_account": get_salesforce_opportunities_by_account.openai_schema,
    # RAG and Document Search Tools
    "document_search": document_search.openai_schema,
    "document_metadata_search": document_metadata_search.openai_schema,
    "vectorizer_conversative_search": vectorizer_conversative_search.openai_schema,
    # Backward compatibility aliases for renamed functions
    "qdrant_search": media_context_retriever.openai_schema,  # Alias for backward compatibility
    "query_retriever": query_retriever.openai_schema,
    "customer_query_retriever": customer_query_retriever.openai_schema,
    "sql_database": sql_database.openai_schema,
    "arlo_api": arlo_api.openai_schema,
    # ServiceNow Tools
    "ServiceNow_ITSM": ServiceNow_ITSM.openai_schema,
    "ServiceNow_CSM": ServiceNow_CSM.openai_schema,
    # Salesforce Tools
    "Salesforce_CSM": Salesforce_CSM.openai_schema,
    # Mitie Tools
    "extract_rfq_json": extract_rfq_json.openai_schema,
    "extract_rfq_from_snow_agent": extract_rfq_from_snow_agent.openai_schema,
    "calculate_mitie_quote": calculate_mitie_quote.openai_schema,
    "generate_mitie_pdf": generate_mitie_pdf.openai_schema,
    # Kevel Tools
    "kevel_get_sites": kevel_get_sites.openai_schema,
    "kevel_get_ad_types": kevel_get_ad_types.openai_schema,
}
