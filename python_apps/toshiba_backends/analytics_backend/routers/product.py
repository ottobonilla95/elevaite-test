from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_db_connection
import traceback

router = APIRouter(prefix="/api/analytics/product")

def build_date_filter_for_product(start_date: Optional[str], end_date: Optional[str]):
    """Build date filter clause - EXACT SAME AS WORKING SUMMARY"""
    if start_date and end_date:
        return f"AND sr.incident_date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        return f"AND sr.incident_date >= '{start_date}'"
    elif end_date:
        return f"AND sr.incident_date <= '{end_date}'"
    else:
        return ""
    
def build_product_type_filter(product_type: Optional[str]):
    """Build product type filter using the ingested machine models table"""
    if not product_type or product_type == 'all':
        return ""
    elif product_type == 'toshiba':
        return """AND sr.machine_type IN (
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'TGCS - Active'
        )"""
    elif product_type == 'oem':
        return """AND sr.machine_type IN (
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'OEM'
        )"""
    else:
        return ""

@router.get("/parts-by-machine-type")
def get_parts_by_machine_type(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
        product_type: Optional[str] = Query('all')

):
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type) 
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    COUNT(p.part_number) as total_parts_ordered,
                    COUNT(DISTINCT p.part_number) as unique_parts_count
                FROM service_requests sr
                JOIN tasks t ON sr.sr_number = t.sr_number
                JOIN parts_used p ON t.task_number = p.task_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.machine_type IS NOT NULL
                AND p.part_number IS NOT NULL
                AND p.part_number != ''
                AND ft.id = {fst_id}
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY total_parts_ordered DESC
                LIMIT 6
            """
        elif manager_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    COUNT(p.part_number) as total_parts_ordered,
                    COUNT(DISTINCT p.part_number) as unique_parts_count
                FROM service_requests sr
                JOIN tasks t ON sr.sr_number = t.sr_number
                JOIN parts_used p ON t.task_number = p.task_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE sr.machine_type IS NOT NULL
                AND p.part_number IS NOT NULL
                AND p.part_number != ''
                AND fma.manager_id = {manager_id}
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY total_parts_ordered DESC
                LIMIT 6
            """
        else:
            # No manager/FST filter - just date
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    COUNT(p.part_number) as total_parts_ordered,
                    COUNT(DISTINCT p.part_number) as unique_parts_count
                FROM service_requests sr
                JOIN tasks t ON sr.sr_number = t.sr_number
                JOIN parts_used p ON t.task_number = p.task_number
                WHERE sr.machine_type IS NOT NULL
                AND p.part_number IS NOT NULL
                AND p.part_number != ''
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY total_parts_ordered DESC
                LIMIT 6
            """
        
        print(f"Executing parts-by-machine-type query: {query}")
        cur.execute(query)
        machine_parts = cur.fetchall()
        
        # Get top parts for each machine type
        top_parts_by_machine = {}
        for machine in machine_parts:
            machine_type = machine['machine_type']
            
            # Use same filtering for parts query
            if fst_id:
                parts_query = f"""
                    SELECT 
                        p.part_number,
                        COALESCE(MAX(p.description), 'No description') as description,
                        COUNT(p.part_number) as count
                    FROM parts_used p
                    JOIN tasks t ON p.task_number = t.task_number
                    JOIN service_requests sr ON t.sr_number = sr.sr_number
                    LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                    LEFT JOIN fst_technicians ft ON (
                        fst_tasks.assignee_name = ft.full_name OR
                        fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                        fst_tasks.assignee_name = ft.fst_email
                    )
                    WHERE sr.machine_type = '{machine_type}' 
                    AND p.part_number IS NOT NULL 
                    AND p.part_number != ''
                    AND ft.id = {fst_id}
                    {date_filter}
                    GROUP BY p.part_number
                    ORDER BY count DESC
                    LIMIT 5
                """
            elif manager_id:
                parts_query = f"""
                    SELECT 
                        p.part_number,
                        COALESCE(MAX(p.description), 'No description') as description,
                        COUNT(p.part_number) as count
                    FROM parts_used p
                    JOIN tasks t ON p.task_number = t.task_number
                    JOIN service_requests sr ON t.sr_number = sr.sr_number
                    LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                    LEFT JOIN fst_technicians ft ON (
                        mgr_tasks.assignee_name = ft.full_name OR
                        mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                        mgr_tasks.assignee_name = ft.fst_email
                    )
                    LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE sr.machine_type = '{machine_type}' 
                    AND p.part_number IS NOT NULL 
                    AND p.part_number != ''
                    AND fma.manager_id = {manager_id}
                    {date_filter}
                    GROUP BY p.part_number
                    ORDER BY count DESC
                    LIMIT 5
                """
            else:
                parts_query = f"""
                    SELECT 
                        p.part_number,
                        COALESCE(MAX(p.description), 'No description') as description,
                        COUNT(p.part_number) as count
                    FROM parts_used p
                    JOIN tasks t ON p.task_number = t.task_number
                    JOIN service_requests sr ON t.sr_number = sr.sr_number
                    WHERE sr.machine_type = '{machine_type}' 
                    AND p.part_number IS NOT NULL 
                    AND p.part_number != ''
                    {date_filter}
                    GROUP BY p.part_number
                    ORDER BY count DESC
                    LIMIT 5
                """
                
            cur.execute(parts_query)
            top_parts = cur.fetchall()
            
            top_parts_by_machine[machine_type] = [{
                "partNumber": part['part_number'],
                "description": part['description'],
                "count": part['count']
            } for part in top_parts]
        
        cur.close()
        conn.close()
        
        return [{
            "machineType": row['machine_type'],
            "serviceRequests": row['service_requests'],
            "totalPartsOrdered": row['total_parts_ordered'],
            "uniquePartsCount": row['unique_parts_count'],
            "topParts": top_parts_by_machine.get(row['machine_type'], [])
        } for row in machine_parts]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_parts_by_machine_type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/machine-overview")
def get_machine_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')

):
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
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
                {product_filter}

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
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY count DESC
                LIMIT 6
            """
        else:
            # No manager/FST filter - just date
            query = f"""
                SELECT 
                    machine_type,
                    COUNT(*) as count,
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
                FROM service_requests sr
                WHERE machine_type IS NOT NULL
                {date_filter}
                {product_filter}

                GROUP BY machine_type
                ORDER BY count DESC
                LIMIT 6
            """
        
        cur.execute(query)
        type_distribution = cur.fetchall()
        
        # Bar chart data with same filtering
        if fst_id:
            bar_query = f"""
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
                {product_filter}

                GROUP BY sr.machine_type
                ORDER BY count DESC
                LIMIT 7
            """
        elif manager_id:
            bar_query = f"""
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
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY count DESC
                LIMIT 7
            """
        else:
            bar_query = f"""
                SELECT 
                    machine_type,
                    COUNT(*) as count
                FROM service_requests sr
                WHERE machine_type IS NOT NULL
                {date_filter}
                {product_filter}
                
                GROUP BY machine_type
                ORDER BY count DESC
                LIMIT 7
            """
        
        cur.execute(bar_query)
        type_counts = cur.fetchall()
        
        # Top models by type with same filtering
        main_machine_types = ['6800', '6225', '6201', '4901', '4810', '6150', '6149', '6145', '4828', '6260', '4825', '6160', '6180', '6700', '6880', '6900', '7401', '8000']        
        if fst_id:
            models_query = f"""
                SELECT 
                    sr.machine_type,
                    sr.machine_model,
                    COUNT(DISTINCT sr.sr_number) as count
                FROM service_requests sr
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE sr.machine_type IS NOT NULL 
                AND sr.machine_model IS NOT NULL
                AND sr.machine_type IN ('6800', '6225', '6201', '4901', '4810', '6150', '6149', '6145', '4828', '6260', '4825', '6160', '6180', '6700', '6880', '6900', '7401', '8000')                AND ft.id = {fst_id}
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type, sr.machine_model
                ORDER BY sr.machine_type, count DESC
            """
        elif manager_id:
            models_query = f"""
                SELECT 
                    sr.machine_type,
                    sr.machine_model,
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
                AND sr.machine_model IS NOT NULL
                AND sr.machine_type IN ('6800', '6225', '6201', '4901', '4810', '6150', '6149', '6145', '4828', '6260', '4825', '6160', '6180', '6700', '6880', '6900', '7401', '8000')                AND fma.manager_id = {manager_id}
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type, sr.machine_model
                ORDER BY sr.machine_type, count DESC
            """
        else:
            models_query = f"""
                SELECT 
                    machine_type,
                    machine_model,
                    COUNT(*) as count
                FROM service_requests sr
                WHERE machine_type IS NOT NULL 
                AND machine_model IS NOT NULL
                AND machine_type IN ('6800', '6225', '6201', '4901', '4810', '6150', '6149', '6145', '4828', '6260', '4825', '6160', '6180', '6700', '6880', '6900', '7401', '8000')
                {date_filter}
                {product_filter}
                GROUP BY machine_type, machine_model
                ORDER BY machine_type, count DESC
            """
        
        cur.execute(models_query)
        models_results = cur.fetchall()
        
        # Group models by type and take top 5
        models_by_type = {}
        for row in models_results:
            machine_type = row['machine_type']
            if machine_type not in models_by_type:
                models_by_type[machine_type] = []
            if len(models_by_type[machine_type]) < 5:  # Only take top 5
                models_by_type[machine_type].append({
                    "model": row['machine_model'],
                    "count": row['count']
                })
        
        top_models_by_type = []
        for machine_type in main_machine_types:
            if machine_type in models_by_type:
                top_models_by_type.append({
                    "machineType": machine_type,
                    "models": models_by_type[machine_type]
                })
        
        cur.close()
        conn.close()
        
        colors = ["#FF681F", "#FF9F71", "#FFD971", "#BF0909", "#FFBD71", "#FF0000"]
        
        return {
            "typeDistribution": [{
                "name": row['machine_type'],
                "value": round(row['percentage'], 1),
                "count": row['count'],
                "color": colors[i % len(colors)]
            } for i, row in enumerate(type_distribution)],
            "topModelsByType": top_models_by_type,
            "typeBarChart": [{
                "label": row['machine_type'],
                "count": row['count'],
                "color": "#4ADE80"
            } for row in type_counts],
            "replacementTrend": []
        }
    except Exception as e:
        traceback.print_exc()
        print(f"Error in machine-overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/machine-details")
