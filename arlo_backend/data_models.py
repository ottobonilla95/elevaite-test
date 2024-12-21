from pydantic import BaseModel
from typing import Dict, List, Optional
import datetime
import uuid


class ChatRequest(BaseModel):
    message: str
    session_id: str
    chat_history: List[Dict[str, str]]
    user_id: str
    enable_web_search: bool
    fetched_knowledge: str

class ChatRequestWithQueryId(BaseModel):
    message: str
    session_id: str
    chat_history: List[Dict[str, str]]
    user_id: str
    fetched_knowledge: str
    query_id: str

class ChatResponse(BaseModel):
    response: str
    # chat_history: List[Dict[str, str]]
    # web_text: str
    # kb_text: str
    fetched_knowledge: Optional[str] = None
    urls_fetched: List[str]
    query_id: str
    extracted_information: Optional[str] = None
    verification_message: Optional[str] = None
    issue_acknowledgement: Optional[str] = None
    opex_data: Optional[List[List[str]]] = None


class ChatInferenceStepInfo(BaseModel):
    step_name: str
    step_input_label: str
    step_output_label: str
    start_time: datetime.datetime
    step_input: str
    step_output: str
    end_time: datetime.datetime

class ChatSessionDataResponse(BaseModel):
    query: str
    query_timestamp: datetime.datetime
    inference_steps: List[ChatInferenceStepInfo]
    response: str
    response_timestamp: datetime.datetime

    class Config:
        arbitrary_types_allowed = True

class ChatSessionDataModel(BaseModel):
    chat_timestamp: datetime.datetime
    user_id: str
    session_id: uuid.UUID
    query_id: uuid.UUID
    chat_json: ChatSessionDataResponse

class ChatVoting(BaseModel):
    query_id: str
    user_id: str
    vote: int

class ChatFeedback(BaseModel):
    query_id: str
    user_id: str
    feedback: str # Feedback message
    vote: int


class EntityModel(BaseModel):
    entity: List[Dict[str, str]]

class SummaryInputModel(BaseModel):
    system_prompt: str
    text: str
    entities: Dict[str, str]
    history: Optional[List[Dict[str, str]]] = None
    more_context: Optional[str] = None

class SummaryDataModel(BaseModel):
    summary_id: uuid.UUID
    session_id: uuid.UUID
    user_id: str
    summary_timestamp_start: datetime.datetime
    summary_timestamp_end: datetime.datetime
    input_text: str
    summary: str

class SummaryRequest(BaseModel):
    text: str
    session_id: str
    user_id: str
    case_id: Optional[str] = None


class SummaryVoting(BaseModel):
    summary_id: str
    session_id: str
    user_id: str
    vote: int

class ChatHistory(BaseModel):
    chat_json: List[Dict[str, str]]

class ChatHistoryModel(BaseModel):
    query_id: uuid.UUID
    session_id: uuid.UUID
    user_id: str
    chat_timestamp: datetime.datetime
    chat_json: ChatHistory

class CaseID(BaseModel):
    session_id: uuid.UUID
    case_id: str

class SFChatRequest(BaseModel):
    session_id: str
    user_id: str
    case_id: str

class SFResponse(BaseModel):
    response: str
    fetched_knowledge: Optional[str] = None
    urls_fetched: List[str]
    query_id: str
    extracted_information: Optional[str] = None
    verification_message: Optional[str] = None
    issue_acknowledgement: Optional[str] = None
    sf_data: Optional[List[Dict[str,str]]] = None