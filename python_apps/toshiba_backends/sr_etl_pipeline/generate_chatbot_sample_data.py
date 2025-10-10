import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import random
from datetime import datetime, timedelta
import os
import json

# Load config from settings.json
def load_config():
    try:
        with open("config/settings.json", "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("❌ config/settings.json not found")
        return None

# Sample data for realistic chatbot queries
SAMPLE_QUERIES = [
    "How do I reset the X4000 model after error code E72?",
    "What does error code E72 mean on 335 series?",
    "Can I order part #T90-4521 replacement online?",
    "How long is warranty coverage for Z2000 series?",
    "Schedule emergency technician visit today",
    "Step by step calibration procedure for 4900 model",
    "Troubleshoot power supply issue on model X1200",
    "What part number do I need for the main board?",
    "How to access diagnostic mode on 500 series?",
    "Machine keeps showing temperature error, what to do?",
    "Where can I download the service manual?",
    "How to replace the filter on model Y300?",
    "Error code E15 keeps appearing, need help",
    "Can you help me with preventive maintenance schedule?",
    "What's the procedure for software update?",
    "How to contact technical support?",
    "Need part number for display assembly",
    "Machine won't start, troubleshooting steps?",
    "How to perform system backup?",
    "What are the safety procedures for maintenance?"
]

SAMPLE_RESPONSES = [
    "To reset the X4000 model after error E72, please follow these steps: 1) Power off the unit completely...",
    "Error code E72 indicates a temperature sensor malfunction. Please check the sensor connections...",
    "Yes, you can order part #T90-4521 through our online portal. Here's the direct link...",
    "The Z2000 series comes with a 2-year manufacturer warranty covering parts and labor...",
    "I can help you schedule a technician visit. Please provide your location and preferred time...",
    "Here's the step-by-step calibration procedure for the 4900 model: Step 1) Access the calibration menu...",
    "For power supply troubleshooting on X1200, first check these common issues...",
    "The main board part number depends on your specific model. Can you provide the serial number?",
    "To access diagnostic mode on 500 series: Hold down the Menu and Enter buttons simultaneously...",
    "Temperature errors can be caused by several factors. Let's troubleshoot systematically...",
    "Service manuals are available in the documentation section of our support portal...",
    "To replace the filter on Y300: 1) Power off the unit 2) Remove the front panel...",
    "Error E15 typically indicates a communication fault. Try these troubleshooting steps...",
    "Here's the recommended preventive maintenance schedule for your equipment...",
    "Software updates can be performed through the system settings menu...",
    "You can reach technical support at 1-800-SUPPORT or through the chat portal...",
    "The display assembly part number for your model is DA-2450-X. Would you like ordering information?",
    "If the machine won't start, please check these items in order: 1) Power connection...",
    "To perform a system backup: 1) Navigate to System Settings 2) Select Backup Options...",
    "Safety procedures for maintenance include: 1) Always power off equipment 2) Use proper PPE..."
]

# Original queries (what user actually typed, might have typos or informal language)
ORIGINAL_QUERIES = [
    "how do i reset x4000 after e72 error??",
    "what is e72 error on 335 machine",
    "can i buy part T90-4521 online?",
    "warranty info for z2000?",
    "need tech visit asap today",
    "calibration steps for 4900",
    "x1200 power problem help",
    "main board part number?",
    "how to get to diagnostic mode 500 series",
    "temp error keeps showing up",
    "where is service manual download",
    "y300 filter replacement how to",
    "e15 error wont go away",
    "preventive maintenance schedule help",
    "software update procedure",
    "tech support contact info",
    "display assembly part #",
    "machine wont start help",
    "system backup how to",
    "maintenance safety rules"
]

USER_IDS = [
    "john.doe@company.com", "jane.smith@corp.com", "mike.jones@business.com",
    "sarah.wilson@company.com", "robert.brown@corp.com", "lisa.davis@business.com",
    "david.miller@company.com", "emily.garcia@corp.com", "james.rodriguez@business.com",
    "maria.martinez@company.com", "tech001", "tech002", "tech003", "manager01", "customer123"
]

def generate_sample_data():
    """Generate realistic sample chatbot data with original_request column"""
    try:
        # Load config from JSON
        config = load_config()
        if not config:
            return
            
        # Get database connection string
        database_url = config.get("pg_conn_string")
        if not database_url:
            print("❌ pg_conn_string not found in config/settings.json")
            return
            
        print(f"🔗 Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        
        conn = psycopg2.connect(database_url)
        conn.cursor_factory = RealDictCursor
        cur = conn.cursor()
        
        print("🔄 Generating sample chatbot data...")
        
        # Clear existing data
        cur.execute("DELETE FROM chat_data_final")
        cur.execute("DELETE FROM agent_flow_data")
        print("🗑️ Cleared existing chatbot data")
        
        # Generate data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        session_count = 0
        total_queries = 0
        
        # Generate sessions (aim for 800-1200 sessions over 30 days)
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            
            # More queries during business hours and weekdays
            if current_date.weekday() < 5:  # Weekday
                sessions_per_day = random.randint(25, 45)
            else:  # Weekend
                sessions_per_day = random.randint(10, 20)
            
            for session in range(sessions_per_day):
                session_id = str(uuid.uuid4())
                session_count += 1
                
                # Random time during the day (weighted towards business hours)
                if random.random() < 0.7:  # 70% during business hours (8 AM - 6 PM)
                    hour = random.randint(8, 17)
                else:
                    hour = random.randint(0, 23)
                
                minute = random.randint(0, 59)
                session_start = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Queries per session (1-5, weighted towards 1-2)
                queries_in_session = random.choices([1, 2, 3, 4, 5], weights=[40, 35, 15, 7, 3])[0]
                
                user_id = random.choice(USER_IDS)
                
                for query_num in range(queries_in_session):
                    query_time = session_start + timedelta(minutes=query_num * random.randint(1, 5))
                    response_time = query_time + timedelta(seconds=random.randint(1, 10))
                    
                    # Select query and response
                    query_idx = random.randint(0, len(SAMPLE_QUERIES) - 1)
                    original_query = ORIGINAL_QUERIES[query_idx]  # What user actually typed
                    processed_query = SAMPLE_QUERIES[query_idx]  # Cleaned/processed version
                    response_text = SAMPLE_RESPONSES[query_idx]
                    
                    # Generate vote (70% no vote, 20% thumbs up, 10% thumbs down)
                    vote_choice = random.choices([0, 1, -1], weights=[70, 20, 10])[0]
                    vote_timestamp = response_time + timedelta(seconds=random.randint(5, 30)) if vote_choice != 0 else None
                    
                    # Generate feedback for voted queries
                    feedback = ""
                    feedback_timestamp = None
                    if vote_choice != 0 and random.random() < 0.3:  # 30% of voted queries have written feedback
                        if vote_choice == 1:
                            feedback = random.choice([
                                "Very helpful, solved my issue quickly!",
                                "Perfect answer, exactly what I needed.",
                                "Great response, saved me time.",
                                "Excellent support, thank you!"
                            ])
                        else:
                            feedback = random.choice([
                                "Didn't solve my problem, need more help.",
                                "Answer was too generic, need specific steps.",
                                "Still confused after this response.",
                                "Need to speak with a human technician."
                            ])
                        feedback_timestamp = vote_timestamp + timedelta(seconds=random.randint(10, 60))
                    
                    # Insert query data with original_request column
                    cur.execute("""
                        INSERT INTO chat_data_final (
                            qid, session_id, sr_ticket_id, original_request, request, request_timestamp,
                            response, user_id, response_timestamp, vote, vote_timestamp,
                            feedback, feedback_timestamp, agent_flow_id, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        str(uuid.uuid4()), session_id, f"SR-{random.randint(100000, 999999)}",
                        original_query, processed_query, query_time, response_text, user_id, response_time,
                        vote_choice, vote_timestamp, feedback, feedback_timestamp,
                        str(uuid.uuid4()), query_time, query_time
                    ))
                    
                    total_queries += 1
                    
                    if total_queries % 200 == 0:
                        print(f"📊 Generated {total_queries} queries so far...")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Successfully generated {total_queries} queries across {session_count} sessions")
        print(f"📊 Average queries per session: {round(total_queries/session_count, 2)}")
        print(f"📅 Data spans from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Show some sample statistics
        print("\n📈 Sample Data Statistics:")
        print(f"   Total Sessions: {session_count}")
        print(f"   Total Queries: {total_queries}")
        print(f"   Estimated Thumbs Up: ~{int(total_queries * 0.2)}")
        print(f"   Estimated Thumbs Down: ~{int(total_queries * 0.1)}")
        print(f"   Estimated No Vote: ~{int(total_queries * 0.7)}")
        print(f"   Each query has both original_request and request columns")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_sample_data()