from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from database import get_db_connection
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from io import BytesIO

router = APIRouter(prefix="/api/analytics/user-analytics")



# Define excluded emails and domains at the top for easy maintenance
EXCLUDED_EMAILS = [
    'walker.franklin@toshibagcs.com',
    'thomas.conway@toshibagcs.com'
]

EXCLUDED_DOMAINS = [
    '@iopex.com'
]

def safe_float(value):
    """Safely convert value to float"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0

def build_user_date_filter(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Build date filter for user analytics queries"""
    date_filter = ""
    params = []
    
    if start_date and end_date:
        date_filter = "request_timestamp::date BETWEEN %s::date AND %s::date"
        params = [start_date, end_date]
    elif start_date:
        date_filter = "request_timestamp::date >= %s::date"
        params = [start_date]
    elif end_date:
        date_filter = "request_timestamp::date <= %s::date"
        params = [end_date]
    
    return date_filter, params

def build_email_exclusion_filter():
    """Build email exclusion filter for both specific emails and domains"""
    exclusions = []
    params = []
    
    # Add specific email exclusions
    if EXCLUDED_EMAILS:
        email_placeholders = ', '.join(['%s'] * len(EXCLUDED_EMAILS))
        exclusions.append(f"cdf.user_id NOT IN ({email_placeholders})")
        params.extend(EXCLUDED_EMAILS)
    
    # Add domain exclusions
    if EXCLUDED_DOMAINS:
        for domain in EXCLUDED_DOMAINS:
            exclusions.append("cdf.user_id NOT LIKE %s")
            params.append(f"%{domain}")
    
    if exclusions:
        exclusion_filter = " AND ".join(exclusions)
        return exclusion_filter, params
    
    return "", []

def build_fst_filter(manager_id: Optional[int] = None, fst_id: Optional[int] = None):
    """Build FST filtering for user analytics based on user_id"""
    fst_filter = ""
    fst_params = []
    
    if fst_id:
        # Filter by specific FST - match user_id to FST email only
        fst_filter = """cdf.user_id = (
                SELECT ft.fst_email 
                FROM fst_technicians ft 
                WHERE ft.id = %s
            )"""
        fst_params = [fst_id]
    elif manager_id:
        # Filter by manager - get all FSTs under this manager
        fst_filter = """cdf.user_id IN (
                SELECT ft.fst_email 
                FROM fst_technicians ft
                JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE fma.manager_id = %s
            )"""
        fst_params = [manager_id]
    
    return fst_filter, fst_params

def build_combined_where_clause(date_filter=None, fst_filter=None, exclusion_filter=None, additional_conditions=None):
    """Build a combined WHERE clause from multiple filter conditions"""
    where_clauses = ["cdf.user_id IS NOT NULL", "cdf.request_timestamp IS NOT NULL"]
    
    if date_filter:
        where_clauses.append(date_filter)
    if fst_filter:
        where_clauses.append(fst_filter)
    if exclusion_filter:
        where_clauses.append(exclusion_filter)
    if additional_conditions:
        if isinstance(additional_conditions, list):
            where_clauses.extend(additional_conditions)
        else:
            where_clauses.append(additional_conditions)
    
    return "WHERE " + " AND ".join(where_clauses)

def validate_date_range_for_export(start_date: Optional[str], end_date: Optional[str]):
    """Validate if date range is provided for export"""
    if not start_date and not end_date:
        return {
            "requires_date_range": True,
            "message": "Please select a date range to export user data. Choose a start date and/or end date to limit the export."
        }
    return {"requires_date_range": False}

