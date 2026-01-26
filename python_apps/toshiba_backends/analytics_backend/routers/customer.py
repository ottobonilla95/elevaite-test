from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_db_connection
import traceback
from decimal import Decimal

router = APIRouter(prefix="/api/analytics/customer")

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

def build_date_filter_for_customer(start_date: Optional[str], end_date: Optional[str]):
    """Build date filter clause - EXACT SAME AS WORKING SUMMARY"""
    if start_date and end_date:
        return f"AND sr.incident_date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        return f"AND sr.incident_date >= '{start_date}'"
    elif end_date:
        return f"AND sr.incident_date <= '{end_date}'"
    else:
        return ""
    

@router.get("/customer-top-technicians")
def get_customer_top_technicians(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_account: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get top 3 technicians for a specific customer with date filtering"""
    try:
        date_filter = build_date_filter_for_customer(start_date, end_date)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not customer_account:
            return {"error": "customer_account parameter is required"}
        
        # Use the working query without fst_technicians table
        query = f"""
            SELECT 
                t.assignee_name as technician_name,
                COUNT(DISTINCT sr.sr_number) as service_requests_count,
                AVG(CASE 
                    WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                    THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                    ELSE NULL 
                END) as avg_resolution_days
            FROM service_requests sr
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            LEFT JOIN tasks t ON sr.sr_number = t.sr_number
            WHERE sr.incident_date IS NOT NULL
            AND c.customer_account_number = '{customer_account}'
            AND t.assignee_name IS NOT NULL
            AND t.assignee_name != ''
            AND t.assignee_name NOT ILIKE '%dummy%'
            AND t.assignee_name NOT ILIKE '%resource%'
            {date_filter}
            GROUP BY t.assignee_name
            HAVING COUNT(DISTINCT sr.sr_number) > 0
            ORDER BY service_requests_count DESC, avg_resolution_days ASC
            LIMIT 3
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        top_technicians = []
        for row in results:
            top_technicians.append({
                "name": row['technician_name'],
                "count": row['service_requests_count'],
                "avg_resolution_days": round(row['avg_resolution_days'], 1) if row['avg_resolution_days'] else 0
            })
        
        print(f"Found {len(top_technicians)} technicians for customer {customer_account}")
        
        cur.close()
        conn.close()
        
        return {
            "top_technicians": top_technicians,
            "customer_account": customer_account
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_customer_top_technicians: {str(e)}")
        return {"error": str(e), "top_technicians": []}

@router.get("/top-customers")
def get_top_customers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get top customers by service request count with manager/FST and date filtering"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_customer(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        limit_clause = ""
        if limit is not None and limit > 0:
            limit_clause = f"LIMIT {limit}"
        
        if fst_id:
            query = f"""
                WITH filtered_total AS (
                    SELECT COUNT(DISTINCT sr.sr_number) as total_count
                    FROM service_requests sr 
                    JOIN customers c ON sr.customer_account_number = c.customer_account_number
                    LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                    LEFT JOIN fst_technicians ftech ON (
                        fst_tasks.assignee_name = ftech.full_name OR
                        fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                        fst_tasks.assignee_name = ftech.fst_email
                    )
                    WHERE sr.incident_date IS NOT NULL
                    AND ftech.id = {fst_id}
                    {date_filter}
                )
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    (COUNT(DISTINCT sr.sr_number) * 100.0 / ft_total.total_count) as percent_total,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                CROSS JOIN filtered_total ft_total
                WHERE sr.incident_date IS NOT NULL
                AND ftech.id = {fst_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number, ft_total.total_count
                ORDER BY service_requests DESC
                {limit_clause}
            """
        elif manager_id:
            query = f"""
                WITH filtered_total AS (
                    SELECT COUNT(DISTINCT sr.sr_number) as total_count
                    FROM service_requests sr 
                    JOIN customers c ON sr.customer_account_number = c.customer_account_number
                    LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                    LEFT JOIN fst_technicians ftech ON (
                        mgr_tasks.assignee_name = ftech.full_name OR
                        mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                        mgr_tasks.assignee_name = ftech.fst_email
                    )
                    LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                    WHERE sr.incident_date IS NOT NULL
                    AND fma.manager_id = {manager_id}
                    {date_filter}
                )
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    (COUNT(DISTINCT sr.sr_number) * 100.0 / ft_total.total_count) as percent_total,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                CROSS JOIN filtered_total ft_total
                WHERE sr.incident_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number, ft_total.total_count
                ORDER BY service_requests DESC
                {limit_clause}
            """
        else:
            query = f"""
                WITH filtered_total AS (
                    SELECT COUNT(DISTINCT sr.sr_number) as total_count
                    FROM service_requests sr 
                    JOIN customers c ON sr.customer_account_number = c.customer_account_number
                    WHERE sr.incident_date IS NOT NULL
                    {date_filter}
                )
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    (COUNT(DISTINCT sr.sr_number) * 100.0 / ft_total.total_count) as percent_total,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                CROSS JOIN filtered_total ft_total
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number, ft_total.total_count
                ORDER BY service_requests DESC
                {limit_clause}
            """
        
        print(f"Executing top customers query: {query}")
        cur.execute(query)
        results = cur.fetchall()
        
        print(f"Found {len(results)} customers with filters applied")
        
        cur.close()
        conn.close()
        
        return [{
            "customer": row['customer_name'],
            "customerAccount": row['customer_account_number'],
            "serviceRequests": row['service_requests'],
            "percentTotal": f"{round(safe_float(row['percent_total']), 1)}%",
            "avgResolutionTime": f"{round(safe_float(row['avg_resolution_days']), 1)} days" if row['avg_resolution_days'] else "N/A"
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_top_customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-distribution")
def get_customer_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get customer distribution for pie chart with manager/FST and date filtering"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_customer(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    COUNT(*) as count,
                    (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()) as percentage
                FROM service_requests sr
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND ftech.id = {fst_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY count DESC
            """
        elif manager_id:
            query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    COUNT(*) as count,
                    (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()) as percentage
                FROM service_requests sr
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY count DESC
            """
        else:
            query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    COUNT(*) as count,
                    (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER()) as percentage
                FROM service_requests sr
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY count DESC
            """
        
        cur.execute(query)
        results = cur.fetchall()
        
        print(f"Found {len(results)} customers for distribution with filters applied")
        
        customer_data = []
        other_count = 0
        other_percentage = 0
        
        for i, row in enumerate(results):
            if i < 4:
                customer_data.append({
                    "name": row['customer_name'],
                    "value": round(row['percentage'], 1),
                    "count": row['count']
                })
            else:
                other_count += row['count']
                other_percentage += row['percentage']
        
        if other_count > 0:
            customer_data.append({
                "name": "Other",
                "value": round(other_percentage, 1),
                "count": other_count
            })
        
        colors = ["#FF6B35", "#FF8C42", "#FFB366", "#FFD1B1", "#FFEBB2"]
        for i, data in enumerate(customer_data):
            data["color"] = colors[i % len(colors)]
        
        cur.close()
        conn.close()
        
        return customer_data
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_customer_distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-parts")
def get_customer_parts(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_account: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get customer parts data with manager/FST and date filtering"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_customer(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        customer_filter = ""
        if customer_account:
            customer_filter = f"AND c.customer_account_number = '{customer_account}'"
        
        if fst_id:
            summary_query = f"""
                SELECT 
                    COUNT(DISTINCT p.part_number) as unique_parts,
                    SUM(p.total_cost) as total_cost,
                    COUNT(*) as total_replacements
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                AND ftech.id = {fst_id}
                {customer_filter}
                {date_filter}
            """
            
            cur.execute(summary_query)
            summary = cur.fetchone()
            
            parts_query = f"""
                SELECT 
                    p.part_number,
                    p.description,
                    COUNT(p.part_number) as replacement_count,
                    SUM(p.total_cost) as total_cost
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                AND ftech.id = {fst_id}
                {customer_filter}
                {date_filter}
                GROUP BY p.part_number, p.description
                ORDER BY replacement_count DESC
                LIMIT 10
            """
        elif manager_id:
            summary_query = f"""
                SELECT 
                    COUNT(DISTINCT p.part_number) as unique_parts,
                    SUM(p.total_cost) as total_cost,
                    COUNT(*) as total_replacements
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                AND fma.manager_id = {manager_id}
                {customer_filter}
                {date_filter}
            """
            
            cur.execute(summary_query)
            summary = cur.fetchone()
            
            parts_query = f"""
                SELECT 
                    p.part_number,
                    p.description,
                    COUNT(p.part_number) as replacement_count,
                    SUM(p.total_cost) as total_cost
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                AND fma.manager_id = {manager_id}
                {customer_filter}
                {date_filter}
                GROUP BY p.part_number, p.description
                ORDER BY replacement_count DESC
                LIMIT 10
            """
        else:
            summary_query = f"""
                SELECT 
                    COUNT(DISTINCT p.part_number) as unique_parts,
                    SUM(p.total_cost) as total_cost,
                    COUNT(*) as total_replacements
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                {customer_filter}
                {date_filter}
            """
            
            cur.execute(summary_query)
            summary = cur.fetchone()
            
            # Get parts data
            parts_query = f"""
                SELECT 
                    p.part_number,
                    p.description,
                    COUNT(p.part_number) as replacement_count,
                    SUM(p.total_cost) as total_cost
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                JOIN customers c ON sr.customer_account_number = c.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                AND p.part_number IS NOT NULL
                {customer_filter}
                {date_filter}
                GROUP BY p.part_number, p.description
                ORDER BY replacement_count DESC
                LIMIT 10
            """
        
        cur.execute(parts_query)
        parts_data = [{
            "partNumber": row['part_number'],
            "partDescription": row['description'] or "Unknown Part",
            "replacementCount": row['replacement_count'],
            "totalCost": round(row['total_cost'], 2) if row['total_cost'] else 0
        } for row in cur.fetchall()]
        
        print(f"Found {len(parts_data)} parts for customer with filters applied")
        
        cur.close()
        conn.close()
        
        return {
            "summary": {
                "uniquePartsCount": summary['unique_parts'] if summary['unique_parts'] else 0,
                "totalCost": round(summary['total_cost'], 2) if summary['total_cost'] else 0,
                "totalReplacements": summary['total_replacements'] if summary['total_replacements'] else 0
            },
            "partsData": parts_data
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_customer_parts: {str(e)}")
        return {
            "summary": {
                "uniquePartsCount": 0,
                "totalCost": 0,
                "totalReplacements": 0
            },
            "partsData": []
        }

# Add this debug code to your get_customer_detailed_metrics function in Python

@router.get("/customer-detailed-metrics")
def get_customer_detailed_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_account: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get comprehensive metrics for a specific customer with manager/FST and date filtering"""
    try:
        print("🔍 DEBUG: Received parameters:")
        print(f"  - customer_account: '{customer_account}' (type: {type(customer_account)})")
        print(f"  - start_date: {start_date}")
        print(f"  - end_date: {end_date}")
        print(f"  - manager_id: {manager_id}")
        print(f"  - fst_id: {fst_id}")
        
        if not customer_account:
            return {"error": "customer_account parameter is required"}
        
        date_filter = build_date_filter_for_customer(start_date, end_date)
        print(f"🔍 DEBUG: Built date_filter: '{date_filter}'")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Debug: First check if customer exists in customers table
        debug_customer_query = """
            SELECT 
                customer_name, 
                customer_account_number,
                COUNT(*) as records_count
            FROM customers 
            WHERE customer_account_number = %s 
            GROUP BY customer_name, customer_account_number
        """
        
        cur.execute(debug_customer_query, [customer_account])
        customer_check = cur.fetchone()
        
        if not customer_check:
            print(f"❌ ERROR: Customer account '{customer_account}' not found in customers table")
            
            # Show similar customers for debugging
            similar_query = """
                SELECT DISTINCT customer_name, customer_account_number 
                FROM customers 
                WHERE customer_name ILIKE %s OR customer_account_number ILIKE %s
                LIMIT 5
            """
            cur.execute(similar_query, [f"%{customer_account}%", f"%{customer_account}%"])
            similar_customers = cur.fetchall()
            
            return {
                "error": f"Customer account '{customer_account}' not found",
                "debug_info": {
                    "similar_customers": [
                        {"name": row['customer_name'], "account": row['customer_account_number']} 
                        for row in similar_customers
                    ]
                }
            }
        
        print("✅ DEBUG: Found customer:")
        print(f"  - Name: {customer_check['customer_name']}")
        print(f"  - Account: {customer_check['customer_account_number']}")
        print(f"  - Records in customers table: {customer_check['records_count']}")
        
        # Debug: Check how many service requests exist for this customer
        sr_check_query = f"""
            SELECT COUNT(*) as sr_count
            FROM service_requests sr
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            WHERE c.customer_account_number = %s
            AND sr.incident_date IS NOT NULL
            {date_filter}
        """
        
        cur.execute(sr_check_query, [customer_account])
        sr_check = cur.fetchone()
        print(f"🔍 DEBUG: Service requests for this customer: {sr_check['sr_count']}")
        
        # Continue with your existing query logic...
        if fst_id:
            query = f"""
                SELECT 
                    c.customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NOT NULL) as resolved_requests,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NULL) as open_requests,
                    COUNT(DISTINCT p.part_number) as unique_parts_used,
                    COALESCE(SUM(p.total_cost), 0) as total_parts_cost
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks t ON sr.sr_number = t.sr_number
                LEFT JOIN parts_used p ON t.task_number = p.task_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND c.customer_account_number = %s
                AND ftech.id = {fst_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
            """
        elif manager_id:
            query = f"""
                SELECT 
                    c.customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NOT NULL) as resolved_requests,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NULL) as open_requests,
                    COUNT(DISTINCT p.part_number) as unique_parts_used,
                    COALESCE(SUM(p.total_cost), 0) as total_parts_cost
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks t ON sr.sr_number = t.sr_number
                LEFT JOIN parts_used p ON t.task_number = p.task_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND c.customer_account_number = %s
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
            """
        else:
            query = f"""
                SELECT 
                    c.customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NOT NULL) as resolved_requests,
                    COUNT(DISTINCT sr.sr_number) FILTER (WHERE sr.closed_date IS NULL) as open_requests,
                    COUNT(DISTINCT p.part_number) as unique_parts_used,
                    COALESCE(SUM(p.total_cost), 0) as total_parts_cost
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks t ON sr.sr_number = t.sr_number
                LEFT JOIN parts_used p ON t.task_number = p.task_number
                WHERE sr.incident_date IS NOT NULL
                AND c.customer_account_number = %s
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
            """
        
        print(f"🔍 DEBUG: Executing main query for customer {customer_account}")
        cur.execute(query, [customer_account])
        result = cur.fetchone()
        
        if not result:
            print(f"❌ ERROR: Main query returned no results for customer {customer_account}")
            print("   This means customer exists but has no service requests matching the filters")
            
            # Return customer info with zero metrics instead of error
            return {
                "customer": customer_check['customer_name'] or f"Customer {customer_check['customer_account_number']}",
                "customerAccount": customer_check['customer_account_number'],
                "serviceRequests": {
                    "total": 0,
                    "resolved": 0,
                    "open": 0,
                    "resolutionRate": 0
                },
                "performance": {
                    "avgResolutionDays": 0
                },
                "resources": {
                    "uniquePartsUsed": 0,
                    "totalPartsCost": 0
                },
                "debug_info": {
                    "customer_exists": True,
                    "service_requests_found": 0,
                    "filters_applied": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "manager_id": manager_id,
                        "fst_id": fst_id
                    }
                }
            }
        
        print(f"✅ SUCCESS: Found {result['total_service_requests']} service requests for {customer_account}")
        
        response = {
            "customer": result['customer_name'] or f"Customer {result['customer_account_number']}",
            "customerAccount": result['customer_account_number'],
            "serviceRequests": {
                "total": result['total_service_requests'],
                "resolved": result['resolved_requests'],
                "open": result['open_requests'],
                "resolutionRate": round((result['resolved_requests'] / result['total_service_requests']) * 100, 1) if result['total_service_requests'] > 0 else 0
            },
            "performance": {
                "avgResolutionDays": round(result['avg_resolution_days'], 1) if result['avg_resolution_days'] else 0
            },
            "resources": {
                "uniquePartsUsed": result['unique_parts_used'],
                "totalPartsCost": float(result['total_parts_cost'])
            }
        }
        
        cur.close()
        conn.close()
        
        return response
        
    except Exception as e:
        traceback.print_exc()
        print(f"❌ ERROR in get_customer_detailed_metrics: {str(e)}")
        return {"error": str(e)}

@router.get("/customer-count")
def get_customer_count(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get customer count with filtering support"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_customer(start_date, end_date)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT 
                    COUNT(DISTINCT c.customer_account_number) as total_customers,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND ftech.id = {fst_id}
                {date_filter}
            """
        elif manager_id:
            query = f"""
                SELECT 
                    COUNT(DISTINCT c.customer_account_number) as total_customers,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
            """
        else:
            query = f"""
                SELECT 
                    COUNT(DISTINCT c.customer_account_number) as total_customers,
                    COUNT(DISTINCT sr.sr_number) as total_service_requests
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
            """
        
        cur.execute(query)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "totalCustomers": result['total_customers'] if result['total_customers'] else 0,
            "totalServiceRequests": result['total_service_requests'] if result['total_service_requests'] else 0
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_customer_count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers-paginated")
def get_customers_paginated(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Get paginated customers with filtering support"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_customer(start_date, end_date)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        offset = (page - 1) * page_size
        
        if fst_id:
            count_query = f"""
                SELECT COUNT(DISTINCT c.customer_account_number) as total
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND ftech.id = {fst_id}
                {date_filter}
            """
        elif manager_id:
            count_query = f"""
                SELECT COUNT(DISTINCT c.customer_account_number) as total
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
            """
        else:
            count_query = f"""
                SELECT COUNT(DISTINCT c.customer_account_number) as total
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
            """
        
        cur.execute(count_query)
        total_customers = cur.fetchone()['total']
        
        if fst_id:
            data_query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    fst_tasks.assignee_name = ftech.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    fst_tasks.assignee_name = ftech.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND ftech.id = {fst_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY service_requests DESC
                LIMIT {page_size} OFFSET {offset}
            """
        elif manager_id:
            data_query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ftech ON (
                    mgr_tasks.assignee_name = ftech.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ftech.full_name, '%') OR
                    mgr_tasks.assignee_name = ftech.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ftech.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY service_requests DESC
                LIMIT {page_size} OFFSET {offset}
            """
        else:
            data_query = f"""
                SELECT 
                    COALESCE(c.customer_name, 'Customer ' || c.customer_account_number) as customer_name,
                    c.customer_account_number,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM customers c
                JOIN service_requests sr ON c.customer_account_number = sr.customer_account_number
                WHERE sr.incident_date IS NOT NULL
                {date_filter}
                GROUP BY c.customer_name, c.customer_account_number
                ORDER BY service_requests DESC
                LIMIT {page_size} OFFSET {offset}
            """
        
        cur.execute(data_query)
        customers = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_customers + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        customer_data = [{
            "customer": row['customer_name'],
            "customerAccount": row['customer_account_number'],
            "serviceRequests": row['service_requests'],
            "avgResolutionTime": f"{round(safe_float(row['avg_resolution_days']), 1)} days" if row['avg_resolution_days'] else "N/A"
        } for row in customers]
        
        return {
            "customers": customer_data,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalCustomers": total_customers,
                "totalPages": total_pages,
                "hasNext": has_next,
                "hasPrev": has_prev
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_customers_paginated: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))