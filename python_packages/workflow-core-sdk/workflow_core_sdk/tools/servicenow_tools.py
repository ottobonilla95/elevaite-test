"""
ServiceNow Tools (ported from Agent Studio)

These tools interact with ServiceNow via the ServiceNow connector API.
Includes both ITSM (incident management) and CSM (case management) tools.

Environment variables:
- SERVICENOW_CONNECTOR_URL: Base URL for ServiceNow connector (default: http://localhost:8091)
"""

from __future__ import annotations

import os
import requests
import json
from typing import Optional

from .decorators import function_schema

# Config from environment
SERVICENOW_API_BASE = os.getenv("SERVICENOW_CONNECTOR_URL", "http://localhost:8091")


# ==================== ITSM Tools (Incident Management) ====================


@function_schema
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
    contact_type: Optional[str] = "phone",
) -> str:
    """
    Create a new ServiceNow incident.

    Args:
        short_description: Brief description of the incident (required, max 160 chars)
        description: Detailed description of the incident (max 4000 chars)
        priority: Priority level - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low, "5"=Planning (default: "3")
        impact: Business impact - "1"=High, "2"=Medium, "3"=Low (default: "3")
        urgency: Urgency level - "1"=High, "2"=Medium, "3"=Low (default: "3")
        category: Incident category (default: "inquiry")
        subcategory: Incident subcategory
        assignment_group: Assignment group name or sys_id
        assigned_to: Assigned user name or sys_id
        caller_id: Caller user name or sys_id
        location: Location name or sys_id
        business_service: Business service name or sys_id
        cmdb_ci: Configuration item name or sys_id
        contact_type: Contact method - "phone", "email", "walk-in", etc. (default: "phone")

    Returns:
        str: JSON string with created incident details including sys_id, number, and all field values
    """
    try:
        payload = {
            "short_description": short_description,
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
            "category": category,
            "contact_type": contact_type,
        }

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

        response = requests.post(
            f"{SERVICENOW_API_BASE}/incidents", json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Incident created successfully", "data": response.json()})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to create incident: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while creating incident: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Unexpected error while creating incident: {str(e)}", "error": str(e)})


@function_schema
def servicenow_itsm_get_incident(identifier: str, identifier_type: str = "sys_id") -> str:
    """
    Retrieve a ServiceNow incident by sys_id or incident number.

    Args:
        identifier: The incident identifier (sys_id or incident number like INC0000123)
        identifier_type: Type of identifier - "sys_id" or "number" (default: "sys_id")

    Returns:
        str: JSON string with incident details including all fields and current status
    """
    try:
        if identifier_type.lower() == "number":
            endpoint = f"{SERVICENOW_API_BASE}/incidents/search/{identifier}"
        else:
            endpoint = f"{SERVICENOW_API_BASE}/incidents/{identifier}"

        response = requests.get(endpoint, headers={"Content-Type": "application/json"}, timeout=30)

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Incident retrieved successfully", "data": response.json()})
        elif response.status_code == 404:
            return json.dumps({"success": False, "message": f"Incident not found: {identifier}", "error": "Incident not found"})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to retrieve incident: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while retrieving incident: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps(
            {"success": False, "message": f"Unexpected error while retrieving incident: {str(e)}", "error": str(e)}
        )


@function_schema
def servicenow_itsm_update_incident(
    sys_id: str,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    impact: Optional[str] = None,
    urgency: Optional[str] = None,
    state: Optional[str] = None,
    work_notes: Optional[str] = None,
    close_notes: Optional[str] = None,
) -> str:
    """
    Update an existing ServiceNow incident.

    Args:
        sys_id: The unique sys_id of the incident to update (required)
        short_description: Updated brief description (max 160 chars)
        description: Updated detailed description (max 4000 chars)
        priority: Updated priority - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low, "5"=Planning
        impact: Updated impact - "1"=High, "2"=Medium, "3"=Low
        urgency: Updated urgency - "1"=High, "2"=Medium, "3"=Low
        state: Updated state - "1"=New, "2"=In Progress, "3"=On Hold, "6"=Resolved, "7"=Closed
        work_notes: Work notes to add to the incident
        close_notes: Resolution notes when closing the incident

    Returns:
        str: JSON string with updated incident details
    """
    try:
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

        response = requests.put(
            f"{SERVICENOW_API_BASE}/incidents/{sys_id}", json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Incident updated successfully", "data": response.json()})
        elif response.status_code == 404:
            return json.dumps({"success": False, "message": f"Incident not found: {sys_id}", "error": "Incident not found"})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to update incident: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while updating incident: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Unexpected error while updating incident: {str(e)}", "error": str(e)})


# ==================== CSM Tools (Case Management) ====================


@function_schema
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
    escalation: Optional[str] = "0",
) -> str:
    """
    Create a new ServiceNow CSM case.

    Args:
        short_description: Brief description of the case (required, max 160 chars)
        description: Detailed description of the case (max 4000 chars)
        priority: Priority level - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low (default: "4")
        impact: Business impact - "1"=High, "2"=Medium, "3"=Low (default: "3")
        urgency: Urgency level - "1"=High, "2"=Medium, "3"=Low (default: "3")
        category: Case category (default: "inquiry")
        subcategory: Case subcategory
        assignment_group: Assignment group name or sys_id
        assigned_to: Assigned user name or sys_id
        contact: Contact/Customer user name or sys_id
        consumer: Consumer user name or sys_id
        account: Account name or sys_id
        contact_type: Contact method - "phone", "email", "web", etc. (default: "phone")
        origin: Case origin - "phone", "email", "web", "walk-in", etc. (default: "phone")
        escalation: Escalation level - "0"=Normal, "1"=Manager, "2"=Executive (default: "0")

    Returns:
        str: JSON string with created case details including sys_id, number, and all field values
    """
    try:
        payload = {
            "short_description": short_description,
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
            "category": category,
            "contact_type": contact_type,
            "origin": origin,
            "escalation": escalation,
        }

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

        response = requests.post(
            f"{SERVICENOW_API_BASE}/cases", json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Case created successfully", "data": response.json()})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to create case: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while creating case: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Unexpected error while creating case: {str(e)}", "error": str(e)})


