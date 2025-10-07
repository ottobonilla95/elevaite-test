from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from database import get_db_connection, log_query
import traceback

router = APIRouter(prefix="/api/analytics/issues")

@router.get("/statistics")
def get_issue_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter
        date_filter = ""
        params = []
        
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Total issues categorized - use sr_notes table for customer_problem_summary
        query = f"""
            SELECT COUNT(*) as total
            FROM service_requests sr
            JOIN sr_notes n ON sr.sr_number = n.sr_number
            {where_clause}
            AND n.customer_problem_summary IS NOT NULL
        """
        cur.execute(query, params)
        total_issues = cur.fetchone()['total'] or 0
        
        # Most common issue
        if total_issues > 0:
            query = f"""
                SELECT 
                    n.customer_problem_summary as issue,
                    COUNT(*) as count,
                    (COUNT(*) * 100.0 / {total_issues}) as percentage
                FROM service_requests sr
                JOIN sr_notes n ON sr.sr_number = n.sr_number
                {where_clause}
                AND n.customer_problem_summary IS NOT NULL
                GROUP BY n.customer_problem_summary
                ORDER BY count DESC
                LIMIT 1
            """
            cur.execute(query, params)
            most_common = cur.fetchone()
        else:
            most_common = None
            
        # Most replaced part - NEW METRIC
        query = f"""
            SELECT 
                p.part_number,
                p.description,
                COUNT(*) as replacement_count,
                SUM(p.total_cost) as total_cost
            FROM parts_used p
            JOIN tasks t ON p.task_number = t.task_number
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            {where_clause.replace('sr.', '')}
            AND p.part_number IS NOT NULL
            AND p.description IS NOT NULL
            GROUP BY p.part_number, p.description
            ORDER BY replacement_count DESC
            LIMIT 1
        """
        try:
            cur.execute(query, params)
            most_replaced_part = cur.fetchone()
        except Exception as e:
            print(f"Error fetching most replaced part: {e}")
            most_replaced_part = None
        
        # Resolution rate
        query = f"""
            SELECT 
                COUNT(CASE WHEN sr.closed_date IS NOT NULL THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0) as resolution_rate
            FROM service_requests sr
            {where_clause}
        """
        cur.execute(query, params)
        resolution_result = cur.fetchone()
        resolution_rate = resolution_result['resolution_rate'] if resolution_result and resolution_result['resolution_rate'] is not None else 0
        
        # Calculate previous period for comparison
        resolution_change = 0
        if start_date and end_date:
            try:
                from datetime import datetime, timedelta
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                period_days = (end_dt - start_dt).days
                
                prev_end = start_dt
                prev_start = prev_end - timedelta(days=period_days)
                
                prev_filter = "WHERE sr.incident_date BETWEEN %s AND %s"
                prev_params = [prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")]
                
                query = f"""
                    SELECT 
                        COUNT(CASE WHEN sr.closed_date IS NOT NULL THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(*), 0) as resolution_rate
                    FROM service_requests sr
                    {prev_filter}
                """
                cur.execute(query, prev_params)
                prev_result = cur.fetchone()
                prev_resolution_rate = prev_result['resolution_rate'] if prev_result and prev_result['resolution_rate'] is not None else 0
                
                resolution_change = resolution_rate - prev_resolution_rate
            except Exception as e:
                print(f"Error calculating previous period: {e}")
                resolution_change = 0
        
        cur.close()
        conn.close()
        
        # Format response
        return {
            "totalIssues": total_issues,
            "mostCommonIssue": {
                "issue": most_common['issue'] if most_common else "N/A",
                "count": most_common['count'] if most_common else 0,
                "percentage": round(most_common['percentage'], 1) if most_common else 0
            },
            "mostReplacedPart": {
                "partNumber": most_replaced_part['part_number'] if most_replaced_part else "N/A",
                "description": most_replaced_part['description'] if most_replaced_part else "N/A",
                "count": most_replaced_part['replacement_count'] if most_replaced_part else 0,
                "cost": round(most_replaced_part['total_cost'], 2) if most_replaced_part and most_replaced_part['total_cost'] else 0
            },
            "resolutionRate": {
                "rate": round(resolution_rate, 1),
                "change": round(resolution_change, 1)
            }
        }
    except Exception as e:
        print(f"Error processing issue statistics: {e}")
        traceback.print_exc()
        
        # Return fallback data on error
        return {
            "totalIssues": 0,
            "mostCommonIssue": {
                "issue": "Data unavailable",
                "count": 0,
                "percentage": 0
            },
            "mostReplacedPart": {
                "partNumber": "N/A",
                "description": "Data unavailable",
                "count": 0,
                "cost": 0
            },
            "resolutionRate": {
                "rate": 0,
                "change": 0
            }
        }

@router.get("/distribution")
def get_issue_distribution(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        # Define enhanced issue categories and their keywords
        categories = {
            "Touch Screen Failure": ["touch", "screen", "display", "monitor", "lcd", "panel", "pixel"],
            "Scanner Problems": ["scan", "scanner", "barcode", "qr", "reader", "honeywell", "zebra", "symbol", "motorola"],
            "Printer Issues": ["print", "printer", "paper", "ink", "toner", "receipt", "thermal", "label", "media", "printhead"],
            "Power Problems": ["power", "battery", "charging", "electricity", "outlet", "cord", "adapter", "ups", "voltage", "12v"],
            "Software Errors": ["software", "system", "error", "bug", "crash", "windows", "application", "program", "reboot", "boot", "bios", "image", "reimage"],
            "Network Connectivity": ["network", "wifi", "internet", "connection", "ip", "ethernet", "wireless", "offline", "connectivity", "router", "switch", "lan", "wan"],
            "Hardware Damage": ["damage", "broken", "physical", "water", "cracked", "bent", "dented", "smashed", "drop", "physical damage"],
            "RFID Reader Issues": ["rfid", "tag", "nfc", "frequency", "antenna", "transponder", "proximity", "card reader"],
            "Cash Handling": ["cash", "drawer", "till", "coin", "bill", "currency", "denominations", "payment", "change", "recycler", "acceptor", "validator"],
            "Maintenance Service": ["maintenance", "cleaning", "dust", "preventive", "scheduled", "routine", "pm", "regular service"],
            "Scale/Weighing Issues": ["scale", "weight", "lb", "kg", "weigh", "load cell", "balance", "calibration", "zero", "tare"],
            "Security Systems": ["security", "camera", "cctv", "surveillance", "lock", "alarm", "access control", "badge", "key"],
            "Other": []
        }
        
        # Define fixed colors
        colors = {
            "Touch Screen Failure": "#FF6B00",
            "Scanner Problems": "#FFB800",
            "Printer Issues": "#F8E897",
            "Power Problems": "#9F4B53",
            "Software Errors": "#D71313",
            "Network Connectivity": "#E16D40",
            "Hardware Damage": "#93000A",
            "RFID Reader Issues": "#8B0000",
            "Cash Handling": "#8B4513",
            "Maintenance Service": "#2E8B57",
            "Scale/Weighing Issues": "#4682B4",
            "Security Systems": "#483D8B",
            "Other": "#C2C2C2"
        }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get problem summaries from sr_notes table
        query = f"""
            SELECT 
                n.customer_problem_summary,
                COUNT(*) as count
            FROM service_requests sr
            JOIN sr_notes n ON sr.sr_number = n.sr_number
            {where_clause}
            AND n.customer_problem_summary IS NOT NULL
            GROUP BY n.customer_problem_summary
            ORDER BY count DESC
        """
        
        log_query(query, params) if 'log_query' in globals() else None
        
        try:
            cur.execute(query, params)
            results = cur.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            results = []
        
        # Categorize issues
        categorized_counts = {category: 0 for category in categories.keys()}
        
        if results:
            for row in results:
                summary = row['customer_problem_summary'].lower() if row['customer_problem_summary'] else ""
                categorized = False
                
                for category, keywords in categories.items():
                    if category != "Other" and any(keyword in summary for keyword in keywords):
                        categorized_counts[category] += row['count']
                        categorized = True
                        break
                
                if not categorized:
                    categorized_counts["Other"] += row['count']
        
        cur.close()
        conn.close()
        
        # Create distribution data
        distribution_data = [
            {
                "name": category,
                "value": count,
                "color": colors[category]
            }
            for category, count in categorized_counts.items()
            if count > 0
        ]
        
        # Sort by count descending
        distribution_data.sort(key=lambda x: x["value"], reverse=True)
        
        return distribution_data
    except Exception as e:
        print(f"Error processing issue distribution: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return []

@router.get("/categories")
def get_issue_categories(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(6)  # Default to showing top 6 categories

):
    try:
        # Enhanced categories with more specific keywords
        categories = {
            "Touch Screen Failure": ["touch", "screen", "display", "monitor", "lcd", "panel", "pixel"],
            "Scanner Problems": ["scan", "scanner", "barcode", "qr", "reader", "honeywell", "zebra", "symbol", "motorola"],
            "Printer Issues": ["print", "printer", "paper", "ink", "toner", "receipt", "thermal", "label", "media", "printhead"],
            "Power Problems": ["power", "battery", "charging", "electricity", "outlet", "cord", "adapter", "ups", "voltage", "12v"],
            "Software Errors": ["software", "system", "error", "bug", "crash", "windows", "application", "program", "reboot", "boot", "bios", "image", "reimage"],
            "Network Connectivity": ["network", "wifi", "internet", "connection", "ip", "ethernet", "wireless", "offline", "connectivity", "router", "switch", "lan", "wan"],
            "Hardware Damage": ["damage", "broken", "physical", "water", "cracked", "bent", "dented", "smashed", "drop", "physical damage"],
            "RFID Reader Issues": ["rfid", "tag", "nfc", "frequency", "antenna", "transponder", "proximity", "card reader"],
            "Cash Handling": ["cash", "drawer", "till", "coin", "bill", "currency", "denominations", "payment", "change", "recycler", "acceptor", "validator"],
            "Maintenance Service": ["maintenance", "cleaning", "dust", "preventive", "scheduled", "routine", "pm", "regular service"],
            "Scale/Weighing Issues": ["scale", "weight", "lb", "kg", "weigh", "load cell", "balance", "calibration", "zero", "tare"],
            "Security Systems": ["security", "camera", "cctv", "surveillance", "lock", "alarm", "access control", "badge", "key"]
        }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get problem summaries from sr_notes table
        query = f"""
            SELECT 
                n.customer_problem_summary,
                COUNT(*) as count
            FROM service_requests sr
            JOIN sr_notes n ON sr.sr_number = n.sr_number
            {where_clause}
            AND n.customer_problem_summary IS NOT NULL
            GROUP BY n.customer_problem_summary
            ORDER BY count DESC
        """
        
        log_query(query, params) if 'log_query' in globals() else None
        
        try:
            cur.execute(query, params)
            results = cur.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            results = []
        
        # Categorize issues
        categorized_counts = {category: 0 for category in categories.keys()}
        
        if results:
            for row in results:
                summary = row['customer_problem_summary'].lower() if row['customer_problem_summary'] else ""
                
                for category, keywords in categories.items():
                    if any(keyword in summary for keyword in keywords):
                        categorized_counts[category] += row['count']
                        break
        
        cur.close()
        conn.close()
        
        # Format for bar chart
        bar_data = [
            {
                "category": category,
                "value": count
            }
            for category, count in categorized_counts.items()
            if count > 0
        ]
        
        # Sort by count (ascending for reverse bar chart)
        bar_data.sort(key=lambda x: x["value"])
        
        return bar_data
    except Exception as e:
        print(f"Error processing issue categories: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return []

@router.get("/by-machine-type")
def get_issues_by_machine_type(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get top machine types
        type_query = f"""
            SELECT 
                machine_type,
                COUNT(*) as count
            FROM service_requests sr
            {where_clause}
            AND machine_type IS NOT NULL
            GROUP BY machine_type
            ORDER BY count DESC
            LIMIT 6
        """
        
        log_query(type_query, params) if 'log_query' in globals() else None
        
        cur.execute(type_query, params)
        machine_types = cur.fetchall()
        
        # Get most common issue for each machine type
        results = []
        
        for machine in machine_types:
            machine_type = machine['machine_type']
            
            issue_query = f"""
                SELECT 
                    n.customer_problem_summary as issue,
                    COUNT(*) as occurrences,
                    COUNT(DISTINCT n.customer_problem_summary) as issue_types
                FROM service_requests sr
                JOIN sr_notes n ON sr.sr_number = n.sr_number
                {where_clause}
                AND sr.machine_type = %s
                AND n.customer_problem_summary IS NOT NULL
                GROUP BY n.customer_problem_summary
                ORDER BY occurrences DESC
                LIMIT 1
            """
            
            log_query(issue_query, params + [machine_type]) if 'log_query' in globals() else None
            
            cur.execute(issue_query, params + [machine_type])
            issue_result = cur.fetchone()
            
            # If no specific issue for this machine type, continue
            if not issue_result:
                continue
                
            # Get total issues for percentage calculation
            total_query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT n.customer_problem_summary) as unique_issues
                FROM service_requests sr
                JOIN sr_notes n ON sr.sr_number = n.sr_number
                {where_clause}
                AND sr.machine_type = %s
                AND n.customer_problem_summary IS NOT NULL
            """
            
            log_query(total_query, params + [machine_type]) if 'log_query' in globals() else None
            
            cur.execute(total_query, params + [machine_type])
            total_result = cur.fetchone()
            
            # Calculate percentage
            percentage = 0
            if issue_result and total_result and total_result['total'] > 0:
                percentage = (issue_result['occurrences'] * 100.0) / total_result['total']
            
            # Get most replaced part for this machine type - NEW DATA
            parts_query = f"""
                SELECT 
                    p.part_number,
                    p.description,
                    COUNT(*) as count
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                {where_clause}
                AND sr.machine_type = %s
                AND p.part_number IS NOT NULL
                AND p.description IS NOT NULL
                GROUP BY p.part_number, p.description
                ORDER BY count DESC
                LIMIT 1
            """
            
            try:
                log_query(parts_query, params + [machine_type]) if 'log_query' in globals() else None
                cur.execute(parts_query, params + [machine_type])
                part_result = cur.fetchone()
            except Exception as e:
                print(f"Error fetching parts for machine type {machine_type}: {e}")
                part_result = None
            
            results.append({
                "machineType": machine_type,
                "mostCommonIssue": issue_result['issue'] if issue_result else "N/A",
                "occurnces": issue_result['occurrences'] if issue_result else 0,
                "typesOfIssues": total_result['unique_issues'] if total_result else 0,
                "percentage": round(percentage, 1),
                "mostReplacedPart": part_result['description'] if part_result else "N/A",
                "partCount": part_result['count'] if part_result else 0
            })
        
        cur.close()
        conn.close()
        
        # Return the results
        return results
    except Exception as e:
        print(f"Error processing issues by machine type: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return []

@router.get("/by-customer")
def get_issues_by_customer(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get top customers
        customer_query = f"""
            SELECT 
                c.customer_name,
                c.customer_account_number,
                COUNT(*) as count
            FROM service_requests sr
            JOIN customers c ON sr.customer_account_number = c.customer_account_number
            {where_clause}
            GROUP BY c.customer_name, c.customer_account_number
            ORDER BY count DESC
            LIMIT 6
        """
        
        log_query(customer_query, params) if 'log_query' in globals() else None
        
        cur.execute(customer_query, params)
        customers = cur.fetchall()
        
        # Get most common issue for each customer
        results = []
        
        for customer in customers:
            customer_name = customer['customer_name'] or f"Customer {customer['customer_account_number']}"
            customer_account = customer['customer_account_number']
            
            issue_query = f"""
                SELECT 
                    n.customer_problem_summary as issue,
                    COUNT(*) as occurrences,
                    COUNT(DISTINCT n.customer_problem_summary) as issue_types
                FROM service_requests sr
                JOIN sr_notes n ON sr.sr_number = n.sr_number
                {where_clause}
                AND sr.customer_account_number = %s
                AND n.customer_problem_summary IS NOT NULL
                GROUP BY n.customer_problem_summary
                ORDER BY occurrences DESC
                LIMIT 1
            """
            
            log_query(issue_query, params + [customer_account]) if 'log_query' in globals() else None
            
            cur.execute(issue_query, params + [customer_account])
            issue_result = cur.fetchone()
            
            # If no specific issue for this customer, continue
            if not issue_result:
                continue
                
            # Get total issues for percentage calculation
            total_query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT n.customer_problem_summary) as unique_issues
                FROM service_requests sr
                JOIN sr_notes n ON sr.sr_number = n.sr_number
                {where_clause}
                AND sr.customer_account_number = %s
                AND n.customer_problem_summary IS NOT NULL
            """
            
            log_query(total_query, params + [customer_account]) if 'log_query' in globals() else None
            
            cur.execute(total_query, params + [customer_account])
            total_result = cur.fetchone()
            
            # Get most replaced part for this customer - NEW DATA
            parts_query = f"""
                SELECT 
                    p.part_number,
                    p.description,
                    COUNT(*) as count,
                    SUM(p.total_cost) as total_cost
                FROM parts_used p
                JOIN tasks t ON p.task_number = t.task_number
                JOIN service_requests sr ON t.sr_number = sr.sr_number
                {where_clause}
                AND sr.customer_account_number = %s
                AND p.part_number IS NOT NULL
                AND p.description IS NOT NULL
                GROUP BY p.part_number, p.description
                ORDER BY count DESC
                LIMIT 1
            """
            
            try:
                log_query(parts_query, params + [customer_account]) if 'log_query' in globals() else None
                cur.execute(parts_query, params + [customer_account])
                part_result = cur.fetchone()
            except Exception as e:
                print(f"Error fetching parts for customer {customer_name}: {e}")
                part_result = None
            
            # Calculate percentage
            percentage = 0
            if issue_result and total_result and total_result['total'] > 0:
                percentage = (issue_result['occurrences'] * 100.0) / total_result['total']
            
            results.append({
                "customerType": customer_name,
                "mostCommonIssue": issue_result['issue'] if issue_result else "N/A",
                "occurnces": issue_result['occurrences'] if issue_result else 0,
                "typesOfIssues": total_result['unique_issues'] if total_result else 0,
                "percentage": round(percentage, 1),
                "mostReplacedPart": part_result['description'] if part_result else "N/A",
                "partCount": part_result['count'] if part_result else 0,
                "partCost": round(part_result['total_cost'], 2) if part_result and part_result['total_cost'] else 0
            })
        
        cur.close()
        conn.close()
        
        # Return the results
        return results
    except Exception as e:
        print(f"Error processing issues by customer: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return []

@router.get("/replaced-parts-overview")
def get_replaced_parts_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """New endpoint to get an overview of most replaced parts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get top replaced parts
        parts_query = f"""
            SELECT 
                p.part_number,
                p.description,
                COUNT(*) as replacement_count,
                SUM(p.total_cost) as total_cost,
                COUNT(DISTINCT sr.sr_number) as service_requests,
                COUNT(DISTINCT sr.machine_type) as machine_types
            FROM parts_used p
            JOIN tasks t ON p.task_number = t.task_number
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            {where_clause}
            AND p.part_number IS NOT NULL
            AND p.description IS NOT NULL
            GROUP BY p.part_number, p.description
            ORDER BY replacement_count DESC
            LIMIT 10
        """
        
        log_query(parts_query, params) if 'log_query' in globals() else None
        
        try:
            cur.execute(parts_query, params)
            parts_data = cur.fetchall()
        except Exception as e:
            print(f"Error fetching replaced parts overview: {e}")
            parts_data = []
        
        # Get summary metrics
        summary_query = f"""
            SELECT 
                COUNT(DISTINCT p.part_number) as unique_parts,
                SUM(p.total_cost) as total_cost,
                COUNT(*) as total_replacements,
                COUNT(DISTINCT sr.sr_number) as affected_service_requests,
                (COUNT(DISTINCT sr.sr_number) * 100.0 / 
                    (SELECT COUNT(*) FROM service_requests sr {where_clause.replace('sr.', '')})) as percent_requiring_parts
            FROM parts_used p
            JOIN tasks t ON p.task_number = t.task_number
            JOIN service_requests sr ON t.sr_number = sr.sr_number
            {where_clause}
            AND p.part_number IS NOT NULL
        """
        
        log_query(summary_query, params) if 'log_query' in globals() else None
        
        try:
            cur.execute(summary_query, params + params if where_clause != "WHERE 1=1" else params)
            summary = cur.fetchone()
        except Exception as e:
            print(f"Error fetching parts summary: {e}")
            summary = None
        
        cur.close()
        conn.close()
        
        # Format response
        return {
            "topReplacedParts": [
                {
                    "partNumber": row['part_number'],
                    "description": row['description'],
                    "replacementCount": row['replacement_count'],
                    "totalCost": round(row['total_cost'], 2) if row['total_cost'] else 0,
                    "serviceRequests": row['service_requests'],
                    "machineTypes": row['machine_types']
                } for row in parts_data
            ],
            "summary": {
                "uniquePartsCount": summary['unique_parts'] if summary and summary['unique_parts'] else 0,
                "totalCost": round(summary['total_cost'], 2) if summary and summary['total_cost'] else 0,
                "totalReplacements": summary['total_replacements'] if summary and summary['total_replacements'] else 0,
                "affectedServiceRequests": summary['affected_service_requests'] if summary and summary['affected_service_requests'] else 0,
                "percentRequiringParts": round(summary['percent_requiring_parts'], 1) if summary and summary['percent_requiring_parts'] else 0
            }
        }
    except Exception as e:
        print(f"Error processing replaced parts overview: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return {
            "topReplacedParts": [],
            "summary": {
                "uniquePartsCount": 0,
                "totalCost": 0,
                "totalReplacements": 0,
                "affectedServiceRequests": 0,
                "percentRequiringParts": 0
            }
        }

@router.get("/parts-to-issues-correlation")
def get_parts_to_issues_correlation(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """New endpoint to correlate issues with replaced parts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build date filter with proper WHERE clause
        params = []
        if start_date and end_date:
            where_clause = "WHERE sr.incident_date BETWEEN %s AND %s"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE sr.incident_date >= %s"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE sr.incident_date <= %s"
            params = [end_date]
        else:
            where_clause = "WHERE 1=1"
        
        # Get correlation between issues and parts
        correlation_query = f"""
            SELECT 
                n.customer_problem_summary as issue,
                p.description as part_description,
                COUNT(*) as occurrence_count
            FROM service_requests sr
            JOIN sr_notes n ON sr.sr_number = n.sr_number
            JOIN tasks t ON sr.sr_number = t.sr_number
            JOIN parts_used p ON t.task_number = p.task_number
            {where_clause}
            AND n.customer_problem_summary IS NOT NULL
            AND p.description IS NOT NULL
            GROUP BY n.customer_problem_summary, p.description
            ORDER BY occurrence_count DESC
            LIMIT 20
        """
        
        log_query(correlation_query, params) if 'log_query' in globals() else None
        
        try:
            cur.execute(correlation_query, params)
            correlations = cur.fetchall()
        except Exception as e:
            print(f"Error fetching parts-issues correlation: {e}")
            correlations = []
        
        cur.close()
        conn.close()
        
        # Format response
        return [
            {
                "issue": row['issue'],
                "partDescription": row['part_description'],
                "occurrenceCount": row['occurrence_count']
            } for row in correlations
        ]
    except Exception as e:
        print(f"Error processing parts-to-issues correlation: {e}")
        traceback.print_exc()
        
        # Return empty data on error
        return []