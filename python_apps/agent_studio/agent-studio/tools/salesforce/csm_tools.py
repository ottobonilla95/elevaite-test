import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from the agent studio .env file
current_dir = os.path.dirname(__file__)
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(env_path)

# Salesforce CSM API base URL
SALESFORCE_CSM_API_BASE = os.getenv("SALESFORCE_CSM_API_URL", "http://localhost:8092")


def salesforce_csm_create_case(
    status: str = "New",
    case_origin: str = "Email",
    first_name: str = "",
    last_name: str = "",
    account_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    email_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    case_sub_type: Optional[str] = None,
    case_type: Optional[str] = None,
    type: Optional[str] = None,
    priority: str = "Medium",
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
    web_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Salesforce CSM case using the Salesforce CSM API.
    
    This tool allows agents to create customer service cases in Salesforce with comprehensive
    case details, contact information, and technical specifications.
    
    Args:
        status (str): Case status - "New", "In Progress", "Escalated", "On Hold", "Closed" (default: "New")
        case_origin (str): How the case was created - "Email", "Phone", "Web", "Chat", "Social Media" (required)
        first_name (str): Contact's first name for case creation (required)
        last_name (str): Contact's last name for case creation (required)
        account_id (str, optional): Salesforce Account ID if linking to existing account
        contact_id (str, optional): Salesforce Contact ID if linking to existing contact
        email_address (str, optional): Contact's email address
        contact_phone (str, optional): Contact's phone number
        case_sub_type (str, optional): Case subcategory for classification
        case_type (str, optional): Case type - "Email", "Phone", "Chat", etc.
        type (str, optional): General case type - "Problem", "Question", "Feature Request"
        priority (str): Case priority - "High", "Medium", "Low" (default: "Medium")
        case_reason (str, optional): Reason for case - "Bug", "Enhancement", "Question", "Complaint"
        symptoms (str, optional): Brief description of symptoms (max 100 chars)
        rootcause (str, optional): Root cause analysis (max 250 chars)
        ux_version (str, optional): Application/UX version information (max 50 chars)
        case_summary (str, optional): Detailed case summary (max 2000 chars)
        subject (str, optional): Case subject line
        description (str, optional): Detailed case description
        internal_comments (str, optional): Internal notes for case handlers
        web_email (str, optional): Web form email if different from contact email
        web_company (str, optional): Company name from web form
        web_name (str, optional): Full name from web form
        web_phone (str, optional): Phone number from web form
    
    Returns:
        Dict[str, Any]: Created case details including case ID, case number, and all field values
    
    Example:
        result = salesforce_csm_create_case(
            status="New",
            case_origin="Email",
            first_name="John",
            last_name="Smith",
            email_address="john.smith@company.com",
            priority="High",
            case_reason="Bug",
            subject="Login issue",
            description="User cannot log into the application",
            symptoms="Login button unresponsive"
        )
    """
    try:
        # Prepare the payload
        payload = {
            "status": status,
            "case_origin": case_origin,
            "first_name": first_name,
            "last_name": last_name,
            "priority": priority
        }
        
        # Add optional fields if provided
        if account_id:
            payload["account_id"] = account_id
        if contact_id:
            payload["contact_id"] = contact_id
        if email_address:
            payload["email_address"] = email_address
        if contact_phone:
            payload["contact_phone"] = contact_phone
        if case_sub_type:
            payload["case_sub_type"] = case_sub_type
        if case_type:
            payload["case_type"] = case_type
        if type:
            payload["type"] = type
        if case_reason:
            payload["case_reason"] = case_reason
        if symptoms:
            payload["symptoms"] = symptoms
        if rootcause:
            payload["rootcause"] = rootcause
        if ux_version:
            payload["ux_version"] = ux_version
        if case_summary:
            payload["case_summary"] = case_summary
        if subject:
            payload["subject"] = subject
        if description:
            payload["description"] = description
        if internal_comments:
            payload["internal_comments"] = internal_comments
        if web_email:
            payload["web_email"] = web_email
        if web_company:
            payload["web_company"] = web_company
        if web_name:
            payload["web_name"] = web_name
        if web_phone:
            payload["web_phone"] = web_phone
        
        # Make API call to Salesforce CSM API
        response = requests.post(
            f"{SALESFORCE_CSM_API_BASE}/cases",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 201:
            return {
                "success": True,
                "message": "Case created successfully",
                "data": response.json()
            }
        elif response.status_code == 400:
            return {
                "success": False,
                "message": "Invalid case data provided",
                "error": response.text
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
            "message": "Failed to connect to Salesforce CSM API",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Unexpected error occurred",
            "error": str(e)
        }


def salesforce_csm_get_case(
    identifier: str,
    identifier_type: str = "case_id"
) -> Dict[str, Any]:
    """
    Retrieve a Salesforce CSM case by case ID or case number.
    
    This tool allows agents to fetch detailed information about an existing case
    using either the unique Salesforce case ID or the human-readable case number.
    
    Args:
        identifier (str): The case identifier (Salesforce case ID like 5001234567890AB or case number like 00001234)
        identifier_type (str): Type of identifier - "case_id" or "case_number" (default: "case_id")
    
    Returns:
        Dict[str, Any]: Case details including all fields, status, and contact information
    
    Example:
        # Get by Salesforce case ID
        result = salesforce_csm_get_case("5001234567890AB", "case_id")
        
        # Get by case number
        result = salesforce_csm_get_case("00001234", "case_number")
    """
    try:
        # Determine the endpoint based on identifier type
        if identifier_type.lower() == "case_number":
            endpoint = f"{SALESFORCE_CSM_API_BASE}/cases/number/{identifier}"
        else:
            endpoint = f"{SALESFORCE_CSM_API_BASE}/cases/{identifier}"
        
        # Make API call to Salesforce CSM API
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
            "message": "Failed to connect to Salesforce CSM API",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Unexpected error occurred",
            "error": str(e)
        }


def salesforce_csm_update_case(
    case_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    case_reason: Optional[str] = None,
    symptoms: Optional[str] = None,
    rootcause: Optional[str] = None,
    case_summary: Optional[str] = None,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    internal_comments: Optional[str] = None,
    case_sub_type: Optional[str] = None,
    case_type: Optional[str] = None,
    type: Optional[str] = None,
    ux_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Salesforce CSM case.

    This tool allows agents to modify case details, change status, update priority,
    add internal comments, and update technical information for existing cases.

    Args:
        case_id (str): The unique Salesforce case ID (required, format: 5001234567890AB)
        status (str, optional): Updated case status - "New", "In Progress", "Escalated", "On Hold", "Closed"
        priority (str, optional): Updated priority - "High", "Medium", "Low"
        case_reason (str, optional): Updated reason - "Bug", "Enhancement", "Question", "Complaint"
        symptoms (str, optional): Updated symptoms description (max 100 chars)
        rootcause (str, optional): Updated root cause analysis (max 250 chars)
        case_summary (str, optional): Updated detailed case summary (max 2000 chars)
        subject (str, optional): Updated case subject line
        description (str, optional): Updated detailed case description
        internal_comments (str, optional): Additional internal notes for case handlers
        case_sub_type (str, optional): Updated case subcategory
        case_type (str, optional): Updated case type
        type (str, optional): Updated general case type - "Problem", "Question", "Feature Request"
        ux_version (str, optional): Updated application/UX version (max 50 chars)

    Returns:
        Dict[str, Any]: Updated case details

    Example:
        # Update case status and add internal comments
        result = salesforce_csm_update_case(
            case_id="5001234567890AB",
            status="In Progress",
            internal_comments="Started investigating the login issue"
        )

        # Close case with resolution
        result = salesforce_csm_update_case(
            case_id="5001234567890AB",
            status="Closed",
            rootcause="Fixed JavaScript authentication bug",
            internal_comments="Issue resolved and deployed to production"
        )

        # Escalate case priority
        result = salesforce_csm_update_case(
            case_id="5001234567890AB",
            priority="High",
            internal_comments="Escalating due to customer impact"
        )
    """
    try:
        # Prepare the payload with only provided fields
        payload = {}
        
        if status:
            payload["status"] = status
        if priority:
            payload["priority"] = priority
        if case_reason:
            payload["case_reason"] = case_reason
        if symptoms:
            payload["symptoms"] = symptoms
        if rootcause:
            payload["rootcause"] = rootcause
        if case_summary:
            payload["case_summary"] = case_summary
        if subject:
            payload["subject"] = subject
        if description:
            payload["description"] = description
        if internal_comments:
            payload["internal_comments"] = internal_comments
        if case_sub_type:
            payload["case_sub_type"] = case_sub_type
        if case_type:
            payload["case_type"] = case_type
        if type:
            payload["type"] = type
        if ux_version:
            payload["ux_version"] = ux_version

        # Make API call to Salesforce CSM API
        response = requests.put(
            f"{SALESFORCE_CSM_API_BASE}/cases/{case_id}",
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
                "message": f"Case not found: {case_id}",
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
            "message": "Failed to connect to Salesforce CSM API",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Unexpected error occurred",
            "error": str(e)
        }