@function_schema
def servicenow_csm_get_case(identifier: str, identifier_type: str = "sys_id") -> str:
    """
    Retrieve a ServiceNow CSM case by sys_id or case number.

    Args:
        identifier: The case identifier (sys_id or case number like CS0000123)
        identifier_type: Type of identifier - "sys_id" or "number" (default: "sys_id")

    Returns:
        str: JSON string with case details including all fields and current status
    """
    try:
        if identifier_type.lower() == "number":
            endpoint = f"{SERVICENOW_API_BASE}/cases/search/{identifier}"
        else:
            endpoint = f"{SERVICENOW_API_BASE}/cases/{identifier}"

        response = requests.get(endpoint, headers={"Content-Type": "application/json"}, timeout=30)

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Case retrieved successfully", "data": response.json()})
        elif response.status_code == 404:
            return json.dumps({"success": False, "message": f"Case not found: {identifier}", "error": "Case not found"})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to retrieve case: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while retrieving case: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Unexpected error while retrieving case: {str(e)}", "error": str(e)})


@function_schema
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
    escalation: Optional[str] = None,
) -> str:
    """
    Update an existing ServiceNow CSM case.

    Args:
        sys_id: The unique sys_id of the case to update (required)
        short_description: Updated brief description (max 160 chars)
        description: Updated detailed description (max 4000 chars)
        priority: Updated priority - "1"=Critical, "2"=High, "3"=Moderate, "4"=Low
        impact: Updated impact - "1"=High, "2"=Medium, "3"=Low
        urgency: Updated urgency - "1"=High, "2"=Medium, "3"=Low
        state: Updated state - "1"=Open, "2"=Work in Progress, "3"=Resolved, "4"=Closed
        work_notes: Work notes to add to the case
        close_notes: Resolution notes when closing the case
        escalation: Updated escalation level - "0"=Normal, "1"=Manager, "2"=Executive

    Returns:
        str: JSON string with updated case details
    """
    try:
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

        response = requests.put(
            f"{SERVICENOW_API_BASE}/cases/{sys_id}", json=payload, headers={"Content-Type": "application/json"}, timeout=30
        )

        if response.status_code == 200:
            return json.dumps({"success": True, "message": "Case updated successfully", "data": response.json()})
        elif response.status_code == 404:
            return json.dumps({"success": False, "message": f"Case not found: {sys_id}", "error": "Case not found"})
        else:
            return json.dumps(
                {"success": False, "message": f"Failed to update case: {response.status_code}", "error": response.text}
            )

    except requests.exceptions.RequestException as e:
        return json.dumps({"success": False, "message": f"Network error while updating case: {str(e)}", "error": str(e)})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Unexpected error while updating case: {str(e)}", "error": str(e)})


# Export store and schemas for aggregation in basic_tools
SERVICENOW_TOOL_STORE = {
    "servicenow_itsm_create_incident": servicenow_itsm_create_incident,
    "servicenow_itsm_get_incident": servicenow_itsm_get_incident,
    "servicenow_itsm_update_incident": servicenow_itsm_update_incident,
    "servicenow_csm_create_case": servicenow_csm_create_case,
    "servicenow_csm_get_case": servicenow_csm_get_case,
    "servicenow_csm_update_case": servicenow_csm_update_case,
}

SERVICENOW_TOOL_SCHEMAS = {name: func.openai_schema for name, func in SERVICENOW_TOOL_STORE.items()}
