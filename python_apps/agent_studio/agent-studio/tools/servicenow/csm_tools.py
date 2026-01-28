import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from the agent studio .env file
current_dir = os.path.dirname(__file__)
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(env_path)

# ServiceNow connector API base URL
SERVICENOW_API_BASE = os.getenv("SERVICENOW_CONNECTOR_URL", "http://localhost:8091")


def servicenow_csm_create_case(
    short_description: str,
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
    escalation: Optional[str] = "0"
) -> Dict[str, Any]:
    """
    Create a new ServiceNow CSM case using the ServiceNow connector API.
    
    This tool allows agents to create customer service cases in ServiceNow with comprehensive details.
    The case will be automatically assigned a unique case number and sys_id.
    
    Args:
        short_description (str): Brief description of the case (required, max 160 chars)
        description (str, optional): Detailed description of the case (max 4000 chars)
        priority (str, optional): Priority level - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low (default: "4")
        impact (str, optional): Business impact - "1"=High, "2"=Medium, "3"=Low (default: "3")
        urgency (str, optional): Urgency level - "1"=High, "2"=Medium, "3"=Low (default: "3")
        category (str, optional): Case category (default: "inquiry")
        subcategory (str, optional): Case subcategory
        assignment_group (str, optional): Assignment group name or sys_id
        assigned_to (str, optional): Assigned user name or sys_id
        contact (str, optional): Contact/Customer user name or sys_id
        consumer (str, optional): Consumer user name or sys_id
        account (str, optional): Account name or sys_id
        contact_type (str, optional): Contact method - "phone", "email", "web", etc. (default: "phone")
        origin (str, optional): Case origin - "phone", "email", "web", "walk-in", etc. (default: "phone")
        escalation (str, optional): Escalation level - "0"=Normal, "1"=Manager, "2"=Executive (default: "0")
    
    Returns:
        Dict[str, Any]: Created case details including sys_id, number, and all field values
    
    Example:
        result = servicenow_csm_create_case(
            short_description="Customer billing inquiry",
            description="Customer has questions about recent charges",
            priority="3",
            category="billing",
            contact="john.doe@company.com",
            origin="email"
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
            "contact_type": contact_type,
            "origin": origin,
            "escalation": escalation
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
        if contact:
            payload["contact"] = contact
        if consumer:
            payload["consumer"] = consumer
        if account:
            payload["account"] = account
        
        # Make API call to ServiceNow connector
        response = requests.post(
            f"{SERVICENOW_API_BASE}/cases",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Case created successfully",
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to create case: {response.status_code}",
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while creating case: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while creating case: {str(e)}",
            "error": str(e)
        }


def servicenow_csm_get_case(
    identifier: str,
    identifier_type: str = "sys_id"
) -> Dict[str, Any]:
    """
    Retrieve a ServiceNow CSM case by sys_id or case number.
    
    This tool allows agents to fetch detailed information about an existing case
    using either the unique sys_id or the human-readable case number.
    
    Args:
        identifier (str): The case identifier (sys_id or case number like CS0000123)
        identifier_type (str): Type of identifier - "sys_id" or "number" (default: "sys_id")
    
    Returns:
        Dict[str, Any]: Case details including all fields and current status
    
    Example:
        # Get by sys_id
        result = servicenow_csm_get_case("a1b2c3d4e5f6", "sys_id")
        
        # Get by case number
        result = servicenow_csm_get_case("CS0000123", "number")
    """
    try:
        # Determine the endpoint based on identifier type
        if identifier_type.lower() == "number":
            endpoint = f"{SERVICENOW_API_BASE}/cases/search/{identifier}"
        else:
            endpoint = f"{SERVICENOW_API_BASE}/cases/{identifier}"
        
        # Make API call to ServiceNow connector
        response = requests.get(
            endpoint,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Case retrieved successfully",
                "data": response.json()
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": f"Case not found: {identifier}",
                "error": "Case not found"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to retrieve case: {response.status_code}",
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while retrieving case: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while retrieving case: {str(e)}",
            "error": str(e)
        }


def servicenow_csm_update_case(
    sys_id: str,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    impact: Optional[str] = None,
    urgency: Optional[str] = None,
    state: Optional[str] = None,
    work_notes: Optional[str] = None,
    close_notes: Optional[str] = None,
    escalation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing ServiceNow CSM case.

    This tool allows agents to modify case details, change status, add work notes,
    escalate cases, and close cases with resolution notes.

    Args:
        sys_id (str): The unique sys_id of the case to update (required)
        short_description (str, optional): Updated brief description (max 160 chars)
        description (str, optional): Updated detailed description (max 4000 chars)
        priority (str, optional): Updated priority - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low
        impact (str, optional): Updated impact - "1"=High, "2"=Medium, "3"=Low
        urgency (str, optional): Updated urgency - "1"=High, "2"=Medium, "3"=Low
        state (str, optional): Updated state - "1"=Open, "2"=Work in Progress, "3"=Resolved, "4"=Closed
        work_notes (str, optional): Work notes to add to the case
        close_notes (str, optional): Resolution notes when closing the case
        escalation (str, optional): Updated escalation level - "0"=Normal, "1"=Manager, "2"=Executive

    Returns:
        Dict[str, Any]: Updated case details

    Example:
        # Update case status and add work notes
        result = servicenow_csm_update_case(
            sys_id="a1b2c3d4e5f6",
            state="2",
            work_notes="Started working on customer inquiry"
        )

        # Escalate case to manager level
        result = servicenow_csm_update_case(
            sys_id="a1b2c3d4e5f6",
            escalation="1",
            work_notes="Escalating to manager due to complexity"
        )

        # Close case with resolution
        result = servicenow_csm_update_case(
            sys_id="a1b2c3d4e5f6",
            state="3",
            close_notes="Customer inquiry resolved successfully"
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
        if escalation is not None:
            payload["escalation"] = escalation

        # Make API call to ServiceNow connector
        response = requests.put(
            f"{SERVICENOW_API_BASE}/cases/{sys_id}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Case updated successfully",
                "data": response.json()
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": f"Case not found: {sys_id}",
                "error": "Case not found"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to update case: {response.status_code}",
                "error": response.text
            }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Network error while updating case: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error while updating case: {str(e)}",
            "error": str(e)
        }
