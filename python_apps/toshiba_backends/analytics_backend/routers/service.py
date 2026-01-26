from fastapi import APIRouter, Query
from typing import Optional
from database import get_db_connection
import traceback
from decimal import Decimal

router = APIRouter(prefix="/api/analytics/service")

def safe_float(value):
    """Safely convert Decimal or any numeric type to float"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0

def build_date_filter_clause(start_date: Optional[str], end_date: Optional[str], table_alias: str = "sr") -> tuple:
    """
    Build a consistent date filter clause for SQL queries
    Returns: (where_clause, params)
    """
    where_clause = ""
    params = []
    
    if start_date and end_date:
        where_clause = f"AND {table_alias}.incident_date BETWEEN %s AND %s"
        params = [start_date, end_date]
    elif start_date:
        where_clause = f"AND {table_alias}.incident_date >= %s"
        params = [start_date]
    elif end_date:
        where_clause = f"AND {table_alias}.incident_date <= %s"
        params = [end_date]
    
    return where_clause, params

@router.get("/metrics")
def get_service_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer: Optional[str] = Query(None)
):
    """Get service metrics including travel time, service time, and top technician"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        # Add customer filter if provided
        customer_filter = ""
        if customer:
            customer_filter = "AND c.customer_name = %s"
            params.append(customer)
        
        print(f"Service metrics - Date filter: {date_filter}, Customer filter: {customer_filter}, Params: {params}")
        
        # Average travel time
        travel_query = f"""
            SELECT 
                AVG(t.travel_time_hours) as avg_travel
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            {customer_filter}
            AND t.travel_time_hours IS NOT NULL
            AND t.travel_time_hours > 0
        """
        cur.execute(travel_query, params)
        travel_info = cur.fetchone()
        avg_travel = safe_float(travel_info['avg_travel']) if travel_info else 0.0
        
        # Format travel time as hours and minutes
        def format_time(hours):
            if not hours or hours == 0:
                return "0h 0m"
            h = int(hours)
            m = int((hours - h) * 60)
            return f"{h}h {m}m"
        
        # Average service time
        service_query = f"""
            SELECT 
                AVG(t.actual_time_hours) as avg_service
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            {customer_filter}
            AND t.actual_time_hours IS NOT NULL
            AND t.actual_time_hours > 0
        """
        cur.execute(service_query, params)
        service_info = cur.fetchone()
        avg_service = safe_float(service_info['avg_service']) if service_info else 0.0
        
        # Top technician
        tech_query = f"""
            SELECT 
                t.assignee_name as technician,
                COUNT(DISTINCT t.sr_number) as sr_count
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            {customer_filter}
            AND t.assignee_name IS NOT NULL
            AND t.assignee_name != ''
            AND t.assignee_name != 'NULL'
            GROUP BY t.assignee_name
            ORDER BY sr_count DESC
            LIMIT 1
        """
        
        cur.execute(tech_query, params)
        top_tech = cur.fetchone()
        
        cur.close()
        conn.close()
        
        print(f"Service metrics loaded: Travel={avg_travel:.2f}h, Service={avg_service:.2f}h, Tech={top_tech['technician'] if top_tech else 'None'}")
        
        return {
            "travel_time": {
                "value": round(avg_travel, 2),
                "formatted": format_time(avg_travel)
            },
            "service_time": {
                "value": round(avg_service, 2),
                "formatted": format_time(avg_service)
            },
            "top_technician": {
                "name": top_tech['technician'] if top_tech and top_tech['technician'] else "No technician data available",
                "count": top_tech['sr_count'] if top_tech else 0
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_service_metrics: {str(e)}")
        return {
            "travel_time": {
                "value": 0.0,
                "formatted": "0h 0m"
            },
            "service_time": {
                "value": 0.0,
                "formatted": "0h 0m"
            },
            "top_technician": {
                "name": "Error loading technician data",
                "count": 0
            }
        }

@router.get("/machine-distribution")
def get_machine_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer: Optional[str] = Query(None)
):
    """Get machine type distribution for customer analysis with proper date filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        # Add customer filter if provided
        customer_filter = ""
        if customer:
            customer_filter = "AND c.customer_name = %s"
            params.append(customer)
        
        print(f"Machine distribution - Date filter: {date_filter}, Customer filter: {customer_filter}, Params: {params}")
        
        # Get machine type distribution
        query = f"""
            WITH machine_counts AS (
                SELECT 
                    sr.machine_type,
                    COUNT(*) as count
                FROM service_requests sr
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
                {customer_filter}
                AND sr.machine_type IS NOT NULL
                GROUP BY sr.machine_type
            ),
            total_count AS (
                SELECT SUM(count) as total FROM machine_counts
            )
            SELECT 
                m.machine_type as name,
                m.count as value,
                ROUND((m.count * 100.0 / GREATEST(t.total, 1)), 1) as percentage
            FROM machine_counts m
            CROSS JOIN total_count t
            ORDER BY m.count DESC
            LIMIT 6
        """
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        print(f"Found {len(results)} machine types for distribution")
        
        cur.close()
        conn.close()
        
        # Define colors for consistency
        colors = ["#FF681F", "#FF9F71", "#FFD971", "#BF0909", "#FFBD71", "#FF0000"]
        
        return [{
            "name": row['name'],
            "value": row['value'],
            "percentage": safe_float(row['percentage']),
            "color": colors[i % len(colors)]
        } for i, row in enumerate(results)]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_machine_distribution: {str(e)}")
        return []

@router.get("/time-analysis")
def get_time_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer: Optional[str] = Query(None)
):
    """Get time analysis metrics with proper date filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        # Add customer filter if provided
        customer_filter = ""
        if customer:
            customer_filter = "AND c.customer_name = %s"
            params.append(customer)
        
        print(f"Time analysis - Date filter: {date_filter}, Customer filter: {customer_filter}, Params: {params}")
        
        # Get comprehensive time metrics
        query = f"""
            SELECT 
                AVG(t.travel_time_hours) as avg_travel_time,
                AVG(t.actual_time_hours) as avg_service_time,
                AVG(CASE 
                    WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                    THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                    ELSE NULL 
                END) as avg_resolution_days,
                COUNT(DISTINCT sr.sr_number) as total_requests,
                COUNT(DISTINCT t.assignee_name) as unique_technicians
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            {customer_filter}
        """
        
        cur.execute(query, params)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result:
            return {
                "avg_travel_time": round(safe_float(result['avg_travel_time']), 2),
                "avg_service_time": round(safe_float(result['avg_service_time']), 2),
                "avg_resolution_days": round(safe_float(result['avg_resolution_days']), 1),
                "total_requests": result['total_requests'] or 0,
                "unique_technicians": result['unique_technicians'] or 0
            }
        else:
            return {
                "avg_travel_time": 0.0,
                "avg_service_time": 0.0,
                "avg_resolution_days": 0.0,
                "total_requests": 0,
                "unique_technicians": 0
            }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_time_analysis: {str(e)}")
        return {
            "avg_travel_time": 0.0,
            "avg_service_time": 0.0,
            "avg_resolution_days": 0.0,
            "total_requests": 0,
            "unique_technicians": 0
        }

@router.get("/technician-performance")
def get_technician_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(10)
):
    """Get technician performance metrics with proper date filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        # Add limit
        limit_clause = f"LIMIT {limit}" if limit else "LIMIT 10"
        
        print(f"Technician performance - Date filter: {date_filter}, Params: {params}")
        
        query = f"""
            SELECT 
                t.assignee_name as technician_name,
                COUNT(DISTINCT sr.sr_number) as total_requests,
                AVG(t.travel_time_hours) as avg_travel_time,
                AVG(t.actual_time_hours) as avg_service_time,
                AVG(CASE 
                    WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                    THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                    ELSE NULL 
                END) as avg_resolution_days
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            AND t.assignee_name IS NOT NULL
            AND t.assignee_name != ''
            AND t.assignee_name != 'NULL'
            GROUP BY t.assignee_name
            ORDER BY total_requests DESC
            {limit_clause}
        """
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        print(f"Found {len(results)} technicians for performance analysis")
        
        cur.close()
        conn.close()
        
        return [{
            "technician_name": row['technician_name'],
            "total_requests": row['total_requests'],
            "avg_travel_time": round(safe_float(row['avg_travel_time']), 2),
            "avg_service_time": round(safe_float(row['avg_service_time']), 2),
            "avg_resolution_days": round(safe_float(row['avg_resolution_days']), 1)
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_technician_performance: {str(e)}")
        return []

@router.get("/travel-by-region")
def get_travel_by_region(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get travel time analysis by region with proper date filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        print(f"Travel by region - Date filter: {date_filter}, Params: {params}")
        
        query = f"""
            SELECT 
                COALESCE(c.state, 'Unknown') as region,
                COUNT(DISTINCT sr.sr_number) as total_requests,
                AVG(t.travel_time_hours) as avg_travel_time,
                MIN(t.travel_time_hours) as min_travel_time,
                MAX(t.travel_time_hours) as max_travel_time
            FROM tasks t
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            AND t.travel_time_hours IS NOT NULL
            AND t.travel_time_hours > 0
            GROUP BY c.state
            ORDER BY avg_travel_time DESC
            LIMIT 15
        """
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        print(f"Found {len(results)} regions for travel analysis")
        
        cur.close()
        conn.close()
        
        return [{
            "region": row['region'],
            "total_requests": row['total_requests'],
            "avg_travel_time": round(safe_float(row['avg_travel_time']), 2),
            "min_travel_time": round(safe_float(row['min_travel_time']), 2),
            "max_travel_time": round(safe_float(row['max_travel_time']), 2)
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_travel_by_region: {str(e)}")
        return []

@router.get("/validate-data")
def validate_service_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer: Optional[str] = Query(None)
):
    """Validate service data for debugging purposes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter using helper function
        date_filter, params = build_date_filter_clause(start_date, end_date)
        
        # Add customer filter if provided
        customer_filter = ""
        if customer:
            customer_filter = "AND c.customer_name = %s"
            params.append(customer)
        
        print(f"Validating service data - Date filter: {date_filter}, Customer filter: {customer_filter}, Params: {params}")
        
        # Get basic counts
        validation_query = f"""
            SELECT 
                COUNT(DISTINCT sr.sr_number) as total_service_requests,
                COUNT(DISTINCT t.task_number) as total_tasks,
                COUNT(DISTINCT t.assignee_name) as unique_technicians,
                COUNT(CASE WHEN t.travel_time_hours IS NOT NULL THEN 1 END) as tasks_with_travel_time,
                COUNT(CASE WHEN t.actual_time_hours IS NOT NULL THEN 1 END) as tasks_with_service_time,
                AVG(t.travel_time_hours) as avg_travel_time,
                AVG(t.actual_time_hours) as avg_service_time
            FROM service_requests sr
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            LEFT JOIN tasks t ON sr.sr_number = t.sr_number
            WHERE sr.incident_date IS NOT NULL
            {date_filter}
            {customer_filter}
        """
        
        cur.execute(validation_query, params)
        validation = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "customer": customer
            },
            "data_counts": {
                "total_service_requests": validation['total_service_requests'] or 0,
                "total_tasks": validation['total_tasks'] or 0,
                "unique_technicians": validation['unique_technicians'] or 0,
                "tasks_with_travel_time": validation['tasks_with_travel_time'] or 0,
                "tasks_with_service_time": validation['tasks_with_service_time'] or 0
            },
            "averages": {
                "avg_travel_time": round(safe_float(validation['avg_travel_time']), 2),
                "avg_service_time": round(safe_float(validation['avg_service_time']), 2)
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in validate_service_data: {str(e)}")
        return {
            "error": str(e),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "customer": customer
            }
        }