import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from .agent_base import Agent


class MitieAgent(Agent):
    """
    Mitie Quote Generation Agent for processing RFQ documents and generating quotes.
    Handles JSON extraction, cost calculations, and PDF generation in a single workflow.
    """

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Execute the Mitie quote generation workflow.
        
        Args:
            query: RFQ document text or request for quote generation
            session_id: Optional session identifier
            user_id: Optional user identifier
            chat_history: Optional chat history for context
            enable_analytics: Whether to enable analytics
            **kwargs: Additional keyword arguments
            
        Returns:
            str: Quote generation result with PDF link and summary
        """
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )

    @property
    def openai_schema(self):
        """OpenAI function schema for this agent"""
        return {
            "type": "function",
            "function": {
                "name": "MitieAgent",
                "description": "Specialized agent for Mitie quote generation from RFQ documents. Use this agent to process RFQ documents, extract project details, calculate costs using Mitie rate cards, and generate professional PDF quotes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The RFQ document text or request for quote generation"},
                        "chat_history": {
                            "type": "array",
                            "description": "Optional chat history for context",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "actor": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["query"],
                },
            },
        }


def get_mitie_agent():
    """Factory function to create and configure MitieAgent instance"""
    from prompts import mitie_agent_system_prompt
    
    # Tools that MitieAgent will have access to
    from .tools import tool_schemas
    mitie_tools = [
        tool_schemas["extract_rfq_json"],
        tool_schemas["calculate_mitie_quote"],
        tool_schemas["generate_mitie_pdf"],
    ]
    
    return MitieAgent(
        name="MitieAgent",
        agent_type="api",  # Using api type as it processes documents and generates outputs
        description="Mitie Quote Generation Agent for RFQ processing and quote generation",
        agent_id=uuid.uuid4(),
        system_prompt=mitie_agent_system_prompt,
        persona="Professional Quote Generation Specialist",
        functions=mitie_tools,
        routing_options={
            "continue": "If you have successfully generated the quote and PDF",
            "ask": "If you need more information from the user to complete the quote",
            "give_up": "If the RFQ cannot be processed due to missing critical information"
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=True,
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )
