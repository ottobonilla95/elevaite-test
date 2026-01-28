# backend/routers/technicians.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import get_db_connection
import traceback

router = APIRouter(prefix="/api/analytics/technicians")

def safe_float(value):
    """Safely convert Decimal or any numeric type to float"""
    if value is None:
        return 0.0
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0

@router.get("/manager-groups")
def get_manager_groups():
    """Get all manager groups with FST counts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                m.id,
                m.manager_name,
                m.region,
                COUNT(fa.fst_id) as fst_count
            FROM manager_groups m
            LEFT JOIN fst_manager_assignments fa ON m.id = fa.manager_id
            GROUP BY m.id, m.manager_name, m.region
            ORDER BY fst_count DESC, m.manager_name
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "id": row['id'],
            "manager_name": row['manager_name'],
            "region": row['region'],
            "fst_count": row['fst_count']
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fsts-by-manager/{manager_id}")
def get_fsts_by_manager(manager_id: int):
    """Get all FSTs for a specific manager"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                f.id,
                f.fst_email,
                f.full_name,
                f.region
            FROM fst_technicians f
            JOIN fst_manager_assignments fa ON f.id = fa.fst_id
            WHERE fa.manager_id = %s
            ORDER BY f.full_name
        """
        
        cur.execute(query, [manager_id])
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "id": row['id'],
            "fst_email": row['fst_email'],
            "full_name": row['full_name'],
            "region": row['region']
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all-fsts")
def get_all_fsts(
    region: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None)
):
    """Get all FSTs with optional filtering"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Base query
        query = """
            SELECT 
                f.id,
                f.fst_email,
                f.full_name,
                f.region,
                m.manager_name
            FROM fst_technicians f
            LEFT JOIN fst_manager_assignments fa ON f.id = fa.fst_id
            LEFT JOIN manager_groups m ON fa.manager_id = m.id
        """
        
        # Build WHERE conditions
        where_conditions = []
        params = []
        
        if region:
            where_conditions.append("f.region = %s")
            params.append(region)
            
        if manager_id:
            where_conditions.append("fa.manager_id = %s")
            params.append(manager_id)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY f.full_name"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [{
            "id": row['id'],
            "fst_email": row['fst_email'],
            "full_name": row['full_name'],
            "region": row['region'],
            "manager_name": row['manager_name']
        } for row in results]
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def build_technician_filter(manager_id: Optional[int] = None, fst_id: Optional[int] = None) -> tuple:
    """
    Build technician filtering for SQL queries
    Returns: (additional_joins, where_clause, params)
    """
    additional_joins = ""
    where_clause = ""
    params = []
    
    if manager_id or fst_id:
        # Add joins for technician filtering
        additional_joins = """
            LEFT JOIN tasks t ON sr.sr_number = t.sr_number
            LEFT JOIN fst_technicians ft ON t.assignee_name = ft.full_name 
            LEFT JOIN fst_manager_assignments fma ON ft.id = fma.fst_id
            LEFT JOIN manager_groups mg ON fma.manager_id = mg.id
        """
        
        if manager_id and fst_id:
            where_clause = "AND mg.id = %s AND ft.id = %s"
            params = [manager_id, fst_id]
        elif manager_id:
            where_clause = "AND mg.id = %s"
            params = [manager_id]
        elif fst_id:
            where_clause = "AND ft.id = %s"
            params = [fst_id]
    
    return additional_joins, where_clause, params

@router.get("/validate-assignments")
def validate_technician_assignments():
    """Validate and show sample technician assignments for debugging"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check assignments
        query = """
            SELECT 
                f.full_name as fst_name,
                f.fst_email,
                f.region as fst_region,
                m.manager_name,
                m.region as manager_region,
                COUNT(DISTINCT fa.id) as assignment_count
            FROM fst_technicians f
            LEFT JOIN fst_manager_assignments fa ON f.id = fa.fst_id
            LEFT JOIN manager_groups m ON fa.manager_id = m.id
            GROUP BY f.id, f.full_name, f.fst_email, f.region, m.manager_name, m.region
            ORDER BY f.full_name
            LIMIT 20
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        # Get total counts
        count_query = """
            SELECT 
                COUNT(DISTINCT f.id) as total_fsts,
                COUNT(DISTINCT m.id) as total_managers,
                COUNT(DISTINCT fa.id) as total_assignments
            FROM fst_technicians f
            LEFT JOIN fst_manager_assignments fa ON f.id = fa.fst_id
            LEFT JOIN manager_groups m ON fa.manager_id = m.id
        """
        
        cur.execute(count_query)
        counts = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "summary": {
                "total_fsts": counts['total_fsts'],
                "total_managers": counts['total_managers'],
                "total_assignments": counts['total_assignments']
            },
            "sample_assignments": [{
                "fst_name": row['fst_name'],
                "fst_email": row['fst_email'],
                "fst_region": row['fst_region'],
                "manager_name": row['manager_name'],
                "manager_region": row['manager_region'],
                "assignment_count": row['assignment_count']
            } for row in results]
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))