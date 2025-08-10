import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import pysnow
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ServiceNow Incident & CSM Case API",
    description="REST API for creating and managing ServiceNow incidents and CSM cases using PySnow",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation - INCIDENTS
class IncidentBase(BaseModel):
    short_description: str = Field(..., min_length=1, max_length=160, description="Brief description of the incident")
    description: Optional[str] = Field(None, max_length=4000, description="Detailed description of the incident")
    priority: Optional[str] = Field("3", description="Priority: 1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning")
    impact: Optional[str] = Field("3", description="Impact: 1=High, 2=Medium, 3=Low")
    urgency: Optional[str] = Field("3", description="Urgency: 1=High, 2=Medium, 3=Low")
    category: Optional[str] = Field("inquiry", description="Incident category")
    subcategory: Optional[str] = Field(None, description="Incident subcategory")
    assignment_group: Optional[str] = Field(None, description="Assignment group name or sys_id")
    assigned_to: Optional[str] = Field(None, description="Assigned user name or sys_id")
    caller_id: Optional[str] = Field(None, description="Caller user name or sys_id")
    location: Optional[str] = Field(None, description="Location name or sys_id")
    business_service: Optional[str] = Field(None, description="Business service name or sys_id")
    cmdb_ci: Optional[str] = Field(None, description="Configuration item name or sys_id")
    contact_type: Optional[str] = Field("phone", description="Contact type: phone, email, walk-in, etc.")

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    short_description: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=4000)
    priority: Optional[str] = Field(None, description="Priority: 1-5")
    impact: Optional[str] = Field(None, description="Impact: 1-3")
    urgency: Optional[str] = Field(None, description="Urgency: 1-3")
    state: Optional[str] = Field(None, description="State: 1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed")
    work_notes: Optional[str] = Field(None, description="Work notes to add")
    close_notes: Optional[str] = Field(None, description="Resolution notes when closing")

class IncidentResponse(BaseModel):
    sys_id: str
    number: str
    short_description: str
    description: Optional[str] = ""
    priority: str
    impact: str
    urgency: str
    state: str
    created_on: Optional[str] = ""
    created_by: Optional[str] = ""
    assigned_to: Optional[str] = ""
    assignment_group: Optional[str] = ""

 

# Pydantic models for CSM CASES
class CaseBase(BaseModel):
    short_description: str = Field(..., min_length=1, max_length=160, description="Brief description of the case")
    description: Optional[str] = Field(None, max_length=4000, description="Detailed description of the case")
    priority: Optional[str] = Field("4", description="Priority: 1=Critical, 2=High, 3=Moderate, 4=Low")
    impact: Optional[str] = Field("3", description="Impact: 1=High, 2=Medium, 3=Low")
    urgency: Optional[str] = Field("3", description="Urgency: 1=High, 2=Medium, 3=Low")
    category: Optional[str] = Field("inquiry", description="Case category")
    subcategory: Optional[str] = Field(None, description="Case subcategory")
    assignment_group: Optional[str] = Field(None, description="Assignment group name or sys_id")
    assigned_to: Optional[str] = Field(None, description="Assigned user name or sys_id")
    contact: Optional[str] = Field(None, description="Contact/Customer user name or sys_id")
    consumer: Optional[str] = Field(None, description="Consumer user name or sys_id")
    account: Optional[str] = Field(None, description="Account name or sys_id")
    contact_type: Optional[str] = Field("phone", description="Contact type: phone, email, web, etc.")
    origin: Optional[str] = Field("phone", description="Case origin: phone, email, web, walk-in, etc.")
    escalation: Optional[str] = Field("0", description="Escalation level: 0=Normal, 1=Manager, 2=Executive")

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    short_description: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=4000)
    priority: Optional[str] = Field(None, description="Priority: 1-4")
    impact: Optional[str] = Field(None, description="Impact: 1-3")
    urgency: Optional[str] = Field(None, description="Urgency: 1-3")
    state: Optional[str] = Field(None, description="State: 1=Open, 2=Work in Progress, 3=Resolved, 4=Closed")
    work_notes: Optional[str] = Field(None, description="Work notes to add")
    close_notes: Optional[str] = Field(None, description="Resolution notes when closing")
    escalation: Optional[str] = Field(None, description="Escalation level: 0=Normal, 1=Manager, 2=Executive")

class CaseResponse(BaseModel):
    sys_id: str
    number: str
    short_description: str
    description: Optional[str] = ""
    priority: str
    impact: str
    urgency: str
    state: str
    escalation: Optional[str] = ""
    created_on: Optional[str] = ""
    created_by: Optional[str] = ""
    assigned_to: Optional[str] = ""
    assignment_group: Optional[str] = ""
    contact: Optional[str] = ""
    consumer: Optional[str] = ""
    account: Optional[str] = ""

 