@router.get("/test-connection")
def test_user_analytics_connection():
    """Test connection to user analytics data"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Add email exclusion to test query
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        where_clause = build_combined_where_clause(exclusion_filter=exclusion_filter)
        
        query = f"""
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(*) as total_queries,
                COUNT(DISTINCT session_id) as total_sessions
            FROM chat_data_final cdf
            {where_clause}
        """
        
        cur.execute(query, exclusion_params)
        result = cur.fetchone()
        
        # Get count of excluded users for reporting
        if EXCLUDED_EMAILS or EXCLUDED_DOMAINS:
            excluded_conditions = []
            excluded_params = []
            
            if EXCLUDED_EMAILS:
                email_placeholders = ', '.join(['%s'] * len(EXCLUDED_EMAILS))
                excluded_conditions.append(f"cdf.user_id IN ({email_placeholders})")
                excluded_params.extend(EXCLUDED_EMAILS)
            
            if EXCLUDED_DOMAINS:
                for domain in EXCLUDED_DOMAINS:
                    excluded_conditions.append("cdf.user_id LIKE %s")
                    excluded_params.append(f"%{domain}")
            
            excluded_count_query = f"""
                SELECT COUNT(DISTINCT user_id) as excluded_users
                FROM chat_data_final cdf
                WHERE user_id IS NOT NULL
                AND ({' OR '.join(excluded_conditions)})
            """
            
            cur.execute(excluded_count_query, excluded_params)
            excluded_result = cur.fetchone()
        else:
            excluded_result = {'excluded_users': 0}
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": "Connected to user analytics database",
            "total_users": result['total_users'],
            "total_queries": result['total_queries'],
            "total_sessions": result['total_sessions'],
            "excluded_users": excluded_result['excluded_users'] if excluded_result else 0,
            "exclusion_rules": {
                "excluded_emails": EXCLUDED_EMAILS,
                "excluded_domains": EXCLUDED_DOMAINS
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/user-metrics")
def get_user_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get overall user metrics and statistics with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
        # Get overall user metrics
        metrics_query = f"""
            WITH user_stats AS (
                SELECT 
                    cdf.user_id,
                    COUNT(*) as user_queries,
                    COUNT(DISTINCT cdf.session_id) as user_sessions,
                    MIN(cdf.request_timestamp) as first_query
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
            ),
            most_active AS (
                SELECT user_id, user_queries
                FROM user_stats
                ORDER BY user_queries DESC
                LIMIT 1
            ),
            newest_user AS (
                SELECT user_id
                FROM user_stats
                ORDER BY first_query DESC
                LIMIT 1
            )
            SELECT 
                COUNT(DISTINCT us.user_id) as total_unique_users,
                ROUND(AVG(us.user_queries), 1) as avg_queries_per_user,
                ROUND(AVG(us.user_sessions), 1) as avg_sessions_per_user,
                (SELECT user_id FROM most_active) as most_active_user,
                (SELECT user_id FROM newest_user) as newest_user
            FROM user_stats us
        """
        
        cur.execute(metrics_query, all_params)
        metrics_result = cur.fetchone()
        
        # Calculate user growth rate (comparing to previous period)
        growth_rate = 0
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                period_length = (end_dt - start_dt).days
                
                prev_start = (start_dt - timedelta(days=period_length)).strftime('%Y-%m-%d')
                prev_end = (end_dt - timedelta(days=period_length)).strftime('%Y-%m-%d')
                
                # Build previous period query with FST filtering and email exclusion
                prev_date_filter = "cdf.request_timestamp::date BETWEEN %s::date AND %s::date"
                prev_date_params = [prev_start, prev_end] + fst_params + exclusion_params
                prev_where_clause = build_combined_where_clause(prev_date_filter, fst_filter, exclusion_filter)
                
                prev_query = f"""
                    SELECT COUNT(DISTINCT cdf.user_id) as prev_users
                    FROM chat_data_final cdf
                    {prev_where_clause}
                """
                cur.execute(prev_query, prev_date_params)
                prev_result = cur.fetchone()
                
                current_users = metrics_result['total_unique_users']
                prev_users = prev_result['prev_users'] if prev_result else 0
                
                if prev_users > 0:
                    growth_rate = ((current_users - prev_users) / prev_users) * 100
            except Exception as e:
                print(f"Growth rate calculation error: {e}")
                growth_rate = 0
        
        cur.close()
        conn.close()
        
        return {
            "total_unique_users": metrics_result['total_unique_users'] or 0,
            "avg_queries_per_user": float(metrics_result['avg_queries_per_user'] or 0),
            "avg_sessions_per_user": float(metrics_result['avg_sessions_per_user'] or 0),
            "most_active_user": metrics_result['most_active_user'] or "",
            "newest_user": metrics_result['newest_user'] or "",
            "user_growth_rate": round(growth_rate, 1),
            "exclusion_rules": {
                "excluded_emails": EXCLUDED_EMAILS,
                "excluded_domains": EXCLUDED_DOMAINS
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-users")
def get_top_users(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    limit: int = Query(10)
):
    """Get top users by query volume with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params + [limit]
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
        query = f"""
            SELECT 
                cdf.user_id,
                COUNT(*) as total_queries,
                COUNT(DISTINCT cdf.session_id) as total_sessions,
                MAX(cdf.request_timestamp) as last_active,
                ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT cdf.session_id), 0)::DECIMAL, 2) as avg_queries_per_session,
                COUNT(DISTINCT DATE(cdf.request_timestamp)) as days_active,
                COUNT(*) FILTER (WHERE cdf.vote = 1) as thumbs_up_count,
                COUNT(*) FILTER (WHERE cdf.vote = -1) as thumbs_down_count,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) > 0 
                        THEN (COUNT(*) FILTER (WHERE cdf.vote = 1) * 100.0 / COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0))
                        ELSE 0 
                    END, 1
                ) as satisfaction_rate
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY cdf.user_id
            ORDER BY total_queries DESC
            LIMIT %s
        """
        
        cur.execute(query, all_params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "user_id": row['user_id'],
            "total_queries": row['total_queries'],
            "total_sessions": row['total_sessions'],
            "last_active": row['last_active'].strftime("%Y-%m-%d %H:%M:%S") if row['last_active'] else None,
            "avg_queries_per_session": float(row['avg_queries_per_session']) if row['avg_queries_per_session'] else 0,
            "days_active": row['days_active'],
            "satisfaction_rate": float(row['satisfaction_rate']),
            "thumbs_up_count": row['thumbs_up_count'],
            "thumbs_down_count": row['thumbs_down_count']
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-breakdown")
def get_user_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    page: int = Query(1),
    page_size: int = Query(50)
):
    """Get detailed user breakdown with pagination, FST filtering, and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params + [page_size, offset]
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
        query = f"""
            SELECT 
                cdf.user_id,
                COUNT(*) as total_queries,
                COUNT(DISTINCT cdf.session_id) as total_sessions,
                MIN(cdf.request_timestamp) as first_query,
                MAX(cdf.request_timestamp) as last_active,
                ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT DATE(cdf.request_timestamp)), 0)::DECIMAL, 1) as avg_queries_per_day,
                ROUND(
                    CASE 
                        WHEN COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) > 0 
                        THEN (COUNT(*) FILTER (WHERE cdf.vote = 1) * 100.0 / COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0))
                        ELSE 0 
                    END, 1
                ) as satisfaction_rate,
                MODE() WITHIN GROUP (ORDER BY EXTRACT(HOUR FROM cdf.request_timestamp)) as most_active_hour,
                ROUND(
                    (COUNT(DISTINCT LOWER(TRIM(cdf.request))) * 100.0 / COUNT(*)), 1
                ) as repeat_query_rate
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY cdf.user_id
            ORDER BY total_queries DESC
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, all_params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "user_id": row['user_id'],
            "total_queries": row['total_queries'],
            "total_sessions": row['total_sessions'],
            "first_query": row['first_query'].strftime("%Y-%m-%d %H:%M:%S") if row['first_query'] else None,
            "last_active": row['last_active'].strftime("%Y-%m-%d %H:%M:%S") if row['last_active'] else None,
            "avg_queries_per_day": float(row['avg_queries_per_day']) if row['avg_queries_per_day'] else 0,
            "satisfaction_rate": float(row['satisfaction_rate']),
            "most_active_hour": int(row['most_active_hour']) if row['most_active_hour'] else 0,
            "repeat_query_rate": float(row['repeat_query_rate']) if row['repeat_query_rate'] else 0
        } for row in results]
        
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
    """Get daily unique users trends with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
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

@router.get("/export/user-data")
async def export_user_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """Export user analytics data to Excel with FST filtering and email exclusion"""
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
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        additional_conditions = []
        if user_id:
            additional_conditions.append("cdf.user_id = %s")
            all_params.append(user_id)
        
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter, additional_conditions)
        
        if user_id:
            # Export specific user's queries
            query = f"""
                SELECT 
                    cdf.qid,
                    cdf.session_id,
                    cdf.user_id,
                    cdf.request as original_request,
                    cdf.response,
                    cdf.request_timestamp,
                    cdf.response_timestamp,
                    cdf.vote,
                    cdf.feedback,
                    cdf.sr_ticket_id
                FROM chat_data_final cdf
                {where_clause}
                ORDER BY cdf.request_timestamp DESC
                LIMIT 5000
            """
        else:
            # Export user analytics summary
            query = f"""
                SELECT 
                    cdf.user_id,
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT cdf.session_id) as total_sessions,
                    MIN(cdf.request_timestamp) as first_query,
                    MAX(cdf.request_timestamp) as last_active,
                    COUNT(DISTINCT DATE(cdf.request_timestamp)) as active_days,
                    ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT cdf.session_id), 0)::DECIMAL, 2) as avg_queries_per_session,
                    COUNT(*) FILTER (WHERE cdf.vote = 1) as thumbs_up_count,
                    COUNT(*) FILTER (WHERE cdf.vote = -1) as thumbs_down_count,
                    ROUND(
                        CASE 
                            WHEN COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) > 0 
                            THEN (COUNT(*) FILTER (WHERE cdf.vote = 1) * 100.0 / COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0))
                            ELSE 0 
                        END, 1
                    ) as satisfaction_rate,
                    MODE() WITHIN GROUP (ORDER BY EXTRACT(HOUR FROM cdf.request_timestamp)) as most_active_hour
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
                ORDER BY total_queries DESC
                LIMIT 5000
            """
        
        cur.execute(query, all_params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Prepare data for Excel
        data = []
        if user_id:
            # Individual user query data
            for row in results:
                data.append({
                    "Query ID": str(row['qid']),
                    "Session ID": str(row['session_id']),
                    "User ID": row['user_id'],
                    "Query": row['original_request'],
                    "Response": row['response'][:500] + "..." if row['response'] and len(row['response']) > 500 else row['response'],
                    "Request Time": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                    "Response Time": row['response_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['response_timestamp'] else "",
                    "Vote": "Thumbs Up" if row['vote'] == 1 else "Thumbs Down" if row['vote'] == -1 else "No Vote",
                    "Feedback": row['feedback'] or "",
                    "SR Ticket": row['sr_ticket_id'] or ""
                })
            sheet_name = f'User {user_id} Queries'
        else:
            # User analytics summary
            for row in results:
                data.append({
                    "User ID": row['user_id'],
                    "Total Queries": row['total_queries'],
                    "Total Sessions": row['total_sessions'],
                    "First Query": row['first_query'].strftime("%Y-%m-%d %H:%M:%S") if row['first_query'] else "",
                    "Last Active": row['last_active'].strftime("%Y-%m-%d %H:%M:%S") if row['last_active'] else "",
                    "Active Days": row['active_days'],
                    "Avg Queries/Session": float(row['avg_queries_per_session']) if row['avg_queries_per_session'] else 0,
                    "Thumbs Up": row['thumbs_up_count'],
                    "Thumbs Down": row['thumbs_down_count'],
                    "Satisfaction Rate": f"{row['satisfaction_rate']}%",
                    "Most Active Hour": f"{row['most_active_hour']}:00" if row['most_active_hour'] else "N/A"
                })
            sheet_name = 'User Analytics'
        
        df = pd.DataFrame(data)
        
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 80)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        
        # Generate filename with FST filter info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_suffix = ""
        if user_id:
            filter_suffix = f"_user_{user_id}"
        elif fst_id:
            filter_suffix = f"_fst_{fst_id}"
        elif manager_id:
            filter_suffix = f"_manager_{manager_id}"
        
        if user_id:
            filename = f"user_{user_id}_queries{filter_suffix}_{timestamp}.xlsx"
        else:
            filename = f"user_analytics{filter_suffix}_{timestamp}.xlsx"
        
        return StreamingResponse(
            BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/user-activity-patterns")
def get_user_activity_patterns(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """Get user activity patterns by hour and day with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        # Build WHERE clause
        additional_conditions = []
        if user_id:
            additional_conditions.append("cdf.user_id = %s")
            all_params.append(user_id)
        
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter, additional_conditions)
        
        # Hourly activity pattern
        hourly_query = f"""
            SELECT 
                EXTRACT(HOUR FROM cdf.request_timestamp) as hour,
                COUNT(*) as query_count,
                COUNT(DISTINCT cdf.user_id) as unique_users
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY EXTRACT(HOUR FROM cdf.request_timestamp)
            ORDER BY hour
        """
        
        cur.execute(hourly_query, all_params)
        hourly_results = cur.fetchall()
        
        # Daily activity pattern (day of week)
        daily_query = f"""
            SELECT 
                EXTRACT(DOW FROM cdf.request_timestamp) as day_of_week,
                TO_CHAR(cdf.request_timestamp, 'Day') as day_name,
                COUNT(*) as query_count,
                COUNT(DISTINCT cdf.user_id) as unique_users
            FROM chat_data_final cdf
            {where_clause}
            GROUP BY EXTRACT(DOW FROM cdf.request_timestamp), TO_CHAR(cdf.request_timestamp, 'Day')
            ORDER BY day_of_week
        """
        
        cur.execute(daily_query, all_params)
        daily_results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format hourly data
        hourly_data = {}
        for row in hourly_results:
            hourly_data[int(row['hour'])] = {
                "query_count": row['query_count'],
                "unique_users": row['unique_users']
            }
        
        hourly_formatted = []
        for hour in range(24):
            data = hourly_data.get(hour, {"query_count": 0, "unique_users": 0})
            hourly_formatted.append({
                "hour": f"{hour:02d}:00",
                "queries": data["query_count"],
                "users": data["unique_users"]
            })
        
        # Format daily data
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        daily_data = {}
        for row in daily_results:
            daily_data[int(row['day_of_week'])] = {
                "day_name": row['day_name'].strip(),
                "query_count": row['query_count'],
                "unique_users": row['unique_users']
            }
        
        daily_formatted = []
        for dow in range(7):
            data = daily_data.get(dow, {"day_name": day_names[dow], "query_count": 0, "unique_users": 0})
            daily_formatted.append({
                "day": data["day_name"],
                "queries": data["query_count"],
                "users": data["unique_users"]
            })
        
        return {
            "hourly_patterns": hourly_formatted,
            "daily_patterns": daily_formatted
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-engagement-analysis")
def get_user_engagement_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get user engagement analysis with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
        # User engagement distribution
        engagement_query = f"""
            WITH user_query_counts AS (
                SELECT 
                    cdf.user_id,
                    COUNT(*) as query_count
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
            )
            SELECT 
                CASE 
                    WHEN query_count >= 50 THEN 'Very High (50+)'
                    WHEN query_count >= 20 THEN 'High (20-49)'
                    WHEN query_count >= 10 THEN 'Medium (10-19)'
                    WHEN query_count >= 5 THEN 'Low (5-9)'
                    ELSE 'Very Low (1-4)'
                END as engagement_level,
                COUNT(*) as user_count,
                ROUND(AVG(query_count), 1) as avg_queries,
                MIN(query_count) as min_queries,
                MAX(query_count) as max_queries
            FROM user_query_counts
            GROUP BY 
                CASE 
                    WHEN query_count >= 50 THEN 'Very High (50+)'
                    WHEN query_count >= 20 THEN 'High (20-49)'
                    WHEN query_count >= 10 THEN 'Medium (10-19)'
                    WHEN query_count >= 5 THEN 'Low (5-9)'
                    ELSE 'Very Low (1-4)'
                END
            ORDER BY MIN(query_count) DESC
        """
        
        cur.execute(engagement_query, all_params)
        engagement_results = cur.fetchall()
        
        # Session engagement analysis
        session_engagement_query = f"""
            WITH user_session_data AS (
                SELECT 
                    cdf.user_id,
                    COUNT(DISTINCT cdf.session_id) as session_count,
                    COUNT(*) as total_queries,
                    ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT cdf.session_id), 0)::DECIMAL, 1) as avg_queries_per_session
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
            )
            SELECT 
                CASE 
                    WHEN avg_queries_per_session >= 10 THEN 'High Session Engagement (10+ q/s)'
                    WHEN avg_queries_per_session >= 5 THEN 'Medium Session Engagement (5-9 q/s)'
                    WHEN avg_queries_per_session >= 2 THEN 'Low Session Engagement (2-4 q/s)'
                    ELSE 'Very Low Session Engagement (1 q/s)'
                END as session_engagement_level,
                COUNT(*) as user_count,
                ROUND(AVG(avg_queries_per_session), 1) as avg_queries_per_session,
                ROUND(AVG(session_count), 1) as avg_sessions_per_user
            FROM user_session_data
            GROUP BY 
                CASE 
                    WHEN avg_queries_per_session >= 10 THEN 'High Session Engagement (10+ q/s)'
                    WHEN avg_queries_per_session >= 5 THEN 'Medium Session Engagement (5-9 q/s)'
                    WHEN avg_queries_per_session >= 2 THEN 'Low Session Engagement (2-4 q/s)'
                    ELSE 'Very Low Session Engagement (1 q/s)'
                END
            ORDER BY avg_queries_per_session DESC
        """
        
        cur.execute(session_engagement_query, all_params)
        session_results = cur.fetchall()
        
        # Feedback engagement analysis
        feedback_engagement_query = f"""
            WITH user_feedback_data AS (
                SELECT 
                    cdf.user_id,
                    COUNT(*) as total_queries,
                    COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) as voted_queries,
                    COUNT(*) FILTER (WHERE cdf.feedback IS NOT NULL AND cdf.feedback != '') as feedback_queries,
                    ROUND(
                        (COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) * 100.0) / 
                        NULLIF(COUNT(*), 0), 1
                    ) as vote_rate,
                    ROUND(
                        (COUNT(*) FILTER (WHERE cdf.feedback IS NOT NULL AND cdf.feedback != '') * 100.0) / 
                        NULLIF(COUNT(*), 0), 1
                    ) as feedback_rate
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
                HAVING COUNT(*) >= 5  -- Only users with at least 5 queries
            )
            SELECT 
                CASE 
                    WHEN vote_rate >= 50 THEN 'High Feedback Engagement (50%+ vote)'
                    WHEN vote_rate >= 25 THEN 'Medium Feedback Engagement (25-49% vote)'
                    WHEN vote_rate >= 10 THEN 'Low Feedback Engagement (10-24% vote)'
                    ELSE 'Very Low Feedback Engagement (<10% vote)'
                END as feedback_engagement_level,
                COUNT(*) as user_count,
                ROUND(AVG(vote_rate), 1) as avg_vote_rate,
                ROUND(AVG(feedback_rate), 1) as avg_feedback_rate
            FROM user_feedback_data
            GROUP BY 
                CASE 
                    WHEN vote_rate >= 50 THEN 'High Feedback Engagement (50%+ vote)'
                    WHEN vote_rate >= 25 THEN 'Medium Feedback Engagement (25-49% vote)'
                    WHEN vote_rate >= 10 THEN 'Low Feedback Engagement (10-24% vote)'
                    ELSE 'Very Low Feedback Engagement (<10% vote)'
                END
            ORDER BY avg_vote_rate DESC
        """
        
        cur.execute(feedback_engagement_query, all_params)
        feedback_results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "query_engagement_distribution": [
                {
                    "level": row['engagement_level'],
                    "user_count": row['user_count'],
                    "avg_queries": row['avg_queries'],
                    "min_queries": row['min_queries'],
                    "max_queries": row['max_queries']
                } for row in engagement_results
            ],
            "session_engagement_distribution": [
                {
                    "level": row['session_engagement_level'],
                    "user_count": row['user_count'],
                    "avg_queries_per_session": row['avg_queries_per_session'],
                    "avg_sessions_per_user": row['avg_sessions_per_user']
                } for row in session_results
            ],
            "feedback_engagement_distribution": [
                {
                    "level": row['feedback_engagement_level'],
                    "user_count": row['user_count'],
                    "avg_vote_rate": row['avg_vote_rate'],
                    "avg_feedback_rate": row['avg_feedback_rate']
                } for row in feedback_results
            ]
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/user-recent-sessions")
def get_user_recent_sessions(
    user_id: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit_sessions: int = Query(3)
):
    """Get user's most recent chat sessions with all queries in each session"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Build WHERE clause with user filter
        additional_conditions = ["cdf.user_id = %s"]
        where_clause = build_combined_where_clause(date_filter, None, exclusion_filter, additional_conditions)
        
        # Combine parameters - user_id first, then limit_sessions
        all_params = date_params + exclusion_params + [user_id, limit_sessions]
        
        # Get user's recent sessions (last N complete sessions)
        query = f"""
            WITH recent_sessions AS (
                SELECT 
                    session_id,
                    MAX(request_timestamp) as last_activity
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY session_id
                ORDER BY last_activity DESC
                LIMIT %s
            ),
            session_queries AS (
                SELECT 
                    cdf.qid,
                    cdf.session_id,
                    cdf.user_id,
                    cdf.request as original_request,
                    cdf.response,
                    cdf.request_timestamp,
                    cdf.response_timestamp,
                    cdf.vote,
                    cdf.feedback,
                    cdf.sr_ticket_id
                FROM chat_data_final cdf
                JOIN recent_sessions rs ON cdf.session_id = rs.session_id
                WHERE cdf.user_id = %s
            )
            SELECT * FROM session_queries
            ORDER BY session_id DESC, request_timestamp ASC
        """
        
        # Parameters: date_params + exclusion_params + [user_id, limit_sessions, user_id]
        query_params = date_params + exclusion_params + [user_id, limit_sessions, user_id]
        
        print(f"DEBUG: Executing query with params: {query_params}")
        cur.execute(query, query_params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format results
        sessions_data = []
        for row in results:
            sessions_data.append({
                "qid": str(row['qid']),
                "session_id": str(row['session_id']),
                "user_id": row['user_id'],
                "query": row['original_request'],
                "response": row['response'],
                "timestamp": row['request_timestamp'].strftime("%Y-%m-%d %H:%M:%S") if row['request_timestamp'] else "",
                "vote": row['vote'],
                "feedback": row['feedback'] or ""
            })
        
        return {
            "user_id": user_id,
            "recent_sessions": sessions_data,
            "total_queries": len(sessions_data)
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_user_recent_sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-retention-analysis")
def get_user_retention_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get user retention analysis with FST filtering and email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build filters
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        fst_filter, fst_params = build_fst_filter(manager_id, fst_id)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Combine parameters
        all_params = date_params + fst_params + exclusion_params
        
        # Build WHERE clause
        where_clause = build_combined_where_clause(date_filter, fst_filter, exclusion_filter)
        
        # User retention analysis by days between first and last query
        retention_query = f"""
            WITH user_activity_span AS (
                SELECT 
                    cdf.user_id,
                    MIN(cdf.request_timestamp::date) as first_query_date,
                    MAX(cdf.request_timestamp::date) as last_query_date,
                    (MAX(cdf.request_timestamp::date) - MIN(cdf.request_timestamp::date)) as activity_span_days,
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT cdf.request_timestamp::date) as active_days
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
                HAVING COUNT(*) > 1  -- Only users with more than 1 query
            )
            SELECT 
                CASE 
                    WHEN activity_span_days >= 30 THEN 'Long-term (30+ days)'
                    WHEN activity_span_days >= 14 THEN 'Medium-term (14-29 days)'
                    WHEN activity_span_days >= 7 THEN 'Short-term (7-13 days)'
                    WHEN activity_span_days >= 1 THEN 'Brief (1-6 days)'
                    ELSE 'Single Day'
                END as retention_category,
                COUNT(*) as user_count,
                ROUND(AVG(activity_span_days), 1) as avg_span_days,
                ROUND(AVG(total_queries), 1) as avg_queries_per_user,
                ROUND(AVG(active_days), 1) as avg_active_days
            FROM user_activity_span
            GROUP BY 
                CASE 
                    WHEN activity_span_days >= 30 THEN 'Long-term (30+ days)'
                    WHEN activity_span_days >= 14 THEN 'Medium-term (14-29 days)'
                    WHEN activity_span_days >= 7 THEN 'Short-term (7-13 days)'
                    WHEN activity_span_days >= 1 THEN 'Brief (1-6 days)'
                    ELSE 'Single Day'
                END
            ORDER BY avg_span_days DESC
        """
        
        cur.execute(retention_query, all_params)
        retention_results = cur.fetchall()
        
        # New vs returning users analysis
        user_type_query = f"""
            WITH user_query_dates AS (
                SELECT 
                    cdf.user_id,
                    COUNT(DISTINCT cdf.request_timestamp::date) as unique_query_days,
                    COUNT(*) as total_queries,
                    MIN(cdf.request_timestamp) as first_query,
                    MAX(cdf.request_timestamp) as last_query
                FROM chat_data_final cdf
                {where_clause}
                GROUP BY cdf.user_id
            )
            SELECT 
                CASE 
                    WHEN unique_query_days = 1 THEN 'One-time Users'
                    WHEN unique_query_days <= 3 THEN 'Occasional Users (2-3 days)'
                    WHEN unique_query_days <= 7 THEN 'Regular Users (4-7 days)'
                    ELSE 'Frequent Users (8+ days)'
                END as user_type,
                COUNT(*) as user_count,
                ROUND(AVG(total_queries), 1) as avg_queries,
                ROUND(AVG(unique_query_days), 1) as avg_active_days
            FROM user_query_dates
            GROUP BY 
                CASE 
                    WHEN unique_query_days = 1 THEN 'One-time Users'
                    WHEN unique_query_days <= 3 THEN 'Occasional Users (2-3 days)'
                    WHEN unique_query_days <= 7 THEN 'Regular Users (4-7 days)'
                    ELSE 'Frequent Users (8+ days)'
                END
            ORDER BY avg_active_days DESC
        """
        
        cur.execute(user_type_query, all_params)
        user_type_results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "retention_analysis": [
                {
                    "category": row['retention_category'],
                    "user_count": row['user_count'],
                    "avg_span_days": row['avg_span_days'],
                    "avg_queries_per_user": row['avg_queries_per_user'],
                    "avg_active_days": row['avg_active_days']
                } for row in retention_results
            ],
            "user_type_analysis": [
                {
                    "type": row['user_type'],
                    "user_count": row['user_count'],
                    "avg_queries": row['avg_queries'],
                    "avg_active_days": row['avg_active_days']
                } for row in user_type_results
            ]
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fst-user-summary")
def get_fst_user_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None)
):
    """Get summary of users by FST team for managers with email exclusion"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter and email exclusion
        date_filter, date_params = build_user_date_filter(start_date, end_date)
        exclusion_filter, exclusion_params = build_email_exclusion_filter()
        
        # Build base WHERE conditions for the LEFT JOIN
        join_conditions = ["cdf.request_timestamp IS NOT NULL"]
        if date_filter:
            join_conditions.append(date_filter)
        if exclusion_filter:
            join_conditions.append(exclusion_filter)
        
        join_where = " AND ".join(join_conditions) if join_conditions else "TRUE"
        
        if manager_id:
            # Get FSTs under this manager and their user activity
            query = f"""
                SELECT 
                    ft.id as fst_id,
                    ft.full_name as fst_name,
                    ft.fst_email,
                    COUNT(DISTINCT cdf.user_id) as unique_users,
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT cdf.session_id) as total_sessions,
                    ROUND(AVG(
                        CASE 
                            WHEN COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) > 0 
                            THEN (COUNT(*) FILTER (WHERE cdf.vote = 1) * 100.0 / COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0))
                            ELSE 0 
                        END
                    ), 1) as avg_satisfaction_rate
                FROM fst_technicians ft
                JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                LEFT JOIN chat_data_final cdf ON (
                    cdf.user_id = ft.fst_email OR 
                    cdf.user_id = LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                ) AND {join_where}
                WHERE fma.manager_id = %s
                GROUP BY ft.id, ft.full_name, ft.fst_email
                ORDER BY total_queries DESC NULLS LAST
            """
            
            params = date_params + exclusion_params + [manager_id]
        else:
            # Get all FSTs and their user activity
            query = f"""
                SELECT 
                    ft.id as fst_id,
                    ft.full_name as fst_name,
                    ft.fst_email,
                    COUNT(DISTINCT cdf.user_id) as unique_users,
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT cdf.session_id) as total_sessions,
                    ROUND(
                        CASE 
                            WHEN COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0) > 0 
                            THEN (COUNT(*) FILTER (WHERE cdf.vote = 1) * 100.0 / COUNT(*) FILTER (WHERE cdf.vote IS NOT NULL AND cdf.vote != 0))
                            ELSE 0 
                        END, 1
                    ) as avg_satisfaction_rate
                FROM fst_technicians ft
                LEFT JOIN chat_data_final cdf ON (
                    cdf.user_id = ft.fst_email OR 
                    cdf.user_id = LOWER(REPLACE(ft.full_name, ' ', '.')) || '@toshibagcs.com'
                ) AND {join_where}
                GROUP BY ft.id, ft.full_name, ft.fst_email
                ORDER BY total_queries DESC NULLS LAST
            """
            
            params = date_params + exclusion_params
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "fst_id": row['fst_id'],
            "fst_name": row['fst_name'],
            "fst_email": row['fst_email'],
            "unique_users": row['unique_users'] or 0,
            "total_queries": row['total_queries'] or 0,
            "total_sessions": row['total_sessions'] or 0,
            "avg_satisfaction_rate": float(row['avg_satisfaction_rate'] or 0)
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Exclusion rule management endpoints
@router.get("/exclusion-rules")
def get_exclusion_rules():
    """Get current exclusion rules"""
    return {
        "excluded_emails": EXCLUDED_EMAILS,
        "excluded_domains": EXCLUDED_DOMAINS
    }