def get_machine_details(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')

):
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type) 
        print(f"DEBUG: date_filter: {date_filter}")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL 
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
                WHERE sr.machine_type IS NOT NULL
                AND ft.id = {fst_id}
                {date_filter}
                {product_filter}

                GROUP BY sr.machine_type
                ORDER BY service_requests DESC
                LIMIT 9
            """
        elif manager_id:
            query = f"""
                SELECT 
                    sr.machine_type,
                    COUNT(DISTINCT sr.sr_number) as service_requests,
                    AVG(CASE 
                        WHEN sr.closed_date IS NOT NULL AND sr.incident_date IS NOT NULL 
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
                WHERE sr.machine_type IS NOT NULL
                AND fma.manager_id = {manager_id}
                {date_filter}
                {product_filter}
                GROUP BY sr.machine_type
                ORDER BY service_requests DESC
                LIMIT 9
            """
        else:
            # No manager/FST filter
            query = f"""
                SELECT 
                    machine_type,
                    COUNT(*) as service_requests,
                    AVG(CASE 
                        WHEN closed_date IS NOT NULL AND incident_date IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (closed_date - incident_date))/86400 
                        ELSE NULL 
                    END) as avg_resolution_days
                FROM service_requests sr
                WHERE machine_type IS NOT NULL
                {date_filter}
                {product_filter}
                GROUP BY machine_type
                ORDER BY service_requests DESC
                LIMIT 9
            """
        
        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "machine_type": row['machine_type'],
            "service_requests": row['service_requests'],
            "avg_resolution_time": round(row['avg_resolution_days'], 1) if row['avg_resolution_days'] else 0
        } for row in results]
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_machine_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parts")
def get_parts_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')
):
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type) 
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description') as description,
                    COUNT(*) as count
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != ''
                AND ft.id = {fst_id}
                {date_filter}
                {product_filter}
                GROUP BY p.part_number
                ORDER BY count DESC
                LIMIT {limit}
            """
        elif manager_id:
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description') as description,
                    COUNT(*) as count
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != ''
                AND fma.manager_id = {manager_id}
                {date_filter}
                {product_filter}
                GROUP BY p.part_number
                ORDER BY count DESC
                LIMIT {limit}
            """
        else:
            # No manager/FST filter
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description') as description,
                    COUNT(*) as count
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != ''
                {date_filter}
                {product_filter}
                GROUP BY p.part_number
                ORDER BY count DESC
                LIMIT {limit}
            """
        
        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "partNumber": row['part_number'],
            "description": (row['description'][:50] + "...") if row['description'] and len(row['description']) > 50 else row['description'],
            "count": int(row['count'])
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_parts_analysis: {str(e)}")
        return []

