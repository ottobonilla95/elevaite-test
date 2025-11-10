from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from database import get_db_connection
import traceback
from datetime import datetime
from decimal import Decimal
import pandas as pd
from io import BytesIO

router = APIRouter(prefix="/api/analytics/query-analytics")

def safe_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0

def build_chatbot_date_filter(start_date: Optional[str] = None, end_date: Optional[str] = None):
    date_filter = ""
    params = []
   
    if start_date and end_date:
        date_filter = "WHERE request_timestamp::date BETWEEN %s::date AND %s::date"  # Remove cdf. prefix
        params = [start_date, end_date]
    elif start_date:
        date_filter = "WHERE request_timestamp::date >= %s::date"  # Remove cdf. prefix
        params = [start_date]
    elif end_date:
        date_filter = "WHERE request_timestamp::date <= %s::date"  # Remove cdf. prefix
        params = [end_date]
   
    return date_filter, params
def build_fst_filter(manager_id: Optional[int] = None, fst_id: Optional[int] = None):
    """Build FST filtering for chatbot queries based on user_id"""
    fst_filter = ""
    fst_params = []
   
    if fst_id:
        # Filter by specific FST - match user_id to FST email or full name
        fst_filter = """
            AND cdf.user_id IN (
                SELECT ft.fst_email
                FROM fst_technicians ft
                WHERE ft.id = %s
                UNION
                SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                FROM fst_technicians ft
                WHERE ft.id = %s
            )
        """
        fst_params = [fst_id, fst_id]
    elif manager_id:
        # Filter by manager - get all FSTs under this manager
        fst_filter = """
            AND cdf.user_id IN (
                SELECT ft.fst_email
                FROM fst_technicians ft
                JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE fma.manager_id = %s
                UNION
                SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                FROM fst_technicians ft
                JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE fma.manager_id = %s
            )
        """
        fst_params = [manager_id, manager_id]
   
    return fst_filter, fst_params

def validate_date_range_for_export(start_date: Optional[str], end_date: Optional[str]):
    if not start_date and not end_date:
        return {
            "requires_date_range": True,
            "message": "Please select a date range to export data. Choose a start date and/or end date to limit the export."
        }
    return {"requires_date_range": False}

@router.get("/test-connection")
def test_chatbot_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM chat_data_final")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "status": "success",
            "message": f"Connected to chatbot database with {result['total']} records",
            "total_queries": result['total']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/date-range-info")