@router.post("/exclusion-rules")
def update_exclusion_rules(
    emails: list[str] = None,
    domains: list[str] = None
):
    """Update exclusion rules (requires restart to take effect)"""
    global EXCLUDED_EMAILS, EXCLUDED_DOMAINS
    
    if emails is not None:
        EXCLUDED_EMAILS = emails
    if domains is not None:
        # Ensure domains start with @
        EXCLUDED_DOMAINS = [domain if domain.startswith('@') else f'@{domain}' for domain in domains]
    
    return {
        "message": "Exclusion rules updated. Note: Changes take effect on next server restart.",
        "excluded_emails": EXCLUDED_EMAILS,
        "excluded_domains": EXCLUDED_DOMAINS
    }

# Legacy endpoints for backward compatibility
@router.get("/excluded-emails")
def get_excluded_emails():
    """Get list of currently excluded emails (legacy endpoint)"""
    return {"excluded_emails": EXCLUDED_EMAILS}

@router.post("/excluded-emails")
def update_excluded_emails(emails: list[str]):
    """Update the list of excluded emails (legacy endpoint - requires restart to take effect)"""
    global EXCLUDED_EMAILS
    EXCLUDED_EMAILS = emails
    return {
        "message": "Excluded emails updated. Note: Changes take effect on next server restart.",
        "excluded_emails": EXCLUDED_EMAILS
    }