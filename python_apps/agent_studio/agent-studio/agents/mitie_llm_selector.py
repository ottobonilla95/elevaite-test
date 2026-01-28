#!/usr/bin/env python3
"""
Mitie LLM Item Selector - Uses LLM to intelligently select relevant items from available configurations
"""

import json
import openai
from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from mitie_context_provider import get_all_available_mitie_configs

def select_relevant_mitie_items(rfq_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to intelligently select relevant items from available Mitie configurations.
    
    Args:
        rfq_data: Extracted RFQ data containing scope, project type, etc.
        
    Returns:
        Dictionary containing selected items with quantities and justifications
    """
    try:
        # Get all available configurations
        available_configs = get_all_available_mitie_configs()
        
        # Prepare the LLM prompt
        prompt = f"""
You are a Mitie telecommunications infrastructure cost estimator. Based on the RFQ scope and available rate card items, select the most relevant items for this project.

RFQ DETAILS:
- Project Type: {rfq_data.get('project_type', 'Unknown')}
- Client: {rfq_data.get('client_name', 'Unknown')}
- Site Location: {rfq_data.get('site_postcode', 'Unknown')}
- Technical Scope: {rfq_data.get('technical_scope', '')}
- Scope Items: {rfq_data.get('technical_specs', {}).get('scope', [])}

AVAILABLE CONFIGURATIONS:
{available_configs}

TASK:
Analyze the RFQ scope and select relevant items from the available configurations. For each selected item, provide:
1. The exact item code/key from the available configurations
2. Estimated quantity needed
3. Brief justification for selection

PROJECT TYPE GUIDANCE:
- ROOFTOP PROJECTS: Select only power, lighting, enclosures, and preliminaries. DO NOT select towers, monopoles, or steel configurations.
- MONOPOLE PROJECTS: Select appropriate Elara/monopole items, steel configurations, plus power/lighting as needed.
- LATTICE TOWER PROJECTS: Select appropriate steel configurations, plus power/lighting as needed.

SELECTION CRITERIA:
- Power supply: Select if scope mentions power, electrical, or equipment connections
- Lighting: Select if scope mentions lighting, illumination, or rooftop lighting
- Access/Lifting: Select if scope mentions crane, cherry picker, lifting, or height work
- Steel/Towers: Select ONLY if scope explicitly mentions tower installation, monopole installation, lattice tower, or mast erection
- Preferred Supplier Items: Select ONLY if scope explicitly mentions specific products (Elara, TSC, Lancaster) or tower/monopole installation
- Regional Uplift: Determine based on postcode
- Risk Level: Assess based on scope complexity (standard/moderate/critical)

IMPORTANT RULES:
- DO NOT select tower/monopole items for rooftop-only projects
- DO NOT select steel configurations unless towers/monopoles are explicitly mentioned
- Select only ONE preferred supplier item per product type (Elara, TSC, Lancaster) and ONLY when relevant
- For rooftop projects: focus on power, lighting, enclosures, and preliminaries only
- Choose the most appropriate height/specification match
- Prefer new items over refurbished unless cost is a specific concern

RESPONSE FORMAT:
Return ONLY a valid JSON object (no comments, no markdown, no explanations). Use actual numeric values from the available configurations:

{{
    "selected_rate_items": [
        {{
            "code": "11.16",
            "description": "Provide power supply to new equipment/enclosure",
            "rate": 806.12,
            "unit": "Nr",
            "quantity": 1,
            "justification": "Power connection mentioned in scope"
        }}
    ],
    "selected_preferred_items": [
        {{
            "description": "Elara 20m Medium monopole",
            "product_type": "Elara",
            "rate": 12500.0,
            "quantity": 1,
            "justification": "Elara monopole specified in scope"
        }}
    ],
    "selected_steel_config": {{
        "key": "30m_lattice",
        "height": "30m",
        "tower_type": "lattice",
        "tonnage": 12.0,
        "rate_per_tonne": 1200.0,
        "justification": "30m lattice tower specified"
    }},
    "regional_uplift": {{
        "region": "remote_rural",
        "uplift_percentage": 15.0,
        "justification": "IV24 postcode is Scottish Highlands"
    }},
    "risk_assessment": {{
        "level": "critical",
        "justification": "Remote location, helicopter access required"
    }},
    "project_classification": {{
        "type": "mixed",
        "justification": "Both active and passive components"
    }}
}}

IMPORTANT:
- Use ONLY numeric values from the available configurations
- NO comments in JSON (// not allowed)
- NO placeholder text like "estimated_tonnage"
- NO markdown formatting
- Return raw JSON only
"""

        # Call OpenAI API
        client = openai.OpenAI()
        # print(f"INPUT TO THE SELECTOR: {prompt}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional telecommunications infrastructure cost estimator with expertise in Mitie rate cards and project scoping."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        # Parse the response
        llm_response = response.choices[0].message.content
        
        # Extract JSON from the response
        try:
            # Remove markdown formatting if present
            if "```json" in llm_response:
                start_marker = "```json"
                end_marker = "```"
                start_idx = llm_response.find(start_marker) + len(start_marker)
                end_idx = llm_response.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = llm_response[start_idx:end_idx].strip()
                else:
                    json_str = llm_response[start_idx:].strip()
            else:
                # Find JSON in the response
                start_idx = llm_response.find('{')
                end_idx = llm_response.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = llm_response[start_idx:end_idx]
                else:
                    raise ValueError("No JSON found in LLM response")

            # Remove any comments from JSON (// comments)
            import re
            json_str = re.sub(r'//.*', '', json_str)  # Remove // comments
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # Remove /* */ comments

            # Parse the cleaned JSON
            selected_items = json.loads(json_str)
            # print(f"OUTPUT OF THE SELECTOR: {selected_items}")
            return selected_items
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse LLM response as JSON: {e}")
            print(f"LLM Response: {llm_response}")
            return _get_fallback_selection(rfq_data)
            
    except Exception as e:
        print(f"❌ Error in LLM item selection: {e}")
        return _get_fallback_selection(rfq_data)

def _get_fallback_selection(rfq_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback selection logic if LLM fails.
    """
    scope = str(rfq_data.get('technical_scope', '')).lower()
    
    fallback = {
        "selected_rate_items": [],
        "selected_preferred_items": [],
        "selected_steel_config": {},
        "regional_uplift": {"region": "standard", "uplift_percentage": 0, "justification": "fallback"},
        "risk_assessment": {"level": "standard", "justification": "fallback"},
        "project_classification": {"type": "mixed", "justification": "fallback"}
    }
    
    # Basic keyword matching as fallback
    if "power" in scope:
        fallback["selected_rate_items"].append({
            "code": "11.16",
            "description": "Provide power supply to new equipment/enclosure",
            "rate": 806.12,
            "unit": "Nr",
            "quantity": 1,
            "justification": "Power mentioned in scope"
        })
    
    if "lighting" in scope:
        fallback["selected_rate_items"].append({
            "code": "11.5", 
            "description": "Rooftop lighting scheme with LED luminaires",
            "rate": 1200.0,
            "unit": "Nr",
            "quantity": 1,
            "justification": "Lighting mentioned in scope"
        })
    
    return fallback

if __name__ == "__main__":
    # Test the selector
    test_rfq = {
        "project_type": "Monopole",
        "client_name": "ConnectTel UK",
        "site_postcode": "YO7 1DA",
        "technical_scope": "Supply of New Structure – Elara 20m Medium monopole Removal of Existing Structure",
        "technical_specs": {
            "scope": ["Supply of New Structure – Elara 20m Medium monopole", "Removal of Existing Structure"]
        }
    }
    
    result = select_relevant_mitie_items(test_rfq)
    print("🤖 LLM Selected Items:")
    print(json.dumps(result, indent=2))
