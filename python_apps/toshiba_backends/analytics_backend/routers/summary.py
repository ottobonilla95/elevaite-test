from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_db_connection
import traceback

router = APIRouter(prefix="/api/analytics/summary")

def build_date_filter(start_date: Optional[str], end_date: Optional[str]):
    """Build date filter clause"""
    if start_date and end_date:
        return f"AND sr.incident_date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        return f"AND sr.incident_date >= '{start_date}'"
    elif end_date:
        return f"AND sr.incident_date <= '{end_date}'"
    else:
        return ""

@router.get("/metrics")
def get_enhanced_summary_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Enhanced summary metrics with FST filtering support AND date filtering"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT COUNT(DISTINCT sr.sr_number) as total 
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE ft.id = {fst_id}
                {date_filter}
            """
            filter_type = "fst"
            
        elif manager_id:
            query = f"""
                SELECT COUNT(DISTINCT sr.sr_number) as total 
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE fma.manager_id = {manager_id}
                {date_filter}
            """
            filter_type = "manager"
            
        else:
            if date_filter:
                query = f"SELECT COUNT(*) as total FROM service_requests sr WHERE 1=1 {date_filter}"
            else:
                query = "SELECT COUNT(*) as total FROM service_requests"
            filter_type = "date_only" if date_filter else "none"
        
        print(f"Executing query: {query}")
        cur.execute(query)
        
        result = cur.fetchone()
        total_srs = result['total'] if result else 0
        
        print(f"SUCCESS! Total SRs: {total_srs} (filter: {filter_type})")
        
        if fst_id:
            resolution_query = f"""
                SELECT 
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.incident_date IS NOT NULL
                AND sr.closed_date IS NOT NULL
                AND ft.id = {fst_id}
                {date_filter}
            """
        elif manager_id:
            resolution_query = f"""
                SELECT 
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL AND sr.closed_date > sr.incident_date
                        THEN EXTRACT(EPOCH FROM (sr.closed_date - sr.incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL
                AND sr.closed_date IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
            """
        else:
            if date_filter:
                resolution_query = f"""
                    SELECT 
                        AVG(CASE 
                            WHEN closed_date IS NOT NULL AND incident_date IS NOT NULL AND closed_date > incident_date
                            THEN EXTRACT(EPOCH FROM (closed_date - incident_date))/86400 
                            ELSE NULL 
                        END) as avg_resolution_days
                    FROM service_requests sr
                    WHERE incident_date IS NOT NULL
                    AND closed_date IS NOT NULL
                    {date_filter}
                """
            else:
                resolution_query = """
                    SELECT 
                        AVG(CASE 
                            WHEN closed_date IS NOT NULL AND incident_date IS NOT NULL AND closed_date > incident_date
                            THEN EXTRACT(EPOCH FROM (closed_date - incident_date))/86400 
                            ELSE NULL 
                        END) as avg_resolution_days
                    FROM service_requests
                    WHERE incident_date IS NOT NULL
                    AND closed_date IS NOT NULL
                """
        
        cur.execute(resolution_query)
        resolution_result = cur.fetchone()
        avg_resolution_days = resolution_result['avg_resolution_days'] if resolution_result and resolution_result['avg_resolution_days'] else 0
        
        print(f"SUCCESS! Avg Resolution Time: {avg_resolution_days} days")
        
        if fst_id:
            date_query = f"""
                SELECT 
                    MIN(sr.incident_date) as min_date,
                    MAX(sr.incident_date) as max_date,
                    COUNT(DISTINCT DATE(sr.incident_date)) as unique_days
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE ft.id = {fst_id}
                {date_filter}
            """
        elif manager_id:
            date_query = f"""
                SELECT 
                    MIN(sr.incident_date) as min_date,
                    MAX(sr.incident_date) as max_date,
                    COUNT(DISTINCT DATE(sr.incident_date)) as unique_days
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE fma.manager_id = {manager_id}
                {date_filter}
            """
        else:
            if date_filter:
                date_query = f"""
                    SELECT 
                        MIN(incident_date) as min_date,
                        MAX(incident_date) as max_date,
                        COUNT(DISTINCT DATE(incident_date)) as unique_days
                    FROM service_requests sr
                    WHERE 1=1 {date_filter}
                """
            else:
                date_query = """
                    SELECT 
                        MIN(incident_date) as min_date,
                        MAX(incident_date) as max_date,
                        COUNT(DISTINCT DATE(incident_date)) as unique_days
                    FROM service_requests
                """
        
        cur.execute(date_query)
        date_info = cur.fetchone()
        
        avg_per_day = 0
        if date_info['unique_days'] and date_info['unique_days'] > 0:
            avg_per_day = total_srs / date_info['unique_days']
        
        if fst_id:
            machine_query = f"""
                SELECT 
                    sr.machine_type, 
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr 
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.machine_type IS NOT NULL
                AND ft.id = {fst_id}
                {date_filter}
                GROUP BY sr.machine_type 
                ORDER BY count DESC 
                LIMIT 1
            """
        elif manager_id:
            machine_query = f"""
                SELECT 
                    sr.machine_type, 
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr 
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.machine_type IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY sr.machine_type 
                ORDER BY count DESC 
                LIMIT 1
            """
        else:
            if date_filter:
                machine_query = f"""
                    SELECT 
                        machine_type, 
                        COUNT(*) as count
                    FROM service_requests sr
                    WHERE machine_type IS NOT NULL
                    {date_filter}
                    GROUP BY machine_type 
                    ORDER BY count DESC 
                    LIMIT 1
                """
            else:
                machine_query = """
                    SELECT 
                        machine_type, 
                        COUNT(*) as count
                    FROM service_requests
                    WHERE machine_type IS NOT NULL
                    GROUP BY machine_type 
                    ORDER BY count DESC 
                    LIMIT 1
                """
        
        cur.execute(machine_query)
        top_machine = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "total_srs": total_srs,
            "avg_requests_per_day": round(avg_per_day, 1),
            "avg_travel_time": 0,
            "avg_travel_time_formatted": "0h 0m",
            "avg_resolution_time": round(avg_resolution_days, 1),  
            "top_machine_type": f"{top_machine['machine_type']} ({top_machine['count']})" if top_machine else "N/A",
            "total_parts_cost": 0,
            "unique_parts": 0,
            "top_machine_model": "N/A",
            "date_range": {
                "start": date_info['min_date'].strftime("%Y-%m-%d") if date_info['min_date'] else None,
                "end": date_info['max_date'].strftime("%Y-%m-%d") if date_info['max_date'] else None,
                "requested_start": start_date,
                "requested_end": end_date
            },
            "total_queries": 30200,
            "avg_queries_per_day": 1006,
            "query_trends": [
                {"date": "2024-01", "value": 4500},
                {"date": "2024-02", "value": 5200},
                {"date": "2024-03", "value": 6100},
                {"date": "2024-04", "value": 5800},
                {"date": "2024-05", "value": 6500},
                {"date": "2024-06", "value": 7200}
            ],
            "_data_source": "real_database_with_fst_and_date_filtering",
            "_date_filter_applied": bool(date_filter),
            "_manager_filter_applied": bool(manager_id and not fst_id),
            "_fst_filter_applied": bool(fst_id),
            "_manager_id": manager_id,
            "_fst_id": fst_id,
            "_filter_type": filter_type,
            "_validation_passed": True,
            "_avg_resolution_days_calculated": round(avg_resolution_days, 1)  # debug
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
def get_service_request_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Trends with FST filtering support AND date filtering"""
    try:
        date_filter = build_date_filter(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT 
                    DATE_TRUNC('month', sr.incident_date)::date as period,
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.incident_date IS NOT NULL 
                AND sr.incident_date >= '2025-01-01' 
                AND sr.incident_date <= CURRENT_DATE
                AND ft.id = {fst_id}
                {date_filter}
                GROUP BY period
                ORDER BY period
            """
        elif manager_id:
            query = f"""
                SELECT 
                    DATE_TRUNC('month', sr.incident_date)::date as period,
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.incident_date IS NOT NULL 
                AND sr.incident_date >= '2025-01-01' 
                AND sr.incident_date <= CURRENT_DATE
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY period
                ORDER BY period
            """
        else:
            if date_filter:
                query = f"""
                    SELECT 
                        DATE_TRUNC('month', incident_date)::date as period,
                        COUNT(*) as count
                    FROM service_requests sr
                    WHERE incident_date IS NOT NULL 
                    AND incident_date >= '2025-01-01' 
                    AND incident_date <= CURRENT_DATE
                    {date_filter}
                    GROUP BY period
                    ORDER BY period
                """
            else:
                query = """
                    SELECT 
                        DATE_TRUNC('month', incident_date)::date as period,
                        COUNT(*) as count
                    FROM service_requests
                    WHERE incident_date IS NOT NULL 
                    AND incident_date >= '2025-01-01' 
                    AND incident_date <= CURRENT_DATE
                    GROUP BY period
                    ORDER BY period
                """
        
        cur.execute(query)
        results = cur.fetchall()
        
        formatted_results = []
        for row in results:
            if row['period']:
                formatted_results.append({
                    "date": row['period'].strftime('%m/%y'),
                    "value": row['count'],
                    "_raw_date": row['period'].strftime('%Y-%m-%d'),
                    "_grouping": "monthly",
                    "_manager_filtered": bool(manager_id and not fst_id),
                    "_fst_filtered": bool(fst_id),
                    "_date_filtered": bool(date_filter)
                })
        
        cur.close()
        conn.close()
        
        return formatted_results
        
    except Exception as e:
        print(f"Trends ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/machine-distribution")
def get_machine_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Machine distribution with FST filtering support AND date filtering"""
    try:
        date_filter = build_date_filter(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as count,
                    COUNT(DISTINCT sr.sr_number) * 100.0 / SUM(COUNT(DISTINCT sr.sr_number)) OVER() as percentage
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.machine_type IS NOT NULL
                AND ft.id = {fst_id}
                {date_filter}
                GROUP BY sr.machine_type
                ORDER BY count DESC
                LIMIT 6
            """
        elif manager_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as count,
                    COUNT(DISTINCT sr.sr_number) * 100.0 / SUM(COUNT(DISTINCT sr.sr_number)) OVER() as percentage
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.machine_type IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY sr.machine_type
                ORDER BY count DESC
                LIMIT 6
            """
        else:
            if date_filter:
                query = f"""
                    SELECT 
                        machine_type,
                        COUNT(*) as count,
                        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
                    FROM service_requests sr
                    WHERE machine_type IS NOT NULL
                    {date_filter}
                    GROUP BY machine_type
                    ORDER BY count DESC
                    LIMIT 6
                """
            else:
                query = """
                    SELECT 
                        machine_type,
                        COUNT(*) as count,
                        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
                    FROM service_requests
                    WHERE machine_type IS NOT NULL
                    GROUP BY machine_type
                    ORDER BY count DESC
                    LIMIT 6
                """
        
        cur.execute(query)
        results = cur.fetchall()
        
        colors = ["#FF681F", "#FF9F71", "#FFD971", "#BF0909", "#FFBD71", "#FF0000"]
        
        response_data = []
        for i, row in enumerate(results):
            machine_type = row['machine_type'] if row['machine_type'] else "Unknown"
            response_data.append({
                "name": machine_type,
                "value": round(row['percentage'], 1),
                "count": row['count'],
                "color": colors[i % len(colors)],
                "_manager_filtered": bool(manager_id and not fst_id),
                "_fst_filtered": bool(fst_id),
                "_date_filtered": bool(date_filter)
            })
        
        cur.close()
        conn.close()
        
        return response_data
        
    except Exception as e:
        print(f"Machine ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/severity-distribution")
def get_severity_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None)
):
    """Severity distribution with FST filtering support AND date filtering"""
    try:
        date_filter = build_date_filter(start_date, end_date)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if fst_id:
            query = f"""
                SELECT 
                    sr.severity,
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.severity IS NOT NULL
                AND ft.id = {fst_id}
                {date_filter}
                GROUP BY sr.severity
            """
        elif manager_id:
            query = f"""
                SELECT 
                    sr.severity,
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.severity IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                GROUP BY sr.severity
            """
        else:
            if date_filter:
                query = f"""
                    SELECT 
                        severity,
                        COUNT(*) as count
                    FROM service_requests sr
                    WHERE severity IS NOT NULL
                    {date_filter}
                    GROUP BY severity
                """
            else:
                query = """
                    SELECT 
                        severity,
                        COUNT(*) as count
                    FROM service_requests
                    WHERE severity IS NOT NULL
                    GROUP BY severity
                """
        
        cur.execute(query)
        results = cur.fetchall()
        
        mapping = {
            'Critical': ['critical', 'sev 1'],
            'High': ['high', 'sev 2'], 
            'Medium': ['medium', 'sev 3'],
            'Low': ['low', 'sev 4', 'standard']
        }
        
        severity_colors = {
            'Critical': '#EF4444',
            'High': '#F97316', 
            'Medium': '#FACC15',
            'Low': '#22C55E'
        }
        
        severity_counts = {level: 0 for level in mapping.keys()}
        
        for row in results:
            severity_text = row['severity'].lower() if row['severity'] else ""
            assigned = False
            
            for standard_level, keywords in mapping.items():
                if any(keyword in severity_text for keyword in keywords):
                    severity_counts[standard_level] += row['count']
                    assigned = True
                    break
            
            if not assigned:
                severity_counts['Low'] += row['count']
        
        severity_order = ['Critical', 'High', 'Medium', 'Low']
        formatted_results = []
        for level in severity_order:
            if severity_counts[level] > 0:
                formatted_results.append({
                    "label": level,
                    "count": severity_counts[level],
                    "color": severity_colors[level],
                    "_manager_filtered": bool(manager_id and not fst_id),
                    "_fst_filtered": bool(fst_id),
                    "_date_filtered": bool(date_filter)
                })
        
        cur.close()
        conn.close()
        
        return formatted_results
        
    except Exception as e:
        print(f"Severity ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))