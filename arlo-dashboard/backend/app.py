from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from datetime import datetime, date



app = Flask(__name__)
CORS(app)

# Test route to verify server is running
@app.route('/', methods=['GET'])
def home():
    return "Backend server is running!"

# Database connection function
def db_connect():
    return psycopg2.connect(
        host="localhost",
        database="arlo_dashboard",
        user="postgres",
        password="Vijaya@2210$"
    )

# Route to fetch problems data
@app.route('/api/problems-data', methods=['GET'])
def get_problems_data():
    try:
        # Get 'from' and 'to' date parameters from the request
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        conn = db_connect()
        cursor = conn.cursor()
       
        # Base query with date filter
        query = """
            SELECT
                problem AS "Problem",
                root_cause AS "Root cause",
                symptoms AS "Symptoms",
                ai_usage_id AS "AI Usage ID",
                chat_duration AS "Chat Duration"
            FROM sf_chat_transcript_summary
            WHERE problem IS NOT NULL
            AND problem != ''
            AND root_cause IS NOT NULL
            AND root_cause != ''
            AND symptoms IS NOT NULL
            AND symptoms != ''
        """

        # Add date filter if 'from' and 'to' are provided
        params = []
        if from_date and to_date:
            query += " AND created_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
       
        # Execute the query
        cursor.execute(query, tuple(params))
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Convert chat duration to HH:MM format
                if column == "Chat Duration" and value is not None:
                    hours = int(value // 60)
                    minutes = int(value % 60)
                    value = f"{hours:02d}:{minutes:02d}"
                row_dict[column] = value if value is not None else ''
            results.append(row_dict)

        # If no data is found, fetch all data without the date filter
        if not results:
            cursor.execute("""
                SELECT
                    problem AS "Problem",
                    root_cause AS "Root cause",
                    symptoms AS "Symptoms",
                    ai_usage_id AS "AI Usage ID",
                    chat_duration AS "Chat Duration"
                FROM sf_chat_transcript_summary
                WHERE problem IS NOT NULL
                AND problem != ''
                AND root_cause IS NOT NULL
                AND root_cause != ''
                AND symptoms IS NOT NULL
                AND symptoms != ''
            """)
            results = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Convert chat duration to HH:MM format
                    if column == "Chat Duration" and value is not None:
                        hours = int(value // 60)
                        minutes = int(value % 60)
                        value = f"{hours:02d}:{minutes:02d}"
                    row_dict[column] = value if value is not None else ''
                results.append(row_dict)

        cursor.close()
        conn.close()
        return jsonify(results)

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/api/agents-data', methods=['GET'])
def get_agents_data():
    try:
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        conn = db_connect()
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT
                s.owner_full_name as "Owner: Full Name",
                s.status as "Status",
                s.chat_duration as "Chat Duration",
                s.created_date as "Created Date",
                s.ai_usage_id as "AIAssisted",
                m.csat_percentage as "CSAT",
                m.asat_percentage as "ASAT",
                m.fcr_percentage as "FCR",
                m.nps_percentage as "NPS"
            FROM sf_chat_transcript_summary s
            LEFT JOIN agent_metrics m ON 
                s.owner_full_name = m.agent_name 
                AND s.ai_usage_id = m.ai_usage
            WHERE s.owner_full_name IS NOT NULL
        """
        
        # Add date filter if dates are provided
        params = []
        if from_date and to_date:
            query += " AND s.created_date BETWEEN %s AND %s"
            params.extend([from_date, to_date])
            
        # Execute query with date filter
        cursor.execute(query, tuple(params))
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                if column == "Chat Duration" and value is not None:
                    minutes = int(float(value) // 60)
                    seconds = int(float(value) % 60)
                    value = f"{minutes}:{seconds:02d}"
                row_dict[column] = value if value is not None else ''
            results.append(row_dict)

        # If no data found with date filter, fetch all data
        if not results and from_date and to_date:
            base_query = """
                SELECT
                    s.owner_full_name as "Owner: Full Name",
                    s.status as "Status",
                    s.chat_duration as "Chat Duration",
                    s.created_date as "Created Date",
                    s.ai_usage_id as "AIAssisted",
                    m.csat_percentage as "CSAT",
                    m.asat_percentage as "ASAT",
                    m.fcr_percentage as "FCR",
                    m.nps_percentage as "NPS"
                FROM sf_chat_transcript_summary s
                LEFT JOIN agent_metrics m ON 
                    s.owner_full_name = m.agent_name 
                    AND s.ai_usage_id = m.ai_usage
                WHERE s.owner_full_name IS NOT NULL
            """
            
            cursor.execute(base_query)
            for row in cursor.fetchall():
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    if isinstance(value, (datetime, date)):
                        value = value.isoformat()
                    if column == "Chat Duration" and value is not None:
                        minutes = int(float(value) // 60)
                        seconds = int(float(value) % 60)
                        value = f"{minutes}:{seconds:02d}"
                    row_dict[column] = value if value is not None else ''
                results.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary-data', methods=['GET'])
def get_summary_data():
    try:
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        conn = db_connect()
        cursor = conn.cursor()

        where_clause = ""
        params = []
       
        # Build the date filter clause if valid dates are provided
        if from_date and to_date and from_date != 'null' and to_date != 'null':
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
                where_clause = "WHERE created_date BETWEEN %s AND %s"
                params = [from_date, to_date]
            except ValueError:
                pass

        # Query for total sessions
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM sf_chat_transcript_summary
            {where_clause}
        """, params)
        total_sessions = cursor.fetchone()[0]

        # If no data is found, remove the date filter and fetch all data
        if total_sessions == 0:
            where_clause = ""
            params = []
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM sf_chat_transcript_summary
            """)
            total_sessions = cursor.fetchone()[0]

        # Query for average handle time
        cursor.execute(f"""
            SELECT AVG(chat_duration)
            FROM sf_chat_transcript_summary
            WHERE chat_duration IS NOT NULL
            {' AND ' + where_clause[6:] if where_clause else ''}
        """, params)
        avg_handle_time = cursor.fetchone()[0] or 0
        avg_minutes = int(avg_handle_time // 60)
        avg_seconds = int(avg_handle_time % 60)
        aht = f"{avg_minutes}:{avg_seconds:02d}"

        # Query for resolution rate
        cursor.execute(f"""
            SELECT
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)
            FROM sf_chat_transcript_summary
            {where_clause}
        """, params)
        resolution_rate = cursor.fetchone()[0] or 0

        # Query for root causes
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN problem IS NULL OR problem = '' THEN 'Uncategorized'
                    ELSE problem
                END as name,
                COUNT(*) as sessions,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
            FROM sf_chat_transcript_summary
            {where_clause}
            GROUP BY
                CASE
                    WHEN problem IS NULL OR problem = '' THEN 'Uncategorized'
                    ELSE problem
                END
            ORDER BY sessions DESC
            LIMIT 6
        """, params)
        root_causes = [dict(zip(['name', 'sessions', 'percentage'],
                                [r[0], r[1], round(r[2], 1)])) for r in cursor.fetchall()]

        # Query for upvotes and downvotes
        cursor.execute(f"""
            SELECT
                COUNT(CASE WHEN ai_usage_id = 'Yes' THEN 1 END) as upvotes,
                COUNT(CASE WHEN ai_usage_id = 'No' THEN 1 END) as downvotes
            FROM sf_chat_transcript_summary
            {where_clause}
        """, params)
        votes = cursor.fetchone()
        upvotes = votes[0] or 0
        downvotes = votes[1] or 0

        cursor.close()
        conn.close()

        return jsonify({
            "totalSessions": total_sessions,
            "aht": aht,
            "resolutionRate": resolution_rate,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "rootCauses": root_causes
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products_data():
    try:
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        conn = db_connect()
        cursor = conn.cursor()

        # Constructing WHERE clause based on dates
        where_clause = ""
        params = []
        if from_date and to_date and from_date != 'null' and to_date != 'null':
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
                where_clause = "WHERE created_date BETWEEN %s AND %s"
                params = [from_date, to_date]
            except ValueError:
                print("Invalid date format received.")  # Debug log

        # Main query with optional WHERE clause
        query = f"""
            SELECT
                product as "Products",
                sub_product as "Sub Product",
                chat_duration as "AHT",
                problem as "Problem",
                root_cause as "Root cause"
            FROM sf_chat_transcript_summary
            {where_clause}
        """
       
        cursor.execute(query, params)

        # Processing results
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                if column == "AHT" and value is not None:
                    minutes = int(value // 60)
                    seconds = int(value % 60)
                    value = f"{minutes}:{seconds:02d}"
                row_dict[column] = value if value is not None else ''
            results.append(row_dict)

        # If no results are found, fetch all data
        if not results:
            print("No results found for the given date range. Fetching all data...")  # Debug log
            cursor.execute("""
                SELECT
                    product as "Products",
                    sub_product as "Sub Product",
                    chat_duration as "AHT",
                    problem as "Problem",
                    root_cause as "Root cause"
                FROM sf_chat_transcript_summary
            """)
            for row in cursor.fetchall():
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    if column == "AHT" and value is not None:
                        minutes = int(value // 60)
                        seconds = int(value % 60)
                        value = f"{minutes}:{seconds:02d}"
                    row_dict[column] = value if value is not None else ''
                results.append(row_dict)

        cursor.close()
        conn.close()

        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"Error in get_products_data: {str(e)}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    try:
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        conn = db_connect()
        cursor = conn.cursor()

        # First try with date range
        where_clause = ""
        params = []
        if from_date and to_date:
            where_clause = "WHERE created_date BETWEEN %s AND %s"
            params = [from_date, to_date]

        # Query for most upvoted categories
        upvoted_query = f"""
            SELECT 
                symptoms as item,
                'Symptom' as category,
                COUNT(*) as vote_count,
                array_agg(chat_transcript_id) as transcript_ids
            FROM sf_chat_transcript_summary
            {where_clause}
            {'AND ' if where_clause else 'WHERE '}ai_usage_id = 'Yes'
            GROUP BY symptoms
            HAVING COUNT(*) > 0
            ORDER BY vote_count DESC
            LIMIT 3
        """
        
        # Query for most downvoted categories
        downvoted_query = f"""
            SELECT 
                symptoms as item,
                'Symptom' as category,
                COUNT(*) as vote_count,
                array_agg(chat_transcript_id) as transcript_ids
            FROM sf_chat_transcript_summary
            {where_clause}
            {'AND ' if where_clause else 'WHERE '}ai_usage_id = 'No'
            GROUP BY symptoms
            HAVING COUNT(*) > 0
            ORDER BY vote_count DESC
            LIMIT 3
        """

        cursor.execute(upvoted_query, params)
        most_upvoted = [
            {
                'item': row[0],
                'category': row[1],
                'count': row[2],
                'transcript_ids': row[3]
            }
            for row in cursor.fetchall()
        ]

        cursor.execute(downvoted_query, params)
        most_downvoted = [
            {
                'item': row[0],
                'category': row[1],
                'count': row[2],
                'transcript_ids': row[3]
            }
            for row in cursor.fetchall()
        ]

        # If no results found with date range, fetch all-time data
        if not most_upvoted or not most_downvoted:
            upvoted_query = """
                SELECT 
                    symptoms as item,
                    'Symptom' as category,
                    COUNT(*) as vote_count,
                    array_agg(chat_transcript_id) as transcript_ids
                FROM sf_chat_transcript_summary
                WHERE ai_usage_id = 'Yes'
                GROUP BY symptoms
                HAVING COUNT(*) > 0
                ORDER BY vote_count DESC
                LIMIT 5
            """
            
            downvoted_query = """
                SELECT 
                    symptoms as item,
                    'Symptom' as category,
                    COUNT(*) as vote_count,
                    array_agg(chat_transcript_id) as transcript_ids
                FROM sf_chat_transcript_summary
                WHERE ai_usage_id = 'No'
                GROUP BY symptoms
                HAVING COUNT(*) > 0
                ORDER BY vote_count DESC
                LIMIT 5
            """

            cursor.execute(upvoted_query)
            most_upvoted = [
                {
                    'item': row[0],
                    'category': row[1],
                    'count': row[2],
                    'transcript_ids': row[3]
                }
                for row in cursor.fetchall()
            ]

            cursor.execute(downvoted_query)
            most_downvoted = [
                {
                    'item': row[0],
                    'category': row[1],
                    'count': row[2],
                    'transcript_ids': row[3]
                }
                for row in cursor.fetchall()
            ]

        cursor.close()
        conn.close()

        return jsonify({
            "mostUpvoted": most_upvoted,
            "mostDownvoted": most_downvoted
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback-details', methods=['GET'])
def get_feedback_details():
    try:
        item = request.args.get('item')
        feedback_type = request.args.get('type')
        transcript_ids = request.args.get('transcript_ids', '').split(',')
        
        if not transcript_ids or transcript_ids[0] == '':
            return jsonify([]), 200

        conn = db_connect()
        cursor = conn.cursor()

        # Convert transcript_ids to list of integers
        transcript_ids = [int(tid) for tid in transcript_ids if tid]

        query = """
            SELECT 
                chat_transcript_id,
                root_cause,
                symptoms,
                problem,
                product,
                CASE WHEN ai_usage_id = 'Yes' THEN 1 ELSE 0 END as upvotes,
                CASE WHEN ai_usage_id = 'No' THEN 1 ELSE 0 END as downvotes
            FROM sf_chat_transcript_summary
            WHERE chat_transcript_id = ANY(%s)
            ORDER BY chat_transcript_id DESC
            LIMIT 5
        """

        cursor.execute(query, (transcript_ids,))
        results = [
            {
                 'chat_transcript_id': row[0],
                'root_cause': row[1],
                'symptoms': row[2],
                'problem': row[3],
                'product': row[4],  # Added product to results
                'upvotes': row[5],
                'downvotes': row[6],
                'total_votes': row[5] + row[6]
            }
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return jsonify(results)

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)