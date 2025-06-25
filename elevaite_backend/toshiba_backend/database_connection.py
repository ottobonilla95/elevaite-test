import datetime
import os
import uuid
from typing import List, Dict

from sqlalchemy import Column, String, DateTime, Integer, create_engine, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from data_classes import ChatRequest, AgentFlow

# Define the data table
Base = declarative_base()

class ChatRequestTable(Base):
    __tablename__ = 'chat_data_final'
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    sr_ticket_id = Column(String, nullable=True)
    original_request = Column(String, nullable=True)
    request = Column(String, nullable=True)
    request_timestamp = Column(DateTime, nullable=True)
    response = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    response_timestamp = Column(DateTime, nullable=True)
    vote = Column(Integer, default=0)
    vote_timestamp = Column(DateTime, nullable=True)
    feedback = Column(String, default="")
    feedback_timestamp = Column(DateTime, nullable=True)
    agent_flow_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())


class AgentFlowTable(Base):
    __tablename__ = 'agent_flow_data'
    agent_flow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    qid = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(String, nullable=True)
    request = Column(String, nullable=True)
    response = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    tries = Column(Integer, default=0)
    tool_calls = Column(String, nullable=True)
    chat_history = Column(String, nullable=True)



class DatabaseConnection:
    def __init__(self):
        # Create async engine for asyncpg
        self.engine = create_async_engine(
            os.getenv("SQLALCHEMY_DATABASE_URL"),
            echo=True,  # Set to False in production
            pool_pre_ping=True,  # Verify connections before using them
            pool_size=5,  # Adjust based on your needs
            max_overflow=10  # Adjust based on your needs
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession
        )

    async def init_db(self):
        # Create tables asynchronously
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    async def close_db(self):
        # Close the database connection pool
        try:
            await self.engine.dispose()
            print("Database connection closed successfully")
        except Exception as e:
            print(f"Error closing database connection: {str(e)}")

    async def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            await db.close()

    async def update_vote(self, message_id, user_id, vote, session_id):
        """Update the vote for a message in the database.

        Args:
            message_id: UUID of the message to update
            user_id: ID of the user who voted
            vote: The vote value (-1, 0, or 1)
            session_id: UUID of the session

        Returns:
            bool: True if successful, False otherwise
        """
        async with self.SessionLocal() as session:
            try:
                # Try to find the existing chat request
                stmt = select(ChatRequestTable).where(ChatRequestTable.qid == message_id)
                result = await session.execute(stmt)
                existing_request = result.scalars().first()

                # Get current time - use timezone-naive for vote_timestamp and timezone-aware for created_at/updated_at
                current_time_naive = datetime.datetime.now()
                current_time_aware = datetime.datetime.now()

                if existing_request:
                    # Update only the vote and vote_timestamp
                    existing_request.vote = vote
                    existing_request.vote_timestamp = current_time_naive
                    existing_request.updated_at = current_time_aware
                    await session.commit()
                    print(f"Vote updated successfully for message {message_id}")
                    return True
                else:
                    print(f"No existing chat request found with qid {message_id}")
                    # Create a new record with just the vote information
                    # vote_record = ChatRequestTable(
                    #     qid=message_id,
                    #     session_id=session_id,
                    #     user_id=user_id,
                    #     vote=vote,
                    #     vote_timestamp=current_time_naive,
                    #     updated_at=current_time_aware
                    # )
                    # session.add(vote_record)
                    # await session.flush()
                    # await session.commit()
                    # print(f"New vote record created for message {message_id}")
                    return True
            except ResourceClosedError as e:
                await session.rollback()
                print(f"Transaction is closed. Rolling back. Error: {str(e)}")
                return False
            except Exception as e:
                await session.rollback()
                error_type = type(e).__name__
                print(f"Error updating vote: {error_type} - {str(e)}")

                # More detailed error information for debugging
                if hasattr(e, '__cause__') and e.__cause__ is not None:
                    print(f"Caused by: {type(e.__cause__).__name__} - {str(e.__cause__)}")

                return False

    async def update_feedback(self, message_id, user_id, feedback, session_id):
        """Update or add feedback for a message in the database.

        If the message already has feedback, the new feedback is appended with a "\n\n" separator.

        Args:
            message_id: UUID of the message to update
            user_id: ID of the user who provided feedback
            feedback: The feedback text
            session_id: UUID of the session

        Returns:
            bool: True if successful, False otherwise
        """
        async with self.SessionLocal() as session:
            try:
                # Try to find the existing chat request
                stmt = select(ChatRequestTable).where(ChatRequestTable.qid == message_id)
                result = await session.execute(stmt)
                existing_request = result.scalars().first()

                # Get current time - use timezone-naive for feedback_timestamp and timezone-aware for updated_at
                current_time_naive = datetime.datetime.now()
                current_time_aware = datetime.datetime.now()

                if existing_request:
                    # Check if there's already feedback and append the new feedback with separator if needed
                    if existing_request.feedback and existing_request.feedback.strip():
                        if feedback in existing_request.feedback:
                            return True
                        existing_request.feedback = f"{existing_request.feedback}\n\n{feedback}"
                    else:
                        existing_request.feedback = feedback

                    existing_request.feedback_timestamp = current_time_naive
                    existing_request.updated_at = current_time_aware
                    await session.commit()
                    print(f"Feedback updated successfully for message {message_id}")
                    return True
                else:
                    print(f"No existing chat request found with qid {message_id}")
                    # Create a new record with just the feedback information
                    # feedback_record = ChatRequestTable(
                    #     qid=message_id,
                    #     session_id=session_id,
                    #     user_id=user_id,
                    #     feedback=feedback,
                    #     feedback_timestamp=current_time_naive,
                    #     updated_at=current_time_aware
                    # )
                    # session.add(feedback_record)
                    # await session.flush()
                    # await session.commit()
                    # print(f"New feedback record created for message {message_id}")
                    return True
            except ResourceClosedError as e:
                await session.rollback()
                print(f"Transaction is closed. Rolling back. Error: {str(e)}")
                return False
            except Exception as e:
                await session.rollback()
                error_type = type(e).__name__
                print(f"Error updating feedback: {error_type} - {str(e)}")

                # More detailed error information for debugging
                if hasattr(e, '__cause__') and e.__cause__ is not None:
                    print(f"Caused by: {type(e.__cause__).__name__} - {str(e.__cause__)}")

                return False

    async def save_chat_request(self, chat_request: ChatRequest):
        async with self.SessionLocal() as session:
            try:
                chat_request_data = ChatRequestTable(
                    qid=chat_request.qid,
                    session_id=chat_request.session_id,
                    request=chat_request.request,
                    request_timestamp=chat_request.request_timestamp,
                    original_request=chat_request.original_request,
                    response=chat_request.response,
                    response_timestamp=datetime.datetime.now(),
                    user_id=chat_request.user_id,
                    agent_flow_id=chat_request.agent_flow_id,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    sr_ticket_id=chat_request.sr_ticket_id
                )
                session.add(chat_request_data)
                await session.flush()
                await session.commit()
                print("Chat request saved successfully")
                return True
            except ResourceClosedError as e:
                await session.rollback()
                print(f"Transaction is closed. Rolling back. Error: {str(e)}")
                return False
            except Exception as e:
                await session.rollback()
                error_type = type(e).__name__
                print(f"Error saving chat request: {error_type} - {str(e)}")

                # More detailed error information for debugging
                if hasattr(e, '__cause__') and e.__cause__ is not None:
                    print(f"Caused by: {type(e.__cause__).__name__} - {str(e.__cause__)}")

                # Check for common database errors
                if 'connection' in str(e).lower():
                    print("This appears to be a connection issue. Check that your database is running and accessible.")
                elif 'duplicate key' in str(e).lower():
                    print("This appears to be a duplicate key issue. Check that you're not trying to insert a record with an ID that already exists.")
                elif 'column' in str(e).lower() and 'not exist' in str(e).lower():
                    print("This appears to be a schema mismatch. Make sure your database schema matches your model definitions.")

                return False

    async def save_agent_flow(self, agent_flow: AgentFlow):
        async with self.SessionLocal() as session:
            try:
                agent_flow_data = AgentFlowTable(
                    agent_flow_id=agent_flow.agent_flow_id,
                    qid=agent_flow.qid,
                    session_id=agent_flow.session_id,
                    user_id=agent_flow.user_id,
                    request=agent_flow.request,
                    response=agent_flow.response,
                    created_at=datetime.datetime.now(),
                    tool_calls=agent_flow.tool_calls,
                    chat_history=agent_flow.chat_history,
                    name="Toshiba Agent Flow"
                )
                session.add(agent_flow_data)
                await session.flush()
                await session.commit()
                print("Agent flow request saved successfully")
                return True
            except ResourceClosedError as e:
                print(f"Transaction is closed. Rolling back. Error: {str(e)}")
                await session.rollback()
                return False
            finally:
                await session.close()

    async def get_past_sessions(self, user_id: str):
        async with self.SessionLocal() as session:
            try:
                stmt =select(ChatRequestTable.session_id)\
                    .where(ChatRequestTable.user_id == user_id)\
                    .group_by(ChatRequestTable.session_id)\
                    .order_by(func.max(ChatRequestTable.request_timestamp).desc())\
                    .limit(10)
                result = await session.execute(stmt)
                chat_requests = result.scalars().all()
                return chat_requests
            except Exception as e:
                print(f"Error fetching past sessions: {str(e)}")
                return []

    async def get_session_messages(self, session_id: str):
        async with self.SessionLocal() as session:
            try:
                stmt = select(ChatRequestTable).where(ChatRequestTable.session_id == session_id)
                result = await session.execute(stmt)
                # print("Result: ", result)
                chat_requests = result.scalars().all()
                # print("Chat requests: ", chat_requests)
                return chat_requests
            except Exception as e:
                print(f"Error fetching session messages: {str(e)}")
                return []
