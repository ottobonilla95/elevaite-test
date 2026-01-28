from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import logging
from simple_salesforce import Salesforce
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)


class CaseCreationRequest(BaseModel):
    # REQUIRED FIELDS
    status: str = "New"  # Status - Required picklist
    case_origin: str  # Origin - Required picklist (Email, Phone, Web, etc.)
    
    # NEW: CONTACT CREATION FIELDS
    first_name: str  # First name for contact/account creation
    last_name: str   # Last name for contact/account creation
    
    # LOOKUP RELATIONSHIPS 
    account_id: Optional[str] = None  # AccountId lookup
    contact_id: Optional[str] = None  # ContactId lookup
    
    # CONTACT INFORMATION
    email_address: Optional[EmailStr] = None  # Email_Address__c
    contact_phone: Optional[str] = None  # Contact_Phone__c
    
    # CASE CLASSIFICATION
    case_sub_type: Optional[str] = None  # Case_Sub_Type__c picklist
    case_type: Optional[str] = None      # Case_Type__c picklist
    type: Optional[str] = None           # Type picklist
    priority: str = "Medium"             # Priority picklist (default Medium)
    case_reason: Optional[str] = None    # Reason picklist
    
    # TECHNICAL INFORMATION
    symptoms: Optional[str] = None       # Symptoms__c (Text 100)
    rootcause: Optional[str] = None      # Rootcause__c (Text 250)
    ux_version: Optional[str] = None     # UX_Version__c (Text 50)
    
    # CASE DETAILS
    case_summary: Optional[str] = None   # Case_Summary__c (Long Text Area 2000)
    
    # DESCRIPTION INFORMATION
    subject: Optional[str] = None        # Subject (Text 255)
    description: Optional[str] = None    # Description (Long Text Area 32000)
    internal_comments: Optional[str] = None  # Comments (Text Area 4000)
    
    # WEB INFORMATION (Supplied fields)
    web_email: Optional[EmailStr] = None      # SuppliedEmail
    web_company: Optional[str] = None         # SuppliedCompany
    web_name: Optional[str] = None            # SuppliedName
    web_phone: Optional[str] = None           # SuppliedPhone
    
    class Config:
        schema_extra = {
            "example": {
                "status": "New",
                "case_origin": "Email",
                "first_name": "John",
                "last_name": "Smith",
                "account_id": "0011234567890AB",  
                "contact_id": "0031234567890AB", 
                "email_address": "john.smith@acme.com",
                "contact_phone": "+1-555-123-4567",
                "case_sub_type": "Default",
                "case_type": "Email",
                "type": "Problem",
                "priority": "Medium",
                "case_reason": "Bug",
                "symptoms": "Login Failed",
                "rootcause": "Javascript error",
                "ux_version": "v.212",
                "case_summary": "User unable to login",
                "subject": "Login button failed",
                "description": "Login button is unresponsive when clicked",
                "internal_comments": "Customer reported via email",
                "web_email": "user@example.com",
                "web_company": "Acme",
                "web_name": "John smith",
                "web_phone": "+1-555-987-6543"
            }
        }

class CaseUpdateRequest(BaseModel):
    # All fields optional for updates - only the fields you care about
    status: Optional[str] = None
    case_origin: Optional[str] = None
    
    # Lookup relationships
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    
    # Contact information
    email_address: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    
    # Case classification
    case_sub_type: Optional[str] = None
    case_type: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    case_reason: Optional[str] = None
    
    # Technical information
    symptoms: Optional[str] = None
    rootcause: Optional[str] = None
    ux_version: Optional[str] = None
    
    # Case details
    case_summary: Optional[str] = None
    
    # Description information
    subject: Optional[str] = None
    description: Optional[str] = None
    internal_comments: Optional[str] = None
    
    # Web information
    web_email: Optional[EmailStr] = None
    web_company: Optional[str] = None
    web_name: Optional[str] = None
    web_phone: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "In Progress",
                "priority": "High",
                "rootcause": "Identified JavaScript error in authentication module",
                "internal_comments": "Fix deployed to staging environment for testing"
            }
        }

class CaseResponse(BaseModel):
    id: str
    case_number: str
    status: str
    message: str
    case_link: str

class CaseCommentRequest(BaseModel):
    comment_body: str
    is_published: Optional[bool] = False  # True if visible to customer
    
    class Config:
        schema_extra = {
            "example": {
                "comment_body": "Customer confirmed the issue is resolved after applying the patch.",
                "is_published": True
            }
        }

# Simplified Salesforce Case connection manager
class SalesforceCaseManager:
    def __init__(self):
        self.sf = None
        self.connect()
    
    def connect(self):
        """Establish connection to Salesforce"""
        try:
            username = os.getenv('SALESFORCE_USERNAME')
            password = os.getenv('SALESFORCE_PASSWORD')
            security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
            domain = os.getenv('SALESFORCE_DOMAIN', 'test')  # Default to 'test' for sandbox
            
            logger.info(f"Attempting to connect with username: {username}")
            logger.info(f"Using domain: {domain}")
            
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain 
            )
            
            logger.info("Successfully connected to Salesforce")
            
            # Test the connection
            test_query = self.sf.query("SELECT Id FROM User LIMIT 1")
            logger.info(f"Connection test successful. Found {test_query['totalSize']} users")
            
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            self.sf = None
            
    def test_connection(self):
        """Test Salesforce connection"""
        if self.sf is None:
            return False
        try:
            result = self.sf.query("SELECT Id FROM User LIMIT 1")
            return True
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {str(e)}")
            return False

    def generate_case_link(self, case_id: str) -> str:
        """Generate a direct link to the Salesforce case"""
        base_url = os.getenv('SALESFORCE_BASE_URL', '')
        if not base_url:
            logger.warning("SALESFORCE_BASE_URL not configured, returning empty link")
            return ""

        # Construct the Lightning Experience case link
        case_link = f"{base_url}/lightning/r/Case/{case_id}/view"
        return case_link

    def is_valid_salesforce_id(self, id_value: str) -> bool:
        """Check if a string is a valid Salesforce ID (15 or 18 characters)"""
        if not id_value or id_value.lower() == "string" or len(id_value) < 15:
            return False
        return len(id_value) in [15, 18] and id_value.isalnum()
    
    def find_or_create_account(self, first_name: str, last_name: str, email: str = None) -> str:
        """Find existing account or create new one based on contact name and email"""
        try:
            account_name = f"{first_name} {last_name}"
            
            # First try to find existing account by name
            query = f"SELECT Id, Name FROM Account WHERE Name = '{account_name}' LIMIT 1"
            result = self.sf.query(query)
            
            if result['totalSize'] > 0:
                account_id = result['records'][0]['Id']
                logger.info(f"Found existing Account: {account_id} for {account_name}")
                return account_id
            
            # If email provided, also try to find account by looking for contacts with that email
            if email:
                contact_query = f"SELECT AccountId FROM Contact WHERE Email = '{email}' AND AccountId != NULL LIMIT 1"
                contact_result = self.sf.query(contact_query)
                
                if contact_result['totalSize'] > 0:
                    account_id = contact_result['records'][0]['AccountId']
                    logger.info(f"Found existing Account via Contact email: {account_id}")
                    return account_id
            
            # Create new Account
            account_data = {
                'Name': account_name,
                'Type': 'Customer'
            }
            
            if email:
                # Extract domain from email for account website
                domain = email.split('@')[1] if '@' in email else None
                if domain:
                    account_data['Website'] = f"https://www.{domain}"
            
            result = self.sf.Account.create(account_data)
            account_id = result['id']
            logger.info(f"Created new Account: {account_id} for {account_name}")
            
            return account_id
            
        except Exception as e:
            logger.error(f"Failed to find or create Account for {first_name} {last_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create Account: {str(e)}")
    
    def find_or_create_contact(self, first_name: str, last_name: str, email: str = None, phone: str = None, account_id: str = None) -> str:
        """Find existing contact or create new one"""
        try:
            # Try to find existing contact by email first (most reliable)
            if email:
                query = f"SELECT Id, FirstName, LastName, Email, AccountId FROM Contact WHERE Email = '{email}' LIMIT 1"
                result = self.sf.query(query)
                
                if result['totalSize'] > 0:
                    existing_contact = result['records'][0]
                    contact_id = existing_contact['Id']
                    
                    # If contact exists but doesn't have the right account, update it
                    if account_id and existing_contact.get('AccountId') != account_id:
                        logger.info(f"Updating existing Contact {contact_id} to link to Account {account_id}")
                        self.sf.Contact.update(contact_id, {'AccountId': account_id})
                    
                    logger.info(f"Found existing Contact by email: {contact_id}")
                    return contact_id
            
            # Try to find by name and account
            if account_id:
                query = f"SELECT Id FROM Contact WHERE FirstName = '{first_name}' AND LastName = '{last_name}' AND AccountId = '{account_id}' LIMIT 1"
                result = self.sf.query(query)
                
                if result['totalSize'] > 0:
                    contact_id = result['records'][0]['Id']
                    logger.info(f"Found existing Contact by name and account: {contact_id}")
                    return contact_id
            
            # Create new Contact
            contact_data = {
                'FirstName': first_name,
                'LastName': last_name
            }
            
            # IMPORTANT: Always link to the account
            if account_id:
                contact_data['AccountId'] = account_id
            
            if email:
                contact_data['Email'] = email
            
            if phone:
                contact_data['Phone'] = phone
            
            result = self.sf.Contact.create(contact_data)
            contact_id = result['id']
            logger.info(f"Created new Contact: {contact_id} for {first_name} {last_name} linked to Account: {account_id}")
            
            return contact_id
            
        except Exception as e:
            logger.error(f"Failed to find or create Contact for {first_name} {last_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create Contact: {str(e)}")
    
    def create_case(self, case_data: CaseCreationRequest):
        """Create a new Case in Salesforce with auto Account/Contact creation"""
        try:
            # Step 1: Handle Account/Contact creation or validation
            final_account_id = None
            final_contact_id = None
            
            # If account_id and contact_id are provided and valid, use them
            if (case_data.account_id and self.is_valid_salesforce_id(case_data.account_id) and 
                case_data.contact_id and self.is_valid_salesforce_id(case_data.contact_id)):
                final_account_id = case_data.account_id
                final_contact_id = case_data.contact_id
                logger.info(f"Using provided Account: {final_account_id} and Contact: {final_contact_id}")
            else:
                # Auto-create Account and Contact using first_name and last_name
                logger.info(f"Auto-creating Account and Contact for {case_data.first_name} {case_data.last_name}")
                
                # Create/find Account first
                final_account_id = self.find_or_create_account(
                    first_name=case_data.first_name,
                    last_name=case_data.last_name,
                    email=str(case_data.email_address) if case_data.email_address else None
                )
                
                # Create/find Contact with the Account
                final_contact_id = self.find_or_create_contact(
                    first_name=case_data.first_name,
                    last_name=case_data.last_name,
                    email=str(case_data.email_address) if case_data.email_address else None,
                    phone=case_data.contact_phone,
                    account_id=final_account_id
                )
            
            # Step 2: Create Case with final Account and Contact IDs
            sf_data = {}
            
            # REQUIRED FIELDS
            sf_data['Status'] = case_data.status
            sf_data['Origin'] = case_data.case_origin
            
            # LOOKUP RELATIONSHIPS - use final IDs
            sf_data['AccountId'] = final_account_id
            sf_data['ContactId'] = final_contact_id
            
            # CONTACT INFORMATION
            if case_data.email_address:
                sf_data['Email_Address__c'] = case_data.email_address
            if case_data.contact_phone:
                sf_data['Contact_Phone__c'] = case_data.contact_phone
            
            # CASE CLASSIFICATION
            if case_data.case_sub_type:
                sf_data['Case_Sub_Type__c'] = case_data.case_sub_type
            if case_data.case_type:
                sf_data['Case_Type__c'] = case_data.case_type
            if case_data.type:
                sf_data['Type'] = case_data.type
            sf_data['Priority'] = case_data.priority
            if case_data.case_reason:
                sf_data['Reason'] = case_data.case_reason
            
            # TECHNICAL INFORMATION
            if case_data.symptoms:
                sf_data['Symptoms__c'] = case_data.symptoms
            if case_data.rootcause:
                sf_data['Rootcause__c'] = case_data.rootcause
            if case_data.ux_version:
                sf_data['UX_Version__c'] = case_data.ux_version
            
            # CASE DETAILS
            if case_data.case_summary:
                sf_data['Case_Summary__c'] = case_data.case_summary
            
            # DESCRIPTION INFORMATION
            if case_data.subject:
                sf_data['Subject'] = case_data.subject
            if case_data.description:
                sf_data['Description'] = case_data.description
            if case_data.internal_comments:
                sf_data['Comments'] = case_data.internal_comments
            
            # WEB/SUPPLIED INFORMATION
            if case_data.web_email:
                sf_data['SuppliedEmail'] = case_data.web_email
            if case_data.web_company:
                sf_data['SuppliedCompany'] = case_data.web_company
            if case_data.web_name:
                sf_data['SuppliedName'] = case_data.web_name
            if case_data.web_phone:
                sf_data['SuppliedPhone'] = case_data.web_phone
            
            # Create the case
            result = self.sf.Case.create(sf_data)
            case_id = result['id']
            
            logger.info(f"Successfully created Case: {case_id} with Account: {final_account_id} and Contact: {final_contact_id}")
            
            # Return result with case number
            created_case = self.get_case(case_id)
            result['case_number'] = created_case.get('CaseNumber', 'Generated by Salesforce')
            result['account_id'] = final_account_id
            result['contact_id'] = final_contact_id
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Case: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create Case: {str(e)}")
    
    def update_case(self, case_id: str, case_data: CaseUpdateRequest):
        """Update an existing Case in Salesforce"""
        try:
            # Convert update request to Salesforce format
            sf_data = {}
            
            # Only include fields that are being updated (not None)
            if case_data.status is not None:
                sf_data['Status'] = case_data.status
            if case_data.case_origin is not None:
                sf_data['Origin'] = case_data.case_origin
            
            # Lookup relationships
            if case_data.account_id and self.is_valid_salesforce_id(case_data.account_id):
                sf_data['AccountId'] = case_data.account_id
            if case_data.contact_id and self.is_valid_salesforce_id(case_data.contact_id):
                sf_data['ContactId'] = case_data.contact_id
            
            # Contact information
            if case_data.email_address is not None:
                sf_data['Email_Address__c'] = case_data.email_address
            if case_data.contact_phone is not None:
                sf_data['Contact_Phone__c'] = case_data.contact_phone
            
            # Case classification
            if case_data.case_sub_type is not None:
                sf_data['Case_Sub_Type__c'] = case_data.case_sub_type
            if case_data.case_type is not None:
                sf_data['Case_Type__c'] = case_data.case_type
            if case_data.type is not None:
                sf_data['Type'] = case_data.type
            if case_data.priority is not None:
                sf_data['Priority'] = case_data.priority
            if case_data.case_reason is not None:
                sf_data['Reason'] = case_data.case_reason
            
            # Technical information
            if case_data.symptoms is not None:
                sf_data['Symptoms__c'] = case_data.symptoms
            if case_data.rootcause is not None:
                sf_data['Rootcause__c'] = case_data.rootcause
            if case_data.ux_version is not None:
                sf_data['UX_Version__c'] = case_data.ux_version
            
            # Case details
            if case_data.case_summary is not None:
                sf_data['Case_Summary__c'] = case_data.case_summary
            
            # Description information
            if case_data.subject is not None:
                sf_data['Subject'] = case_data.subject
            if case_data.description is not None:
                sf_data['Description'] = case_data.description
            if case_data.internal_comments is not None:
                sf_data['Comments'] = case_data.internal_comments
            
            # Web/Supplied information
            if case_data.web_email is not None:
                sf_data['SuppliedEmail'] = case_data.web_email
            if case_data.web_company is not None:
                sf_data['SuppliedCompany'] = case_data.web_company
            if case_data.web_name is not None:
                sf_data['SuppliedName'] = case_data.web_name
            if case_data.web_phone is not None:
                sf_data['SuppliedPhone'] = case_data.web_phone
            
            # Update the case
            result = self.sf.Case.update(case_id, sf_data)
            logger.info(f"Successfully updated Case: {case_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update Case: {str(e)}")
    
    def get_case(self, case_id: str):
        """Retrieve a Case from Salesforce with only the fields you care about"""
        try:
            # Query using only your specified fields
            query = f"""SELECT Id, CaseNumber, Subject, Description, Status, Priority, 
                               Type, Origin, CreatedDate, LastModifiedDate, Reason,
                               AccountId, Account.Name, ContactId, Contact.Name, OwnerId, Owner.Name,
                               Email_Address__c, Contact_Phone__c,
                               Case_Sub_Type__c, Case_Type__c,
                               Symptoms__c, Rootcause__c, UX_Version__c,
                               Case_Summary__c, Comments,
                               SuppliedEmail, SuppliedCompany, SuppliedName, SuppliedPhone,
                               IsEscalated, ClosedDate, ParentId
                        FROM Case 
                        WHERE Id = '{case_id}'"""
            
            result = self.sf.query(query)
            
            if result['totalSize'] == 0:
                raise HTTPException(status_code=404, detail="Case not found")
            
            return result['records'][0]
        except Exception as e:
            logger.error(f"Failed to retrieve Case {case_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="Case not found")
    
    def get_cases_by_account(self, account_id: str):
        """Get cases for a specific account"""
        try:
            query = f"""SELECT Id, CaseNumber, Subject, Status, Priority, Type, Origin,
                              CreatedDate, Contact.Name, Owner.Name, 
                              Case_Sub_Type__c, Case_Type__c, Case_Summary__c
                       FROM Case 
                       WHERE AccountId = '{account_id}'
                       ORDER BY CreatedDate DESC
                       LIMIT 1000"""
            result = self.sf.query(query)
            return result['records']
        except Exception as e:
            logger.error(f"Failed to get cases for account {account_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve cases for account")
    
    def get_cases_by_contact(self, contact_id: str):
        """Get cases for a specific contact"""
        try:
            query = f"""SELECT Id, CaseNumber, Subject, Status, Priority, Type, Origin,
                              CreatedDate, Account.Name, Owner.Name, 
                              Case_Sub_Type__c, Case_Type__c, Case_Summary__c
                       FROM Case 
                       WHERE ContactId = '{contact_id}'
                       ORDER BY CreatedDate DESC
                       LIMIT 1000"""
            result = self.sf.query(query)
            return result['records']
        except Exception as e:
            logger.error(f"Failed to get cases for contact {contact_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve cases for contact")
    
    def add_case_comment(self, case_id: str, comment_data: CaseCommentRequest):
        """Add a comment to a case"""
        try:
            sf_data = {
                'ParentId': case_id,
                'CommentBody': comment_data.comment_body,
                'IsPublished': comment_data.is_published
            }
            
            result = self.sf.CaseComment.create(sf_data)
            logger.info(f"Successfully added comment to Case: {case_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add comment to Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")
    
    def get_case_comments(self, case_id: str):
        """Get all comments for a case"""
        try:
            query = f"""SELECT Id, CommentBody, CreatedDate, CreatedBy.Name, IsPublished,
                               LastModifiedDate, LastModifiedBy.Name
                       FROM CaseComment 
                       WHERE ParentId = '{case_id}'
                       ORDER BY CreatedDate ASC"""
            result = self.sf.query(query)
            return result['records']
        except Exception as e:
            logger.error(f"Failed to get comments for Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve case comments")
    
    def escalate_case(self, case_id: str, escalation_reason: str = None):
        """Escalate a case"""
        try:
            sf_data = {
                'Priority': 'High',
                'IsEscalated': True
            }
            
            if escalation_reason:
                current_case = self.get_case(case_id)
                existing_comments = current_case.get('Comments', '')
                new_comments = f"ESCALATED: {escalation_reason}"
                if existing_comments:
                    new_comments = f"{existing_comments}\n\n{new_comments}"
                sf_data['Comments'] = new_comments
            
            result = self.sf.Case.update(case_id, sf_data)
            logger.info(f"Successfully escalated Case: {case_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to escalate Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to escalate Case: {str(e)}")
    
    def assign_case(self, case_id: str, new_owner_id: str, assignment_reason: str = None):
        """Assign case to a new owner"""
        try:
            if not self.is_valid_salesforce_id(new_owner_id):
                raise HTTPException(status_code=400, detail="Invalid Owner ID format")
            
            sf_data = {
                'OwnerId': new_owner_id
            }
            
            if assignment_reason:
                current_case = self.get_case(case_id)
                existing_comments = current_case.get('Comments', '')
                new_comments = f"REASSIGNED: {assignment_reason}"
                if existing_comments:
                    new_comments = f"{existing_comments}\n\n{new_comments}"
                sf_data['Comments'] = new_comments
            
            result = self.sf.Case.update(case_id, sf_data)
            logger.info(f"Successfully assigned Case {case_id} to owner {new_owner_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assign Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to assign Case: {str(e)}")
    
    def get_my_cases(self, user_id: str):
        """Get cases assigned to a specific user"""
        try:
            if not self.is_valid_salesforce_id(user_id):
                raise HTTPException(status_code=400, detail="Invalid User ID format")
            
            query = f"""SELECT Id, CaseNumber, Subject, Status, Priority, Type, Origin,
                              CreatedDate, Account.Name, Contact.Name, 
                              Case_Sub_Type__c, Case_Type__c, Case_Summary__c
                       FROM Case 
                       WHERE OwnerId = '{user_id}' AND Status != 'Closed'
                       ORDER BY Priority DESC, CreatedDate ASC"""
            result = self.sf.query(query)
            return result['records']
        except Exception as e:
            logger.error(f"Failed to get cases for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user cases")
    
    def get_related_cases(self, case_id: str):
        """Get related cases (child cases)"""
        try:
            query = f"""SELECT Id, CaseNumber, Subject, Status, Priority, Type,
                              CreatedDate, Owner.Name, Case_Summary__c
                       FROM Case 
                       WHERE ParentId = '{case_id}'
                       ORDER BY CreatedDate DESC"""
            result = self.sf.query(query)
            return result['records']
        except Exception as e:
            logger.error(f"Failed to get related cases for Case {case_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve related cases")