def transform_servicenow_response(snow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform ServiceNow response data to match our model"""
    # Ensure we have a dictionary
    if not isinstance(snow_data, dict):
        logger.error(f"Expected dictionary, got {type(snow_data)}: {snow_data}")
        raise ValueError(f"Expected dictionary, got {type(snow_data)}")


    transformed = {}

    # Direct field mappings for incidents
    incident_field_mappings = {
        'sys_id': 'sys_id',
        'number': 'number',
        'short_description': 'short_description',
        'description': 'description',
        'priority': 'priority',
        'impact': 'impact',
        'urgency': 'urgency',
        'state': 'state',
        'sys_created_on': 'created_on',
        'sys_created_by': 'created_by',
        'assigned_to': 'assigned_to',
        'assignment_group': 'assignment_group'
    }
    
    # Additional field mappings for cases
    case_field_mappings = {
        'escalation': 'escalation',
        'contact': 'contact',
        'consumer': 'consumer',
        'account': 'account'
    }
    
    # Combine mappings
    all_field_mappings = {**incident_field_mappings, **case_field_mappings}
    
    for snow_field, model_field in all_field_mappings.items():
        value = snow_data.get(snow_field, '')
        
        # Handle reference fields (they come as dicts with display_value)
        if isinstance(value, dict):
            transformed[model_field] = value.get('display_value', value.get('value', ''))
        else:
            transformed[model_field] = value or ''
    
    return transformed

class ServiceNowConnection:
    """ServiceNow connection manager using PySnow"""
    
    def __init__(self):
        self.instance = os.getenv('SNOW_INSTANCE')
        self.username = os.getenv('SNOW_USERNAME')
        self.password = os.getenv('SNOW_PASSWORD')
        
        if not all([self.instance, self.username, self.password]):
            raise ValueError("Missing required ServiceNow environment variables: SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD")
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to ServiceNow"""
        try:
            # Create client with proper parameters
            self.client = pysnow.Client(
                instance=self.instance,
                user=self.username,
                password=self.password,
                raise_on_empty=False  # Don't raise exception on empty results
            )
            
            # Set default parameters for display values
            self.client.parameters.display_value = True
            self.client.parameters.exclude_reference_link = True
            
            logger.info(f"Connected to ServiceNow instance: {self.instance}")
        except Exception as e:
            logger.error(f"Failed to connect to ServiceNow: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test the ServiceNow connection"""
        try:
            incident_table = self.client.resource(api_path='/table/incident')
            # Try to fetch one record to test connection
            incident_table.parameters.limit = 1
            result = incident_table.get()
            list(result.all())  # Try to consume the generator
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_incident_table(self):
        """Get the incident table resource"""
        resource = self.client.resource(api_path='/table/incident')
        # Ensure display values are enabled
        resource.parameters.display_value = True
        resource.parameters.exclude_reference_link = True
        return resource
    
    def get_case_table(self):
        """Get the CSM case table resource"""
        resource = self.client.resource(api_path='/table/sn_customerservice_case')
        # Ensure display values are enabled
        resource.parameters.display_value = True
        resource.parameters.exclude_reference_link = True
        return resource

# Global ServiceNow connection instance
snow_connection = None

def get_snow_connection() -> ServiceNowConnection:
    """Dependency to get ServiceNow connection"""
    global snow_connection
    if snow_connection is None:
        snow_connection = ServiceNowConnection()
    return snow_connection

# API Endpoints

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ServiceNow Incident & CSM Case API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/health",
            "incidents": {
                "create": "/incidents",
                "get_by_id": "/incidents/{sys_id}",
                "update": "/incidents/{sys_id}",
                "get_by_number": "/incidents/search/{incident_number}",
                "bulk_create": "/incidents/bulk"
            },
            "cases": {
                "create": "/cases",
                "get_by_id": "/cases/{sys_id}",
                "update": "/cases/{sys_id}",
                "get_by_number": "/cases/search/{case_number}",
                "bulk_create": "/cases/bulk"
            }
        }
    }

@app.get("/health", tags=["Health"])
async def health_check(snow_conn: ServiceNowConnection = Depends(get_snow_connection)):
    """Health check endpoint"""
    try:
        connection_ok = snow_conn.test_connection()
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "servicenow_connection": connection_ok,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "servicenow_connection": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ==================== INCIDENT ENDPOINTS ====================