def get_query_date_range_info(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        cur.execute("""
            SELECT
                MIN(request_timestamp::date) as start_date,
                MAX(request_timestamp::date) as end_date,
                COUNT(*) as total_records
            FROM chat_data_final
            WHERE request_timestamp IS NOT NULL
        """)
        available_range = cur.fetchone()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine filters
        where_clauses = ["cdf.request_timestamp IS NOT NULL"]
        all_params = []
       
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
            all_params.extend(date_params)
       
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
            all_params.extend(fst_params)
       
        combined_filter = "WHERE " + " AND ".join(where_clauses)
       
        filtered_query = f"""
            SELECT
                MIN(cdf.request_timestamp::date) as start_date,
                MAX(cdf.request_timestamp::date) as end_date,
                COUNT(*) as total_records
            FROM chat_data_final cdf
            {combined_filter}
        """
       
        cur.execute(filtered_query, all_params)
        filtered_range = cur.fetchone()
        has_data_in_range = filtered_range['total_records'] > 0
       
        cur.close()
        conn.close()
       
        return {
            "available_range": {
                "start_date": available_range['start_date'].strftime('%Y-%m-%d') if available_range['start_date'] else None,
                "end_date": available_range['end_date'].strftime('%Y-%m-%d') if available_range['end_date'] else None,
                "total_records": available_range['total_records']
            },
            "filtered_range": {
                "start_date": filtered_range['start_date'].strftime('%Y-%m-%d') if filtered_range['start_date'] else None,
                "end_date": filtered_range['end_date'].strftime('%Y-%m-%d') if filtered_range['end_date'] else None,
                "total_records": filtered_range['total_records']
            },
            "has_data_in_range": has_data_in_range,
            "date_filter_applied": bool(date_filter),
            "fst_filter_applied": bool(fst_filter)
        }
       
    except Exception as e:
        traceback.print_exc()
        return {
            "available_range": {"start_date": None, "end_date": None, "total_records": 0},
            "filtered_range": {"start_date": None, "end_date": None, "total_records": 0},
            "has_data_in_range": False,
            "error": str(e)
        }

@router.get("/metrics")
def get_query_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        print(f"Query metrics with filters: start_date={start_date}, end_date={end_date}, manager_id={manager_id}, fst_id={fst_id}")
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine all parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = []
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        combined_filter = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
       
        # Basic metrics query
        basic_query = f"""
            SELECT
                COUNT(DISTINCT cdf.session_id) as total_sessions,
                COUNT(*) as total_queries,
                COUNT(DISTINCT cdf.user_id) as total_unique_users,
                ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT cdf.session_id), 0)::DECIMAL, 2) as queries_per_session
            FROM chat_data_final cdf
            {combined_filter}
        """
       
        cur.execute(basic_query, all_params)
        basic_metrics = cur.fetchone()
       
        # Feedback query
        feedback_query = f"""
            SELECT
                COUNT(*) FILTER (WHERE cdf.vote = 1) as thumbs_up_count,
                COUNT(*) FILTER (WHERE cdf.vote = -1) as thumbs_down_count,
                COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) as total_voted,
                COUNT(*) as total_queries_with_feedback_field
            FROM chat_data_final cdf
            {combined_filter}
        """
       
        cur.execute(feedback_query, all_params)
        feedback_data = cur.fetchone()
       
        total_queries = safe_float(basic_metrics['total_queries'])
        total_unique_users = safe_float(basic_metrics['total_unique_users'])
        thumbs_up_count = safe_float(feedback_data['thumbs_up_count'])
        thumbs_down_count = safe_float(feedback_data['thumbs_down_count'])
        total_voted = safe_float(feedback_data['total_voted'])
       
        method1_thumbs_up = round((thumbs_up_count / max(total_queries, 1)) * 100, 1)
        method1_thumbs_down = round((thumbs_down_count / max(total_queries, 1)) * 100, 1)
        method1_no_vote = round(((total_queries - total_voted) / max(total_queries, 1)) * 100, 1)
       
        method2_thumbs_up = round((thumbs_up_count / max(total_voted, 1)) * 100, 1)
        method2_thumbs_down = round((thumbs_down_count / max(total_voted, 1)) * 100, 1)
       
        engagement_rate = round((total_voted / max(total_queries, 1)) * 100, 1)
        satisfaction_score = method2_thumbs_up
       
        # Repeat queries analysis
        repeat_where_clauses = []
        repeat_params = []
       
        if date_filter:
            repeat_where_clauses.append(date_filter.replace("WHERE ", ""))
            repeat_params.extend(date_params)
        if fst_filter:
            repeat_where_clauses.append(fst_filter.replace("AND ", ""))
            repeat_params.extend(fst_params)
       
        repeat_where_clauses.append("cdf.request IS NOT NULL")
        repeat_where_clause = "WHERE " + " AND ".join(repeat_where_clauses)
       
        repeat_query = f"""
            WITH session_queries AS (
                SELECT
                    cdf.session_id,
                    LOWER(TRIM(cdf.request)) as normalized_query,
                    COUNT(*) as query_count
                FROM chat_data_final cdf
                {repeat_where_clause}
                GROUP BY cdf.session_id, LOWER(TRIM(cdf.request))
            ),
            repeat_analysis AS (
                SELECT
                    COUNT(*) FILTER (WHERE query_count > 1) as exact_repeats,
                    COUNT(DISTINCT session_id) as sessions_with_repeats,
                    SUM(query_count - 1) FILTER (WHERE query_count > 1) as total_repeat_instances
                FROM session_queries
            )
            SELECT
                exact_repeats,
                sessions_with_repeats,
                total_repeat_instances,
                ROUND((total_repeat_instances * 100.0 / NULLIF({total_queries}, 0)), 1) as repeat_percentage
            FROM repeat_analysis
        """
       
        cur.execute(repeat_query, repeat_params)
        repeat_data = cur.fetchone()
       
        # Response time analysis
        response_time_where_clauses = []
        response_time_params = []
       
        if date_filter:
            response_time_where_clauses.append(date_filter.replace("WHERE ", ""))
            response_time_params.extend(date_params)
        if fst_filter:
            response_time_where_clauses.append(fst_filter.replace("AND ", ""))
            response_time_params.extend(fst_params)
       
        response_time_where_clauses.extend([
            "cdf.response_timestamp IS NOT NULL",
            "cdf.request_timestamp IS NOT NULL",
            "cdf.response_timestamp > cdf.request_timestamp"
        ])
       
        response_time_where_clause = "WHERE " + " AND ".join(response_time_where_clauses)
       
        response_time_query = f"""
            SELECT
                AVG(EXTRACT(EPOCH FROM (cdf.response_timestamp - cdf.request_timestamp))) as avg_response_seconds
            FROM chat_data_final cdf
            {response_time_where_clause}
        """
        cur.execute(response_time_query, response_time_params)
        response_time = cur.fetchone()
       
        # Date range for daily averages
        date_range_where_clause = repeat_where_clause.replace("cdf.request IS NOT NULL", "cdf.request_timestamp IS NOT NULL")
       
        date_range_query = f"""
            SELECT
                MIN(cdf.request_timestamp::date) as min_date,
                MAX(cdf.request_timestamp::date) as max_date
            FROM chat_data_final cdf
            {date_range_where_clause}
        """
        cur.execute(date_range_query, repeat_params)
        date_range = cur.fetchone()
       
        # FIXED: Calculate daily averages properly
        avg_queries_per_day = 0
        avg_unique_users_per_day = 0
        days_with_data = 0
       
        if date_range and date_range['min_date'] and date_range['max_date']:
            # Calculate avg queries per day (existing logic is fine)
            days_diff = (date_range['max_date'] - date_range['min_date']).days + 1
            avg_queries_per_day = round(total_queries / days_diff, 1) if days_diff > 0 else 0
           
            # FIXED: Calculate avg unique users per day properly
            daily_users_where_clauses = []
            daily_users_params = []
           
            if date_filter:
                daily_users_where_clauses.append(date_filter.replace("WHERE ", ""))
                daily_users_params.extend(date_params)
            if fst_filter:
                daily_users_where_clauses.append(fst_filter.replace("AND ", ""))
                daily_users_params.extend(fst_params)
           
            daily_users_where_clauses.extend([
                "cdf.request_timestamp IS NOT NULL",
                "cdf.user_id IS NOT NULL"
            ])
           
            daily_users_where_clause = "WHERE " + " AND ".join(daily_users_where_clauses)
           
            daily_users_query = f"""
                SELECT
                    cdf.request_timestamp::date as query_date,
                    COUNT(DISTINCT cdf.user_id) as daily_unique_users
                FROM chat_data_final cdf
                {daily_users_where_clause}
                GROUP BY cdf.request_timestamp::date
                ORDER BY query_date
            """
           
            cur.execute(daily_users_query, daily_users_params)
            daily_user_counts = cur.fetchall()
           
            # Calculate average from actual daily counts
            if daily_user_counts:
                total_daily_users = sum(row['daily_unique_users'] for row in daily_user_counts)
                days_with_data = len(daily_user_counts)
                avg_unique_users_per_day = round(total_daily_users / days_with_data, 1)
       
        cur.close()
        conn.close()
       
        return {
            "total_sessions": int(basic_metrics['total_sessions'] or 0),
            "total_queries": int(total_queries),
            "total_unique_users": int(total_unique_users),
            "queries_per_session": float(basic_metrics['queries_per_session']) if basic_metrics['queries_per_session'] else 0,
            "avg_queries_per_day": avg_queries_per_day,
            "avg_unique_users_per_day": avg_unique_users_per_day,  # Now calculated correctly!
           
            "thumbs_up_percentage": method1_thumbs_up,
            "thumbs_down_percentage": method1_thumbs_down,
            "no_vote_percentage": method1_no_vote,
           
            "accuracy_percentage": satisfaction_score,
            "voter_satisfaction_rate": satisfaction_score,
            "engagement_rate": engagement_rate,
           
            "repeat_queries_percentage": safe_float(repeat_data['repeat_percentage']) if repeat_data else 0,
            "avg_response_time_seconds": round(safe_float(response_time['avg_response_seconds']) if response_time and response_time['avg_response_seconds'] else 0, 2),
           
            "_debug": {
                "method1_percentages": f"Thumbs Up: {method1_thumbs_up}%, Thumbs Down: {method1_thumbs_down}%, No Vote: {method1_no_vote}%",
                "method2_percentages": f"Thumbs Up: {method2_thumbs_up}%, Thumbs Down: {method2_thumbs_down}%",
                "total_voted": int(total_voted),
                "thumbs_up_count": int(thumbs_up_count),
                "thumbs_down_count": int(thumbs_down_count),
                "exact_repeats": int(repeat_data['exact_repeats']) if repeat_data else 0,
                "sessions_with_repeats": int(repeat_data['sessions_with_repeats']) if repeat_data else 0,
                "total_analyzed": int(total_queries),
                "total_unique_users": int(total_unique_users),
                "avg_unique_users_per_day": avg_unique_users_per_day,
                "days_with_data": days_with_data  # Shows actual days with data
            },
           
            "_calculation_method": "Method 1 for thumbs_up/down percentages, Method 2 for accuracy. Fixed avg_unique_users_per_day calculation.",
            "_source": "real_chatbot_database_with_fst_filtering",
            "_manager_filter_applied": bool(manager_id and not fst_id),
            "_fst_filter_applied": bool(fst_id)
        }
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/daily-trends")
def get_daily_query_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["cdf.request_timestamp IS NOT NULL"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        daily_query = f"""
            SELECT
                cdf.request_timestamp::date as query_date,
                COUNT(*) as daily_queries
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY cdf.request_timestamp::date
            ORDER BY query_date DESC
            LIMIT 30
        """
       
        cur.execute(daily_query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        formatted_results = []
        for row in reversed(results):
            formatted_results.append({
                "date": row['query_date'].strftime('%m/%d'),
                "value": row['daily_queries']
            })
       
        return formatted_results
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-unique-users")
def get_daily_unique_users_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["cdf.request_timestamp IS NOT NULL", "cdf.user_id IS NOT NULL"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        daily_users_query = f"""
            SELECT
                cdf.request_timestamp::date as query_date,
                COUNT(DISTINCT cdf.user_id) as daily_unique_users
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY cdf.request_timestamp::date
            ORDER BY query_date DESC
            LIMIT 30
        """
       
        cur.execute(daily_users_query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        formatted_results = []
        for row in reversed(results):
            formatted_results.append({
                "date": row['query_date'].strftime('%m/%d'),
                "value": row['daily_unique_users']
            })
       
        return formatted_results
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hourly-usage")
def get_hourly_usage(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["cdf.request_timestamp IS NOT NULL"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        query = f"""
            SELECT
                EXTRACT(HOUR FROM cdf.request_timestamp) as hour,
                COUNT(*) as query_count
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY EXTRACT(HOUR FROM cdf.request_timestamp)
            ORDER BY hour
        """
       
        cur.execute(query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        hourly_data = {}
        for row in results:
            hourly_data[int(row['hour'])] = row['query_count']
       
        formatted_results = []
        for hour in range(24):
            formatted_results.append({
                "hour": f"{hour:02d}:00",
                "queries": hourly_data.get(hour, 0)
            })
       
        return formatted_results
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback-queries")
def get_feedback_queries(
    feedback_type: str = Query(..., description="thumbs_up, thumbs_down, or no_feedback"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    limit: int = Query(50)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clauses
        where_clauses = []
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        # Handle different feedback types
        if feedback_type == "thumbs_up":
            where_clauses.extend([
                "cdf.vote = %s",
                "cdf.request IS NOT NULL"
            ])
            all_params.append(1)
        elif feedback_type == "thumbs_down":
            where_clauses.extend([
                "cdf.vote = %s",
                "cdf.request IS NOT NULL"
            ])
            all_params.append(-1)
        elif feedback_type == "no_feedback":
            where_clauses.extend([
                "(cdf.vote IS NULL OR cdf.vote = 0)",
                "cdf.request IS NOT NULL"
            ])
        else:
            raise HTTPException(status_code=400, detail="Invalid feedback_type. Must be 'thumbs_up', 'thumbs_down', or 'no_feedback'")
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        query = f"""
            SELECT
                cdf.request as query,
                cdf.response,
                cdf.request_timestamp,
                cdf.user_id,
                cdf.feedback,
                cdf.session_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT %s
        """
       
        all_params.append(limit)
       
        cur.execute(query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        return [{
            "query": row['query'],
            "response": row['response'][:200] + "..." if row['response'] and len(row['response']) > 200 else row['response'],
            "timestamp": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else None,
            "user": row['user_id'],
            "feedback": row['feedback'] or "",
            "session_id": str(row['session_id'])
        } for row in results]
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unresolved-queries")
def get_unresolved_queries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    limit: int = Query(20)
):
    """Get top unresolved queries (thumbs down with high frequency)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        print(f"DEBUG: Parameters - start_date={start_date}, manager_id={manager_id}, fst_id={fst_id}, limit={limit}")
       
        # Build the base date filter
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        print(f"DEBUG: date_filter={date_filter}, date_params={date_params}")
       
        # Build FST filter
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        print(f"DEBUG: fst_filter={fst_filter}, fst_params={fst_params}")
       
        # Combine all parameters
        all_params = date_params + fst_params
        print(f"DEBUG: all_params={all_params}")
       
        # Build WHERE clauses
        where_clauses = []
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
        where_clauses.append("cdf.request IS NOT NULL")
       
        main_where_clause = "WHERE " + " AND ".join(where_clauses)
        print(f"DEBUG: main_where_clause={main_where_clause}")
       
        # Simple query without CTE first to test
        query = f"""
            SELECT
                cdf.request as text,
                COUNT(*) as query_count,
                COUNT(*) FILTER (WHERE cdf.vote = -1) as thumbs_down_count,
                COUNT(*) FILTER (WHERE cdf.vote = 1) as thumbs_up_count,
                ROUND((COUNT(*) * 100.0 / (
                    SELECT COUNT(*) FROM chat_data_final cdf2 {main_where_clause.replace('cdf.', 'cdf2.')}
                )), 2) as percentage_of_total
            FROM chat_data_final cdf
            {main_where_clause}
            GROUP BY cdf.request
            HAVING COUNT(*) FILTER (WHERE cdf.vote = -1) > 0
            ORDER BY thumbs_down_count DESC, query_count DESC
            LIMIT %s
        """
       
        # We need to duplicate the parameters for the subquery
        final_params = all_params + all_params + [limit]
        print(f"DEBUG: final_params={final_params}")
        print(f"DEBUG: query={query}")
       
        cur.execute(query, final_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        unresolved_queries = []
        for row in results:
            feedback_status = "Mostly negative"
            if row['thumbs_up_count'] > row['thumbs_down_count']:
                feedback_status = "Mixed"
           
            confidence = max(10, 100 - (row['thumbs_down_count'] * 20))
           
            unresolved_queries.append({
                "text": row['text'],
                "count": row['query_count'],
                "percentage": f"{row['percentage_of_total']}%",
                "feedback": feedback_status,
                "botConfidence": f"{confidence}%",
                "thumbs_down_count": row['thumbs_down_count'],
                "thumbs_up_count": row['thumbs_up_count']
            })
       
        return unresolved_queries
       
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# You also need to add FST support to these functions. Add the parameters and filters:

@router.get("/metrics")
def get_query_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),  # ADD THIS
    fst_id: Optional[int] = Query(None)       # ADD THIS
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)  # ADD THIS
       
        # Combine parameters
        all_params = date_params + fst_params  # UPDATE THIS
       
        # Build where clause
        where_clauses = []
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))  # ADD THIS
       
        main_where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
       
        basic_query = f"""
            SELECT
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(*) as total_queries,
                COUNT(DISTINCT user_id) as total_unique_users,
                ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT session_id), 0)::DECIMAL, 2) as queries_per_session
            FROM chat_data_final
            {main_where}
        """
        cur.execute(basic_query, all_params)  # UPDATE THIS
        basic_metrics = cur.fetchone()
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/weekly-trends")
def get_weekly_query_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["cdf.request_timestamp IS NOT NULL"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        weekly_query = f"""
            SELECT
                DATE_TRUNC('week', cdf.request_timestamp)::date as week_start,
                COUNT(*) as weekly_queries
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY DATE_TRUNC('week', cdf.request_timestamp)
            ORDER BY week_start DESC
            LIMIT 12
        """
       
        cur.execute(weekly_query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        formatted_results = []
        for row in reversed(results):
            week_label = f"Week of {row['week_start'].strftime('%m/%d')}"
            formatted_results.append({
                "date": week_label,
                "value": row['weekly_queries']
            })
       
        return formatted_results
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly-trends")
def get_monthly_query_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["cdf.request_timestamp IS NOT NULL"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        monthly_query = f"""
            SELECT
                DATE_TRUNC('month', cdf.request_timestamp)::date as month_start,
                COUNT(*) as monthly_queries
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY DATE_TRUNC('month', cdf.request_timestamp)
            ORDER BY month_start DESC
            LIMIT 12
        """
       
        cur.execute(monthly_query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        formatted_results = []
        for row in reversed(results):
            month_label = row['month_start'].strftime('%b %y')
            formatted_results.append({
                "date": month_label,
                "value": row['monthly_queries']
            })
       
        return formatted_results
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/all-queries")
async def export_all_queries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Export ALL queries to Excel file"""
    try:
        validation = validate_date_range_for_export(start_date, end_date)
        if validation["requires_date_range"]:
            return {
                "error": "date_range_required",
                "message": validation["message"]
            }
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build WHERE clause step by step
        where_clauses = []
        params = []
       
        # Add date filter
        if start_date and end_date:
            where_clauses.append("cdf.request_timestamp::date BETWEEN %s::date AND %s::date")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("cdf.request_timestamp::date >= %s::date")
            params.append(start_date)
        elif end_date:
            where_clauses.append("cdf.request_timestamp::date <= %s::date")
            params.append(end_date)
       
        # Add FST filter
        if fst_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                )
            """)
            params.extend([fst_id, fst_id])
        elif manager_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                )
            """)
            params.extend([manager_id, manager_id])
       
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
       
        # Updated query with both request fields
        query = f"""
            SELECT
                cdf.qid,
                cdf.session_id,
                cdf.sr_ticket_id,
                cdf.original_request,
                cdf.request,
                cdf.request_timestamp,
                cdf.response,
                cdf.user_id,
                cdf.response_timestamp,
                cdf.vote,
                cdf.vote_timestamp,
                cdf.feedback,
                cdf.feedback_timestamp,
                cdf.agent_flow_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT 5000
        """
       
        cur.execute(query, params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        # Convert to DataFrame with updated mapping
        data = []
        for row in results:
            data.append({
                "Query ID": str(row['qid']),
                "Session ID": str(row['session_id']),
                "Original Request": row['original_request'] or "",
                "Processed Request": row['request'] or "",
                "Bot Response": row['response'] or "",  # Full response, no truncation
                "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                "User ID": row['user_id'] or "",
                "Vote": "Thumbs Up" if row['vote'] == 1 else "Thumbs Down" if row['vote'] == -1 else "No Vote",
                "Vote Time": row['vote_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['vote_timestamp'] else "",
                "Feedback": row['feedback'] or "",
                "Feedback Time": row['feedback_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['feedback_timestamp'] else "",
                "SR Ticket": row['sr_ticket_id'] or "",
                "Agent Flow ID": str(row['agent_flow_id']) if row['agent_flow_id'] else ""
            })
       
        df = pd.DataFrame(data)
       
        # Create Excel file with enhanced column widths
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Queries', index=False)
           
            worksheet = writer.sheets['All Queries']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
               
                # Customize widths based on column content
                if column_letter == 'C':             # Original Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'D':           # Processed Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'E':           # Bot Response  
                    adjusted_width = min(max_length + 2, 150)
                elif column_letter in ['F', 'G', 'I', 'J', 'L']:  # Timestamp columns
                    adjusted_width = 20
                elif column_letter in ['K', 'M']:    # Feedback and SR Ticket
                    adjusted_width = min(max_length + 2, 80)
                else:                                # Other columns
                    adjusted_width = min(max_length + 2, 35)
               
                worksheet.column_dimensions[column_letter].width = adjusted_width
       
        excel_buffer.seek(0)
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
       
        filename = f"all_queries{filter_suffix}_{timestamp}.xlsx"
       
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
@router.get("/export/thumbs-up")
async def export_thumbs_up_queries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Export ONLY thumbs up queries to Excel file"""
    try:
        validation = validate_date_range_for_export(start_date, end_date)
        if validation["requires_date_range"]:
            return {
                "error": "date_range_required",
                "message": validation["message"]
            }
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build WHERE clause step by step
        where_clauses = ["cdf.vote = 1"]  # Only thumbs up
        params = []
       
        # Add date filter
        if start_date and end_date:
            where_clauses.append("cdf.request_timestamp::date BETWEEN %s::date AND %s::date")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("cdf.request_timestamp::date >= %s::date")
            params.append(start_date)
        elif end_date:
            where_clauses.append("cdf.request_timestamp::date <= %s::date")
            params.append(end_date)
       
        # Add FST filter
        if fst_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                )
            """)
            params.extend([fst_id, fst_id])
        elif manager_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                )
            """)
            params.extend([manager_id, manager_id])
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        # Updated query with both request fields
        query = f"""
            SELECT
                cdf.qid,
                cdf.session_id,
                cdf.sr_ticket_id,
                cdf.original_request,
                cdf.request,
                cdf.request_timestamp,
                cdf.response,
                cdf.user_id,
                cdf.response_timestamp,
                cdf.vote,
                cdf.vote_timestamp,
                cdf.feedback,
                cdf.feedback_timestamp,
                cdf.agent_flow_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT 5000
        """
       
        cur.execute(query, params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        # Convert to DataFrame with updated mapping
        data = []
        for row in results:
            data.append({
                "Query ID": str(row['qid']),
                "Session ID": str(row['session_id']),
                "Original Request": row['original_request'] or "",
                "Processed Request": row['request'] or "",
                "Bot Response": row['response'] or "",  # Full response, no truncation
                "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                "User ID": row['user_id'] or "",
                "Vote": "Thumbs Up",  # Always thumbs up for this export
                "Vote Time": row['vote_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['vote_timestamp'] else "",
                "Feedback": row['feedback'] or "",
                "Feedback Time": row['feedback_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['feedback_timestamp'] else "",
                "SR Ticket": row['sr_ticket_id'] or "",
                "Agent Flow ID": str(row['agent_flow_id']) if row['agent_flow_id'] else ""
            })
       
        df = pd.DataFrame(data)
       
        # Create Excel file with enhanced column widths
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Thumbs Up Queries', index=False)
           
            worksheet = writer.sheets['Thumbs Up Queries']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
               
                # Customize widths based on column content
                if column_letter == 'C':             # Original Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'D':           # Processed Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'E':           # Bot Response  
                    adjusted_width = min(max_length + 2, 150)
                elif column_letter in ['F', 'G', 'I', 'J', 'L']:  # Timestamp columns
                    adjusted_width = 20
                elif column_letter in ['K', 'M']:    # Feedback and SR Ticket
                    adjusted_width = min(max_length + 2, 80)
                else:                                # Other columns
                    adjusted_width = min(max_length + 2, 35)
               
                worksheet.column_dimensions[column_letter].width = adjusted_width
       
        excel_buffer.seek(0)
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
           
        filename = f"thumbs_up_queries{filter_suffix}_{timestamp}.xlsx"
       
        return StreamingResponse(
            BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/thumbs-down")
async def export_thumbs_down_queries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Export ONLY thumbs down queries to Excel file"""
    try:
        validation = validate_date_range_for_export(start_date, end_date)
        if validation["requires_date_range"]:
            return {
                "error": "date_range_required",
                "message": validation["message"]
            }
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build WHERE clause step by step
        where_clauses = ["cdf.vote = -1"]  # Only thumbs down
        params = []
       
        # Add date filter
        if start_date and end_date:
            where_clauses.append("cdf.request_timestamp::date BETWEEN %s::date AND %s::date")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("cdf.request_timestamp::date >= %s::date")
            params.append(start_date)
        elif end_date:
            where_clauses.append("cdf.request_timestamp::date <= %s::date")
            params.append(end_date)
       
        # Add FST filter
        if fst_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                )
            """)
            params.extend([fst_id, fst_id])
        elif manager_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                )
            """)
            params.extend([manager_id, manager_id])
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        # Updated query with both request fields
        query = f"""
            SELECT
                cdf.qid,
                cdf.session_id,
                cdf.sr_ticket_id,
                cdf.original_request,
                cdf.request,
                cdf.request_timestamp,
                cdf.response,
                cdf.user_id,
                cdf.response_timestamp,
                cdf.vote,
                cdf.vote_timestamp,
                cdf.feedback,
                cdf.feedback_timestamp,
                cdf.agent_flow_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT 5000
        """
       
        cur.execute(query, params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        # Convert to DataFrame with updated mapping
        data = []
        for row in results:
            data.append({
                "Query ID": str(row['qid']),
                "Session ID": str(row['session_id']),
                "Original Request": row['original_request'] or "",
                "Processed Request": row['request'] or "",
                "Bot Response": row['response'] or "",  # Full response, no truncation
                "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                "User ID": row['user_id'] or "",
                "Vote": "Thumbs Down",  # Always thumbs down for this export
                "Vote Time": row['vote_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['vote_timestamp'] else "",
                "Feedback": row['feedback'] or "",
                "Feedback Time": row['feedback_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['feedback_timestamp'] else "",
                "SR Ticket": row['sr_ticket_id'] or "",
                "Agent Flow ID": str(row['agent_flow_id']) if row['agent_flow_id'] else ""
            })
       
        df = pd.DataFrame(data)
       
        # Create Excel file with enhanced column widths
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Thumbs Down Queries', index=False)
           
            worksheet = writer.sheets['Thumbs Down Queries']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
               
                # Customize widths based on column content
                if column_letter == 'C':             # Original Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'D':           # Processed Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'E':           # Bot Response  
                    adjusted_width = min(max_length + 2, 150)
                elif column_letter in ['F', 'G', 'I', 'J', 'L']:  # Timestamp columns
                    adjusted_width = 20
                elif column_letter in ['K', 'M']:    # Feedback and SR Ticket
                    adjusted_width = min(max_length + 2, 80)
                else:                                # Other columns
                    adjusted_width = min(max_length + 2, 35)
               
                worksheet.column_dimensions[column_letter].width = adjusted_width
       
        excel_buffer.seek(0)
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
           
        filename = f"thumbs_down_queries{filter_suffix}_{timestamp}.xlsx"
       
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
@router.get("/export/no-feedback")
async def export_no_feedback_queries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Export queries with no feedback/vote to Excel file"""
    try:
        validation = validate_date_range_for_export(start_date, end_date)
        if validation["requires_date_range"]:
            return {
                "error": "date_range_required",
                "message": validation["message"]
            }
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build WHERE clause step by step
        where_clauses = ["(cdf.vote IS NULL OR cdf.vote = 0)"]  # No feedback
        params = []
       
        # Add date filter
        if start_date and end_date:
            where_clauses.append("cdf.request_timestamp::date BETWEEN %s::date AND %s::date")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("cdf.request_timestamp::date >= %s::date")
            params.append(start_date)
        elif end_date:
            where_clauses.append("cdf.request_timestamp::date <= %s::date")
            params.append(end_date)
       
        # Add FST filter
        if fst_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    WHERE ft.id = %s
                )
            """)
            params.extend([fst_id, fst_id])
        elif manager_id:
            where_clauses.append("""
                cdf.user_id IN (
                    SELECT ft.fst_email
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                    UNION
                    SELECT LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                    FROM fst_technicians ft
                    JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE fma.manager_id = %s
                )
            """)
            params.extend([manager_id, manager_id])
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        # Updated query with both request fields
        query = f"""
            SELECT
                cdf.qid,
                cdf.session_id,
                cdf.sr_ticket_id,
                cdf.original_request,
                cdf.request,
                cdf.request_timestamp,
                cdf.response,
                cdf.user_id,
                cdf.response_timestamp,
                cdf.vote,
                cdf.vote_timestamp,
                cdf.feedback,
                cdf.feedback_timestamp,
                cdf.agent_flow_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT 5000
        """
       
        cur.execute(query, params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        # Convert to DataFrame with updated mapping
        data = []
        for row in results:
            data.append({
                "Query ID": str(row['qid']),
                "Session ID": str(row['session_id']),
                "Original Request": row['original_request'] or "",
                "Processed Request": row['request'] or "",
                "Bot Response": row['response'] or "",  # Full response, no truncation
                "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                "User ID": row['user_id'] or "",
                "Vote": "No Vote",  # Always no vote for this export
                "Vote Time": row['vote_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['vote_timestamp'] else "",
                "Feedback": row['feedback'] or "",
                "Feedback Time": row['feedback_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['feedback_timestamp'] else "",
                "SR Ticket": row['sr_ticket_id'] or "",
                "Agent Flow ID": str(row['agent_flow_id']) if row['agent_flow_id'] else ""
            })
       
        df = pd.DataFrame(data)
       
        # Create Excel file with enhanced column widths
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='No Feedback Queries', index=False)
           
            worksheet = writer.sheets['No Feedback Queries']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
               
                # Customize widths based on column content
                if column_letter == 'C':             # Original Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'D':           # Processed Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'E':           # Bot Response  
                    adjusted_width = min(max_length + 2, 150)
                elif column_letter in ['F', 'G', 'I', 'J', 'L']:  # Timestamp columns
                    adjusted_width = 20
                elif column_letter in ['K', 'M']:    # Feedback and SR Ticket
                    adjusted_width = min(max_length + 2, 80)
                else:                                # Other columns
                    adjusted_width = min(max_length + 2, 35)
               
                worksheet.column_dimensions[column_letter].width = adjusted_width
       
        excel_buffer.seek(0)
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
           
        filename = f"no_feedback_queries{filter_suffix}_{timestamp}.xlsx"
       
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
@router.get("/export/queries-with-fst-feedback")
async def export_queries_with_feedback(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Export queries that have written feedback from FSTs to Excel file"""
    try:
        validation = validate_date_range_for_export(start_date, end_date)
        if validation["requires_date_range"]:
            return {
                "error": "date_range_required",
                "message": validation["message"]
            }
       
        conn = get_db_connection()
        cur = conn.cursor()
       
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
       
        # Combine parameters
        all_params = date_params + fst_params
       
        # Build WHERE clause
        where_clauses = ["(cdf.feedback IS NOT NULL AND cdf.feedback != '')"]
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
       
        where_clause = "WHERE " + " AND ".join(where_clauses)
       
        # Updated query with both request fields
        query = f"""
            SELECT
                cdf.qid,
                cdf.session_id,
                cdf.sr_ticket_id,
                cdf.original_request,
                cdf.request,
                cdf.request_timestamp,
                cdf.response,
                cdf.user_id,
                cdf.response_timestamp,
                cdf.vote,
                cdf.vote_timestamp,
                cdf.feedback,
                cdf.feedback_timestamp,
                cdf.agent_flow_id
            FROM chat_data_final cdf
            {where_clause}
            ORDER BY cdf.request_timestamp DESC
            LIMIT 5000
        """
       
        cur.execute(query, all_params)
        results = cur.fetchall()
       
        cur.close()
        conn.close()
       
        # Convert to DataFrame with updated mapping
        data = []
        for row in results:
            data.append({
                "Query ID": str(row['qid']),
                "Session ID": str(row['session_id']),
                "Original Request": row['original_request'] or "",
                "Processed Request": row['request'] or "",
                "Bot Response": row['response'] or "",  # Full response, no truncation
                "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                "User ID": row['user_id'] or "",
                "Vote": "Thumbs Up" if row['vote'] == 1 else "Thumbs Down" if row['vote'] == -1 else "No Vote",
                "Vote Time": row['vote_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['vote_timestamp'] else "",
                "FST Feedback": row['feedback'] or "",  # This is the written feedback from FSTs
                "Feedback Time": row['feedback_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['feedback_timestamp'] else "",
                "SR Ticket": row['sr_ticket_id'] or "",
                "Agent Flow ID": str(row['agent_flow_id']) if row['agent_flow_id'] else ""
            })
       
        df = pd.DataFrame(data)
       
        # Create Excel file with enhanced column widths
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Queries with Feedback', index=False)
           
            worksheet = writer.sheets['Queries with Feedback']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
               
                # Customize widths based on column content
                if column_letter == 'C':             # Original Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'D':           # Processed Request
                    adjusted_width = min(max_length + 2, 120)
                elif column_letter == 'E':           # Bot Response  
                    adjusted_width = min(max_length + 2, 150)
                elif column_letter == 'K':           # FST Feedback - make this wider for detailed feedback
                    adjusted_width = min(max_length + 2, 100)
                elif column_letter in ['F', 'G', 'I', 'J', 'L']:  # Timestamp columns
                    adjusted_width = 20
                elif column_letter == 'M':           # SR Ticket
                    adjusted_width = min(max_length + 2, 80)
                else:                                # Other columns
                    adjusted_width = min(max_length + 2, 35)
               
                worksheet.column_dimensions[column_letter].width = adjusted_width
       
        excel_buffer.seek(0)
       
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
           
        filename = f"queries_with_feedback{filter_suffix}_{timestamp}.xlsx"
       
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
       
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    
@router.get("/classification-metrics")
def get_classification_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get query classification breakdown for pie chart"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_chatbot_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        
        # Combine parameters
        all_params = date_params + fst_params
        
        # Build WHERE clause
        where_clauses = []
        if date_filter:
            where_clauses.append(date_filter.replace("WHERE ", ""))
        if fst_filter:
            where_clauses.append(fst_filter.replace("AND ", ""))
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Query Type Distribution
        query_type_query = f"""
            SELECT
                COALESCE(cdf.query_type, 'Unknown') as query_type,
                COUNT(*) as count,
                ROUND((COUNT(*) * 100.0 / (
                    SELECT COUNT(*) FROM chat_data_final cdf2 {where_clause.replace('cdf.', 'cdf2.')}
                )), 2) as percentage
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY cdf.query_type
            ORDER BY count DESC
        """
        
        # Duplicate params for subquery
        query_type_params = all_params + all_params
        cur.execute(query_type_query, query_type_params)
        query_types = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "query_types": [
                {
                    "type": row['query_type'],
                    "count": int(row['count']),
                    "percentage": float(row['percentage'])
                }
                for row in query_types
            ],
            "_source": "real_chatbot_database_with_fst_filtering"
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))