@router.get("/parts-by-machine-filtered")
def get_parts_by_machine_filtered(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    machine_type: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')
):
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type) 
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Add machine type filter
        machine_filter = ""
        if machine_type and machine_type != 'all':
            machine_filter = f"AND sr.machine_type = '{machine_type}'"
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description available') as description,
                    COUNT(*) as count,
                    sr.machine_type
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    fst_tasks.assignee_name = ft.full_name OR
                    fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    fst_tasks.assignee_name = ft.fst_email
                )
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != '' 
                AND sr.machine_type IS NOT NULL
                AND ft.id = {fst_id}
                {machine_filter}
                {date_filter}
                {product_filter}
                GROUP BY p.part_number, sr.machine_type
                ORDER BY count DESC
                LIMIT 200
            """
        elif manager_id:
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description available') as description,
                    COUNT(*) as count,
                    sr.machine_type
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                LEFT JOIN fst_technicians ft ON (
                    mgr_tasks.assignee_name = ft.full_name OR
                    mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                    mgr_tasks.assignee_name = ft.fst_email
                )
                LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != '' 
                AND sr.machine_type IS NOT NULL
                AND fma.manager_id = {manager_id}
                {machine_filter}
                {date_filter}
                {product_filter}
                GROUP BY p.part_number, sr.machine_type
                ORDER BY count DESC
                LIMIT 200
            """
        else:
            # No manager/FST filter
            query = f"""
                SELECT 
                    p.part_number,
                    COALESCE(MAX(p.description), 'No description available') as description,
                    COUNT(*) as count,
                    sr.machine_type
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                WHERE p.part_number IS NOT NULL 
                AND p.part_number != '' 
                AND sr.machine_type IS NOT NULL
                {machine_filter}
                {date_filter}
                {product_filter}
                GROUP BY p.part_number, sr.machine_type
                ORDER BY count DESC
                LIMIT 200
            """
        
        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "partNumber": row['part_number'],
            "description": row['description'],
            "count": int(row['count']),
            "machineType": row['machine_type']
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_parts_by_machine_filtered: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/machine-field-distribution")
def get_machine_field_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')
):
    """Get machine field distribution with FST filtering - shows SR rates relative to field population"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type) 
        print(f"DEBUG: date_filter: {date_filter}")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                WITH machine_sr_data AS (
                    SELECT 
                        sr.machine_type,
                        sr.machine_model,
                        COUNT(DISTINCT sr.sr_number) as total_srs,
                        COUNT(DISTINCT sr.machine_serial_number) as unique_machines_with_srs
                    FROM service_requests sr
                    LEFT JOIN tasks fst_tasks ON sr.sr_number = fst_tasks.sr_number
                    LEFT JOIN fst_technicians ft ON (
                        fst_tasks.assignee_name = ft.full_name OR
                        fst_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                        fst_tasks.assignee_name = ft.fst_email
                    )
                    WHERE sr.machine_type IS NOT NULL 
                    AND sr.machine_model IS NOT NULL
                    AND ft.id = {fst_id}
                    {date_filter}
                    {product_filter}
                    GROUP BY sr.machine_type, sr.machine_model
                ),
                machine_field_estimates AS (
                    SELECT 
                        machine_type,
                        machine_model,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_sr_data
                )
                SELECT 
                    machine_type as "machineType",
                    machine_model as "machineModel", 
                    total_srs as "totalSRs",
                    estimated_field_population as "machinesInField",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate",
                    unique_machines_with_srs as "uniqueMachinesWithSRs"
                FROM machine_field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
                LIMIT 20
            """
        elif manager_id:
            query = f"""
                WITH machine_sr_data AS (
                    SELECT 
                        sr.machine_type,
                        sr.machine_model,
                        COUNT(DISTINCT sr.sr_number) as total_srs,
                        COUNT(DISTINCT sr.machine_serial_number) as unique_machines_with_srs
                    FROM service_requests sr
                    LEFT JOIN tasks mgr_tasks ON sr.sr_number = mgr_tasks.sr_number
                    LEFT JOIN fst_technicians ft ON (
                        mgr_tasks.assignee_name = ft.full_name OR
                        mgr_tasks.assignee_name LIKE CONCAT('%', ft.full_name, '%') OR
                        mgr_tasks.assignee_name = ft.fst_email
                    )
                    LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
                    WHERE sr.machine_type IS NOT NULL 
                    AND sr.machine_model IS NOT NULL
                    AND fma.manager_id = {manager_id}
                    {date_filter}
                    {product_filter}
                    GROUP BY sr.machine_type, sr.machine_model
                ),
                machine_field_estimates AS (
                    SELECT 
                        machine_type,
                        machine_model,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_sr_data
                )
                SELECT 
                    machine_type as "machineType",
                    machine_model as "machineModel", 
                    total_srs as "totalSRs",
                    estimated_field_population as "machinesInField",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate",
                    unique_machines_with_srs as "uniqueMachinesWithSRs"
                FROM machine_field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
                LIMIT 20
            """
        else:
            # No manager/FST filter
            query = f"""
                WITH machine_sr_data AS (
                    SELECT 
                        machine_type,
                        machine_model,
                        COUNT(DISTINCT sr_number) as total_srs,
                        COUNT(DISTINCT machine_serial_number) as unique_machines_with_srs
                    FROM service_requests sr
                    WHERE machine_type IS NOT NULL 
                    AND machine_model IS NOT NULL
                    {date_filter}
                    {product_filter}
                    GROUP BY machine_type, machine_model
                ),
                machine_field_estimates AS (
                    SELECT 
                        machine_type,
                        machine_model,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_sr_data
                )
                SELECT 
                    machine_type as "machineType",
                    machine_model as "machineModel", 
                    total_srs as "totalSRs",
                    estimated_field_population as "machinesInField",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate",
                    unique_machines_with_srs as "uniqueMachinesWithSRs"
                FROM machine_field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
                LIMIT 20
            """
        
        cur.execute(query)
        field_distribution = cur.fetchall()
        
        # Calculate summary metrics
        total_field_pop = sum(row['machinesInField'] for row in field_distribution)
        total_srs = sum(row['totalSRs'] for row in field_distribution)
        avg_sr_rate = (total_srs / total_field_pop) if total_field_pop > 0 else 0
        
        summary = {
            "totalMachineTypesModels": len(field_distribution),
            "avgSRRate": round(avg_sr_rate, 4),
            "totalFieldPopulation": total_field_pop,
            "dateRange": {
                "startDate": start_date,
                "endDate": end_date
            }
        }
        
        cur.close()
        conn.close()
        
        return {
            "fieldDistribution": [dict(row) for row in field_distribution],
            "summary": summary
        }
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_machine_field_distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/machine-type-field-summary")
def get_machine_type_field_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    fst_id: Optional[int] = Query(None),
    product_type: Optional[str] = Query('all')
):
    """Get machine type field summary with FST filtering - aggregated by machine type"""
    try:
        print(f"DEBUG: start_date: {start_date}, end_date: {end_date}, manager_id: {manager_id}, fst_id: {fst_id}")
        date_filter = build_date_filter_for_product(start_date, end_date)
        product_filter = build_product_type_filter(product_type)
        print(f"DEBUG: date_filter: {date_filter}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Use EXACT same pattern as working Summary
        if fst_id:
            query = f"""
                WITH machine_type_summary AS (
                    SELECT 
                        sr.machine_type,
                        COUNT(DISTINCT sr.sr_number) as total_srs,
                        COUNT(DISTINCT sr.machine_serial_number) as unique_machines_with_srs
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
                    {product_filter}
                    GROUP BY sr.machine_type
                ),
                field_estimates AS (
                    SELECT 
                        machine_type,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20  
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            WHEN machine_type = '344' THEN unique_machines_with_srs * 18
                            WHEN machine_type = '363' THEN unique_machines_with_srs * 12
                            WHEN machine_type = '336' THEN unique_machines_with_srs * 22
                            WHEN machine_type = 'TGCS' THEN unique_machines_with_srs * 8
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_type_summary
                )
                SELECT 
                    machine_type as "machineType",
                    estimated_field_population as "totalMachinesInField",
                    total_srs as "totalSRs", 
                    unique_machines_with_srs as "uniqueMachinesWithSRs",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate"
                FROM field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
            """
        elif manager_id:
            query = f"""
                WITH machine_type_summary AS (
                    SELECT 
                        sr.machine_type,
                        COUNT(DISTINCT sr.sr_number) as total_srs,
                        COUNT(DISTINCT sr.machine_serial_number) as unique_machines_with_srs
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
                    {product_filter}
                    GROUP BY sr.machine_type
                ),
                field_estimates AS (
                    SELECT 
                        machine_type,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20  
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            WHEN machine_type = '344' THEN unique_machines_with_srs * 18
                            WHEN machine_type = '363' THEN unique_machines_with_srs * 12
                            WHEN machine_type = '336' THEN unique_machines_with_srs * 22
                            WHEN machine_type = 'TGCS' THEN unique_machines_with_srs * 8
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_type_summary
                )
                SELECT 
                    machine_type as "machineType",
                    estimated_field_population as "totalMachinesInField",
                    total_srs as "totalSRs", 
                    unique_machines_with_srs as "uniqueMachinesWithSRs",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate"
                FROM field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
            """
        else:
            # No manager/FST filter
            query = f"""
                WITH machine_type_summary AS (
                    SELECT 
                        machine_type,
                        COUNT(DISTINCT sr_number) as total_srs,
                        COUNT(DISTINCT machine_serial_number) as unique_machines_with_srs
                    FROM service_requests sr
                    WHERE machine_type IS NOT NULL 
                    {date_filter}
                    {product_filter}
                    GROUP BY machine_type
                ),
                field_estimates AS (
                    SELECT 
                        machine_type,
                        CASE 
                            WHEN machine_type = '335' THEN unique_machines_with_srs * 25
                            WHEN machine_type = '368' THEN unique_machines_with_srs * 20  
                            WHEN machine_type = '343' THEN unique_machines_with_srs * 15
                            WHEN machine_type = '344' THEN unique_machines_with_srs * 18
                            WHEN machine_type = '363' THEN unique_machines_with_srs * 12
                            WHEN machine_type = '336' THEN unique_machines_with_srs * 22
                            WHEN machine_type = 'TGCS' THEN unique_machines_with_srs * 8
                            ELSE unique_machines_with_srs * 10
                        END as estimated_field_population,
                        total_srs,
                        unique_machines_with_srs
                    FROM machine_type_summary
                )
                SELECT 
                    machine_type as "machineType",
                    estimated_field_population as "totalMachinesInField",
                    total_srs as "totalSRs", 
                    unique_machines_with_srs as "uniqueMachinesWithSRs",
                    ROUND(
                        CASE 
                            WHEN estimated_field_population > 0 
                            THEN total_srs::numeric / estimated_field_population::numeric 
                            ELSE 0 
                        END, 4
                    ) as "srRate"
                FROM field_estimates
                WHERE estimated_field_population > 0
                ORDER BY total_srs DESC
            """
        
        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        traceback.print_exc()
        print(f"Error in get_machine_type_field_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))