@app.post("/incidents", response_model=IncidentResponse, tags=["Incidents"])
async def create_incident(
    incident_data: IncidentCreate,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Create a new incident in ServiceNow"""
    try:
        incident_table = snow_conn.get_incident_table()
        
        # Prepare payload - remove None values and convert to proper format
        payload = {}
        for key, value in incident_data.dict(exclude_unset=True).items():
            if value is not None and value != "string":  # Filter out placeholder values
                payload[key] = value
        
        payload['state'] = '1'  # New state
        
        logger.info(f"Creating incident with payload: {payload}")
        
        # Create the incident - this actually returns a Response object
        response = incident_table.create(payload)
        
        try:
            # Extract the created record from the Response object using .one()
            created_record = response.one()
            logger.info(f"Created incident data: {created_record}")
            
            if created_record:
                # Transform and return the response
                transformed_data = transform_servicenow_response(created_record)
                return IncidentResponse(**transformed_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create incident - no data returned"
                )
        except pysnow.exceptions.NoResults:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create incident - no results found"
            )

            
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {str(e)}"
        )

@app.get("/incidents/{sys_id}", response_model=IncidentResponse, tags=["Incidents"])
async def get_incident(
    sys_id: str,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Get an incident by sys_id"""
    try:
        incident_table = snow_conn.get_incident_table()
        
        # Get the incident using proper pysnow query method
        response = incident_table.get(query={'sys_id': sys_id})
        result = response.one()
        
        if result:
            transformed_data = transform_servicenow_response(result)
            return IncidentResponse(**transformed_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with sys_id {sys_id} not found"
            )
            
    except pysnow.exceptions.NoResults:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with sys_id {sys_id} not found"
        )
    except Exception as e:
        logger.error(f"Error fetching incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch incident: {str(e)}"
        )

@app.put("/incidents/{sys_id}", response_model=IncidentResponse, tags=["Incidents"])
async def update_incident(
    sys_id: str,
    incident_data: IncidentUpdate,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Update an existing incident"""
    try:
        incident_table = snow_conn.get_incident_table()
        
        # Prepare payload (only include fields that are set)
        payload = incident_data.dict(exclude_unset=True)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )

        logger.info(f"Updating incident {sys_id} with payload: {payload}")

        # Update the incident - this actually returns a Response object
        response = incident_table.update(query={'sys_id': sys_id}, payload=payload)

        try:
            # Extract the updated record from the Response object using .one()
            updated_record = response.one()
            logger.info(f"Updated incident data: {updated_record}")

            if updated_record:
                # Transform and return the response
                transformed_data = transform_servicenow_response(updated_record)
                return IncidentResponse(**transformed_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update incident - no data returned"
                )
        except pysnow.exceptions.NoResults:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with sys_id {sys_id} not found for update"
            )

            
    except Exception as e:
        logger.error(f"Error updating incident: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident: {str(e)}"
        )

@app.get("/incidents/search/{incident_number}", response_model=IncidentResponse, tags=["Incidents"])
async def get_incident_by_number(
    incident_number: str,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Get an incident by its number (e.g., INC0000123)"""
    try:
        incident_table = snow_conn.get_incident_table()
        
        # Get the incident by number using proper pysnow query method
        response = incident_table.get(query={'number': incident_number})
        result = response.one()
        
        if result:
            logger.info(f"Found incident {incident_number}")
            transformed_data = transform_servicenow_response(result)
            return IncidentResponse(**transformed_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_number} not found"
            )
            
    except pysnow.exceptions.NoResults:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_number} not found"
        )
    except Exception as e:
        logger.error(f"Error fetching incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch incident: {str(e)}"
        )

@app.post("/incidents/bulk", tags=["Incidents"])
async def create_bulk_incidents(
    incidents: List[IncidentCreate],
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Create multiple incidents at once"""
    if len(incidents) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 incidents allowed per bulk request"
        )
    
    created_incidents = []
    errors = []
    
    for i, incident_data in enumerate(incidents):
        try:
            incident_table = snow_conn.get_incident_table()
            
            # Prepare payload - remove None values and convert to proper format
            payload = {}
            for key, value in incident_data.dict(exclude_unset=True).items():
                if value is not None and value != "string":  # Filter out placeholder values
                    payload[key] = value
            
            payload['state'] = '1'
            
            logger.info(f"Creating bulk incident {i+1} with payload: {payload}")
            
            # Create the incident
            response = incident_table.create(payload)
            
            try:
                created_record = response.one()
                
                if created_record:
                    transformed_data = transform_servicenow_response(created_record)
                    created_incidents.append(IncidentResponse(**transformed_data))
                else:
                    errors.append(f"Failed to create incident {i+1}: No data returned")
            except pysnow.exceptions.NoResults:
                errors.append(f"Failed to create incident {i+1}: No results found")
                
        except Exception as e:
            errors.append(f"Error creating incident {i+1}: {str(e)}")
    
    return {
        "created_count": len(created_incidents),
        "error_count": len(errors),
        "created_incidents": created_incidents,
        "errors": errors
    }

# ==================== CSM CASE ENDPOINTS ====================

@app.post("/cases", response_model=CaseResponse, tags=["Cases"])
async def create_case(
    case_data: CaseCreate,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Create a new CSM case in ServiceNow"""
    try:
        case_table = snow_conn.get_case_table()
        
        # Prepare payload - remove None values and convert to proper format
        payload = {}
        for key, value in case_data.dict(exclude_unset=True).items():
            if value is not None and value != "string":  # Filter out placeholder values
                payload[key] = value
        
        payload['state'] = '1'  # Open state for cases
        
        logger.info(f"Creating case with payload: {payload}")
        
        # Create the case - this actually returns a Response object
        response = case_table.create(payload)
        
        try:
            # Extract the created record from the Response object using .one()
            created_record = response.one()
            logger.info(f"Created case data: {created_record}")
            
            if created_record:
                # Transform and return the response
                transformed_data = transform_servicenow_response(created_record)
                return CaseResponse(**transformed_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create case - no data returned"
                )
        except pysnow.exceptions.NoResults:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create case - no results found"
            )

            
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )

