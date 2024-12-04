from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ResourceClosedError
from data_models import ChatHistoryModel, ChatSessionDataModel, ChatFeedback, ChatVoting, SummaryDataModel, SummaryVoting

Base = declarative_base()

class ChatSessionDataModelSQL(Base):
    __tablename__ = 'chat_session_data'
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    chat_timestamp = Column(DateTime)
    chat_json = Column(JSON)

class VoteSessionDataModelSQL(Base):
    __tablename__ = 'vote_data'
    vote_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String)
    vote_timestamp = Column(DateTime)
    vote = Column(Integer)

class FeedbackSessionDataModelSQL(Base):
    __tablename__ = 'feedback_data'
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String)
    feedback_timestamp = Column(DateTime)
    feedback = Column(String)

class SummarySessionDataModelSQL(Base):
    __tablename__ = 'summary_data'
    summary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String)
    summary_timestamp_start = Column(DateTime)
    summary_timestamp_end = Column(DateTime)
    input_text = Column(String)
    summary = Column(String)

class VoteSummaryDataModelSQL(Base):
    __tablename__ = 'vote_summary_data'
    summary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String)
    vote_timestamp = Column(DateTime)
    vote = Column(Integer)

class ChatHistoryDataModelSQL(Base):
    __tablename__ = 'chat_history_data'
    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String)
    chat_timestamp = Column(DateTime)
    chat_json = Column(JSON)

# Replace with your actual database URL
# DATABASE_URL = "postgresql://somansh@localhost/postgres"
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)


class ChatDBMethods:
    def save_chat_history(chat_hist: ChatHistoryModel):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            chat_history_data = ChatHistoryDataModelSQL(
                query_id=chat_hist.query_id,
                session_id=chat_hist.session_id,
                user_id=chat_hist.user_id,
                chat_timestamp=chat_hist.chat_timestamp,
                chat_json=chat_hist.chat_json.model_dump_json()
            )
            session.add(chat_history_data)
            session.flush()
            if session.is_active:
                session.commit()
        except ResourceClosedError:
            session.rollback()
            print("Transaction is closed. Rolling back.")
        finally:
            session.close()

    def save_response_chat(response_chat: ChatSessionDataModel):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            chat_session_data = ChatSessionDataModelSQL(
                session_id=response_chat.session_id,
                user_id=response_chat.user_id,
                query_id=response_chat.query_id,
                chat_timestamp=response_chat.chat_json.query_timestamp,
                chat_json=response_chat.chat_json.model_dump_json()
            )
            session.add(chat_session_data)
            session.flush()
            if session.is_active:
                session.commit()
        except ResourceClosedError:
            session.rollback()
            print("Transaction is closed. Rolling back.")
        finally:
            session.close()

    def save_summary_session_data(summary_data: SummaryDataModel):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            summary_session_data = SummarySessionDataModelSQL(
                session_id=summary_data.session_id,
                summary_id=summary_data.summary_id,
                user_id=summary_data.user_id,
                summary_timestamp_start=summary_data.summary_timestamp_start,
                summary_timestamp_end=summary_data.summary_timestamp_end,
                input_text=summary_data.input_text,
                summary=summary_data.summary
            )
            session.add(summary_session_data)
            session.flush()
            if session.is_active:
                session.commit()
        except ResourceClosedError:
            session.rollback()
            print("Transaction is closed. Rolling back.")
        finally:
            session.close()

    def save_feedback(feedback_f: ChatFeedback):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            feedback_data = FeedbackSessionDataModelSQL(
                feedback_id=uuid.uuid4(),
                query_id=feedback_f.query_id,
                user_id=feedback_f.user_id,
                feedback_timestamp=datetime.datetime.now(),
                feedback=feedback_f.feedback
            )
            if feedback_f.query_id in session.query(FeedbackSessionDataModelSQL.query_id):
                return "Feedback already recorded"
            session.add(feedback_data)
            if session.is_active:
                session.commit()
        except:
            session.rollback()
            print("Transaction is closed. Rolling back.")

        finally:
            session.close()
            # print("Transaction is closed. Rolling back.")

    def save_vote(vote: ChatVoting):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            vote_data = VoteSessionDataModelSQL(
                vote_id=uuid.uuid4(),
                query_id=vote.query_id,
                user_id=vote.user_id,
                vote_timestamp=datetime.datetime.now(),
                vote=vote.vote
            )
            existing_vote = session.query(VoteSessionDataModelSQL).filter(
                VoteSessionDataModelSQL.query_id == vote.query_id).first()
            if existing_vote:
                existing_vote.vote = vote.vote
            else:
                session.add(vote_data)
            session.flush()
            if session.is_active:
                session.commit()
        except ResourceClosedError:
            session.rollback()
            print("Transaction is closed. Rolling back.")
        finally:
            session.close()
        return "Vote Recorded"

    def save_vote_summary(vote: SummaryVoting):
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            vote_data = VoteSummaryDataModelSQL(
                summary_id=uuid.UUID(vote.summary_id),
                session_id=uuid.UUID(vote.session_id),
                user_id=vote.user_id,
                vote_timestamp=datetime.datetime.now(),
                vote=vote.vote
            )
            existing_vote = session.query(VoteSummaryDataModelSQL).filter(
                VoteSummaryDataModelSQL.summary_id == uuid.UUID(vote.summary_id)).first()
            if existing_vote:
                existing_vote.vote = vote.vote
            else:
                session.add(vote_data)
            session.flush()
            if session.is_active:
                session.commit()
        except ResourceClosedError:
            session.rollback()
            print("Transaction is closed. Rolling back.")
        finally:
            session.close()
        return "Vote Recorded"