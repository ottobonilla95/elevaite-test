from model import InferencePayload
from sql_agent_factory import create_campaign_sql_agent
from db_connector import db_connector

async def sql_inference(inference_payload: InferencePayload):
    try:
        user_id = inference_payload.user_id
        session_id = inference_payload.session_id
        # selected_brand = inference_payload.selected_brand
        # selected_ad_surface = inference_payload.selected_ad_surface
        # selected_campaign = inference_payload.selected_campaign
        # conversation_history = inference_payload.conversation_payload or []
        user_query = inference_payload.query
        
        # Initialize database session
        db_session = db_connector.get_session()
        
        # Create SQL agent and query extractor
        # agent_executor, query_extractor = create_campaign_sql_agent()
        agent_executor = create_campaign_sql_agent()
            # selected_brand=selected_brand,
            # selected_ad_surface=selected_ad_surface,
            # selected_campaign=selected_campaign
            
        # Execute the query with callbacks to extract SQL
        response = await agent_executor.ainvoke(
            {"input": user_query},
            # callbacks=[query_extractor]
        )
        # print("SQL QUERIES USED:",query_extractor.queries if query_extractor.queries else [])
        # Return both the response and the SQL queries used
        yield {
            "response": response["output"],
            # "sql_queries": query_extractor.queries if query_extractor.queries else []
        }
        
    except Exception as e:
        yield {"response": f"An error occurred: {e}\n"}
    finally:
        # Close the database session
        if 'db_session' in locals():
            db_session.close()