@app.get("/cases/{sys_id}", response_model=CaseResponse, tags=["Cases"])
async def get_case(
    sys_id: str,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Get a case by sys_id"""
    try:
        case_table = snow_conn.get_case_table()
        
        # Get the case using proper pysnow query method
        response = case_table.get(query={'sys_id': sys_id})
        result = response.one()
        
        if result:
            transformed_data = transform_servicenow_response(result)
            return CaseResponse(**transformed_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with sys_id {sys_id} not found"
            )
            
    except pysnow.exceptions.NoResults:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with sys_id {sys_id} not found"
        )
    except Exception as e:
        logger.error(f"Error fetching case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch case: {str(e)}"
        )

@app.put("/cases/{sys_id}", response_model=CaseResponse, tags=["Cases"])
async def update_case(
    sys_id: str,
    case_data: CaseUpdate,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Update an existing case"""
    try:
        case_table = snow_conn.get_case_table()
        
        # Prepare payload (only include fields that are set)
        payload = case_data.dict(exclude_unset=True)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        logger.info(f"Updating case {sys_id} with payload: {payload}")
        
        # Update the case - this actually returns a Response object  
        response = case_table.update(query={'sys_id': sys_id}, payload=payload)
        
        try:
            # Extract the updated record from the Response object using .one()
            updated_record = response.one()
            logger.info(f"Updated case data: {updated_record}")
            
            if updated_record:
                # Transform and return the response
                transformed_data = transform_servicenow_response(updated_record)
                return CaseResponse(**transformed_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update case - no data returned"
                )
        except pysnow.exceptions.NoResults:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with sys_id {sys_id} not found for update"
            )

            
    except Exception as e:
        logger.error(f"Error updating case: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update case: {str(e)}"
        )

@app.get("/cases/search/{case_number}", response_model=CaseResponse, tags=["Cases"])
async def get_case_by_number(
    case_number: str,
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Get a case by its number (e.g., CS0001001)"""
    try:
        case_table = snow_conn.get_case_table()
        
        # Get the case by number using proper pysnow query method
        response = case_table.get(query={'number': case_number})
        result = response.one()
        
        if result:
            logger.info(f"Found case {case_number}")
            transformed_data = transform_servicenow_response(result)
            return CaseResponse(**transformed_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_number} not found"
            )
            
    except pysnow.exceptions.NoResults:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_number} not found"
        )
    except Exception as e:
        logger.error(f"Error fetching case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch case: {str(e)}"
        )

@app.post("/cases/bulk", tags=["Cases"])
async def create_bulk_cases(
    cases: List[CaseCreate],
    snow_conn: ServiceNowConnection = Depends(get_snow_connection)
):
    """Create multiple cases at once"""
    if len(cases) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 cases allowed per bulk request"
        )
    
    created_cases = []
    errors = []
    
    for i, case_data in enumerate(cases):
        try:
            case_table = snow_conn.get_case_table()
            
            # Prepare payload - remove None values and convert to proper format
            payload = {}
            for key, value in case_data.dict(exclude_unset=True).items():
                if value is not None and value != "string":  # Filter out placeholder values
                    payload[key] = value
            
            payload['state'] = '1'  # Open state
            
            logger.info(f"Creating bulk case {i+1} with payload: {payload}")
            
            # Create the case
            response = case_table.create(payload)
            
            try:
                created_record = response.one()
                
                if created_record:
                    transformed_data = transform_servicenow_response(created_record)
                    created_cases.append(CaseResponse(**transformed_data))
                else:
                    errors.append(f"Failed to create case {i+1}: No data returned")
            except pysnow.exceptions.NoResults:
                errors.append(f"Failed to create case {i+1}: No results found")
                
        except Exception as e:
            errors.append(f"Error creating case {i+1}: {str(e)}")
    
    return {
        "created_count": len(created_cases),
        "error_count": len(errors),
        "created_cases": created_cases,
        "errors": errors
    }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable, default to 8091
    port = int(os.getenv('PORT', 8091))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )