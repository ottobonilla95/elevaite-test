import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from the agent studio .env file
current_dir = os.path.dirname(__file__)
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(env_path)

# ServiceNow connector API base URL
SERVICENOW_API_BASE = os.getenv("SERVICENOW_CONNECTOR_URL", "http://localhost:8091")


def servicenow_itsm_create_incident(
    short_description: str,
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
    contact_type: Optional[str] = "phone"
) -> Dict[str, Any]:
    """
    Create a new ServiceNow incident using the ServiceNow connector API.
    
    This tool allows agents to create incidents in ServiceNow with comprehensive details.
    The incident will be automatically assigned a unique incident number and sys_id.
    
    Args:
        short_description (str): Brief description of the incident (required, max 160 chars)
        description (str, optional): Detailed description of the incident (max 4000 chars)
        priority (str, optional): Priority level - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low, "5"=Planning (default: "3")
        impact (str, optional): Business impact - "1"=High, "2"=Medium, "3"=Low (default: "3")
        urgency (str, optional): Urgency level - "1"=High, "2"=Medium, "3"=Low (default: "3")
        category (str, optional): Incident category (default: "inquiry")
        subcategory (str, optional): Incident subcategory
        assignment_group (str, optional): Assignment group name or sys_id
        assigned_to (str, optional): Assigned user name or sys_id
        caller_id (str, optional): Caller user name or sys_id
        location (str, optional): Location name or sys_id
        business_service (str, optional): Business service name or sys_id
        cmdb_ci (str, optional): Configuration item name or sys_id
        contact_type (str, optional): Contact method - "phone", "email", "walk-in", etc. (default: "phone")
    
    Returns:
        Dict[str, Any]: Created incident details including sys_id, number, and all field values
    
    Example:
        result = servicenow_itsm_create_incident(
            short_description="Email server down",
            description="Users cannot access email services",
            priority="2",
            impact="2",
            urgency="2",
            category="software"
        )
    """
    try:
        # Prepare the payload
        payload = {
            "short_description": short_description,
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
            "category": category,
            "contact_type": contact_type
        }
        
        # Add optional fields if provided
        if description:
            payload["description"] = description
        if subcategory:
            payload["subcategory"] = subcategory
        if assignment_group:
            payload["assignment_group"] = assignment_group
        if assigned_to:
            payload["assigned_to"] = assigned_to
        if caller_id:
            payload["caller_id"] = caller_id
        if location:
            payload["location"] = location
        if business_service:
            payload["business_service"] = business_service
        if cmdb_ci:
            payload["cmdb_ci"] = cmdb_ci
        
        # Make API call to ServiceNow connector
        response = requests.post(
            f"{SERVICENOW_API_BASE}/incidents",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Incident created successfully",
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create incident: {response.status_code}",
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while creating incident: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while creating incident: {str(e)}",
            "error": str(e)
        }


def servicenow_itsm_get_incident(
    identifier: str,
    identifier_type: str = "sys_id"
) -> Dict[str, Any]:
    """
    Retrieve a ServiceNow incident by sys_id or incident number.
    
    This tool allows agents to fetch detailed information about an existing incident
    using either the unique sys_id or the human-readable incident number.
    
    Args:
        identifier (str): The incident identifier (sys_id or incident number like INC0000123)
        identifier_type (str): Type of identifier - "sys_id" or "number" (default: "sys_id")
    
    Returns:
        Dict[str, Any]: Incident details including all fields and current status
    
    Example:
        # Get by sys_id
        result = servicenow_itsm_get_incident("a1b2c3d4e5f6", "sys_id")
        
        # Get by incident number
        result = servicenow_itsm_get_incident("INC0000123", "number")
    """
    try:
        # Determine the endpoint based on identifier type
        if identifier_type.lower() == "number":
            endpoint = f"{SERVICENOW_API_BASE}/incidents/search/{identifier}"
        else:
            endpoint = f"{SERVICENOW_API_BASE}/incidents/{identifier}"
        
        # Make API call to ServiceNow connector
        response = requests.get(
            endpoint,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Incident retrieved successfully",
                "data": response.json()
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": f"Incident not found: {identifier}",
                "error": "Incident not found"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to retrieve incident: {response.status_code}",
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while retrieving incident: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while retrieving incident: {str(e)}",
            "error": str(e)
        }


def servicenow_itsm_update_incident(
    sys_id: str,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    impact: Optional[str] = None,
    urgency: Optional[str] = None,
    state: Optional[str] = None,
    work_notes: Optional[str] = None,
    close_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing ServiceNow incident.

    This tool allows agents to modify incident details, change status, add work notes,
    and close incidents with resolution notes.

    IMPORTANT: ServiceNow auto-calculates Priority based on Impact + Urgency.
    If you want a specific priority, set the appropriate impact and urgency values.

    Args:
        sys_id (str): The unique sys_id of the incident to update (required)
        short_description (str, optional): Updated brief description (max 160 chars)
        description (str, optional): Updated detailed description (max 4000 chars)
        priority (str, optional): Updated priority - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low, "5"=Planning
                                 NOTE: ServiceNow may override this based on impact + urgency
        impact (str, optional): Updated impact - "1"=High, "2"=Medium, "3"=Low
        urgency (str, optional): Updated urgency - "1"=High, "2"=Medium, "3"=Low
        state (str, optional): Updated state - "1"=New, "2"=In Progress, "3"=On Hold, "6"=Resolved, "7"=Closed
        work_notes (str, optional): Work notes to add to the incident
        close_notes (str, optional): Resolution notes when closing the incident

    Returns:
        Dict[str, Any]: Updated incident details

    Priority Calculation Matrix (Impact + Urgency = Priority):
        Impact 1 + Urgency 1 = Priority 1 (Critical)
        Impact 1 + Urgency 2 = Priority 2 (High)
        Impact 2 + Urgency 1 = Priority 2 (High)
        Impact 2 + Urgency 2 = Priority 3 (Moderate)
        Impact 3 + Urgency 2 = Priority 4 (Low)

    Example:
        # To set Priority to Critical (1), use Impact=1 and Urgency=1
        result = servicenow_itsm_update_incident(
            sys_id="a1b2c3d4e5f6",
            impact="1",
            urgency="1"  # This will result in Priority=1 (Critical)
        )

        # Update incident with work notes
        result = servicenow_itsm_update_incident(
            sys_id="a1b2c3d4e5f6",
            state="2",
            work_notes="Started investigating the issue"
        )
    """
    try:
        # Prepare the payload with only provided fields
        payload = {}

        if short_description is not None:
            payload["short_description"] = short_description
        if description is not None:
            payload["description"] = description
        if priority is not None:
            payload["priority"] = priority
        if impact is not None:
            payload["impact"] = impact
        if urgency is not None:
            payload["urgency"] = urgency
        if state is not None:
            payload["state"] = state
        if work_notes is not None:
            payload["work_notes"] = work_notes
        if close_notes is not None:
            payload["close_notes"] = close_notes
        
        # Make API call to ServiceNow connector
        response = requests.put(
            f"{SERVICENOW_API_BASE}/incidents/{sys_id}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Incident updated successfully",
                "data": response.json()
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": f"Incident not found: {sys_id}",
                "error": "Incident not found"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to update incident: {response.status_code}",
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while updating incident: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while updating incident: {str(e)}",
            "error": str(e)
        }
