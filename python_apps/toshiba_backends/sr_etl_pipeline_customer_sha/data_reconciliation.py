import asyncio
import asyncpg
import json
import os
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataReconciliationReport:
    """Generate reconciliation report between S3 and PostgreSQL"""
    
    def __init__(self, config):
        self.config = config
        self.db_config = self._parse_connection_string(config["pg_conn_string"])
        
    def _parse_connection_string(self, conn_string: str) -> dict:
        """Parse PostgreSQL connection string"""
        try:
            parsed = urlparse(conn_string)
            import urllib.parse
            password = urllib.parse.unquote(parsed.password) if parsed.password else None
            
            return {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or 5432,
                'user': parsed.username or 'postgres',
                'password': password,
                'database': parsed.path.lstrip('/') if parsed.path else 'postgres'
            }
        except Exception as e:
            logger.error(f"Error parsing connection string: {e}")
            raise

    async def get_postgres_summary(self):
        """Get current PostgreSQL data summary"""
        connection = None
        try:
            connection = await asyncpg.connect(**self.db_config)
            
            # Check if tables exist
            tables_exist = await connection.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                AND table_name IN ('service_requests', 'customers', 'tasks', 'parts_used', 'sr_notes')
                ORDER BY table_name
            """)
            
            if not tables_exist:
                return {
                    'status': 'no_tables',
                    'message': 'ETL tables do not exist in database',
                    'tables': {},
                    'monthly_breakdown': {},
                    'months_with_data': []
                }
            
            # Get row counts and data ranges
            postgres_data = {}
            monthly_breakdown = {}
            
            for table_row in tables_exist:
                table_name = table_row['table_name']
                
                # Get basic counts
                count = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                
                # Get date ranges where applicable
                date_info = None
                if table_name == 'service_requests':
                    date_info = await connection.fetchrow("""
                        SELECT 
                            MIN(incident_date) as earliest_incident,
                            MAX(incident_date) as latest_incident,
                            MIN(created_at) as earliest_created,
                            MAX(created_at) as latest_created,
                            COUNT(DISTINCT customer_account_number) as unique_customers,
                            COUNT(DISTINCT machine_model) as unique_machine_models
                        FROM service_requests
                        WHERE incident_date IS NOT NULL
                    """)
                    
                    # Get monthly breakdown of service requests by incident date
                    monthly_data = await connection.fetch("""
                        SELECT 
                            DATE_TRUNC('month', incident_date) as month,
                            COUNT(*) as records_count,
                            COUNT(DISTINCT customer_account_number) as unique_customers
                        FROM service_requests 
                        WHERE incident_date IS NOT NULL
                        GROUP BY DATE_TRUNC('month', incident_date)
                        ORDER BY month DESC
                    """)
                    
                    for row in monthly_data:
                        month_key = row['month'].strftime('%Y-%m')
                        monthly_breakdown[month_key] = {
                            'month_name': row['month'].strftime('%Y %B'),
                            'records_count': row['records_count'],
                            'unique_customers': row['unique_customers'],
                            'date_obj': row['month']
                        }
                
                postgres_data[table_name] = {
                    'row_count': count,
                    'date_info': dict(date_info) if date_info else None,
                    'has_data': count > 0
                }
            
            return {
                'status': 'success',
                'tables': postgres_data,
                'total_records': sum(table['row_count'] for table in postgres_data.values()),
                'monthly_breakdown': monthly_breakdown,
                'months_with_data': list(monthly_breakdown.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL summary: {e}")
            return {'status': 'error', 'error': str(e)}
        finally:
            if connection:
                await connection.close()

    def get_s3_file_summary(self):
        """Get S3 file summary using existing S3Connector"""
        try:
            from connectors.S3Connector import S3Connector
            
            connector = S3Connector(self.config)
            
            # Get all files from S3
            all_files = connector.list_files()
            
            # Filter for Excel/CSV files
            data_files = [f for f in all_files if f['name'].endswith(('.csv', '.xlsx', '.xls'))]
            
            # Find oldest and newest files
            oldest_file = None
            newest_file = None
            if data_files:
                # Sort by LastModified to find oldest and newest
                data_files_with_dates = [f for f in data_files if f.get('LastModified')]
                if data_files_with_dates:
                    oldest_file = min(data_files_with_dates, key=lambda x: x['LastModified'])
                    newest_file = max(data_files_with_dates, key=lambda x: x['LastModified'])
            
            # Categorize files
            file_summary = {
                'total_files': len(all_files),
                'data_files': len(data_files),
                'other_files': len(all_files) - len(data_files),
                'total_size_mb': sum(f.get('Size', 0) for f in all_files) / (1024 * 1024),
                'data_files_size_mb': sum(f.get('Size', 0) for f in data_files) / (1024 * 1024),
                'oldest_file': {
                    'filename': oldest_file['name'],
                    'date': oldest_file['LastModified'].isoformat(),
                    'readable_date': oldest_file['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    'path': oldest_file.get('Key', ''),
                    'folder': '/'.join(oldest_file.get('Key', '').split('/')[:-1]) if oldest_file.get('Key') else ''
                } if oldest_file else None,
                'newest_file': {
                    'filename': newest_file['name'],
                    'date': newest_file['LastModified'].isoformat(),
                    'readable_date': newest_file['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                    'path': newest_file.get('Key', ''),
                    'folder': '/'.join(newest_file.get('Key', '').split('/')[:-1]) if newest_file.get('Key') else ''
                } if newest_file else None
            }
            
            # Get file details
            file_details = []
            monthly_breakdown = {}
            folder_breakdown = {}
            daily_breakdown = {}
            date_hierarchy = {}
            
            for f in data_files:
                last_modified = f['LastModified'] if f.get('LastModified') else None
                last_modified_iso = last_modified.isoformat() if last_modified else None
                
                # Extract folder path and analyze hierarchy
                full_path = f.get('Key', '')
                folder_path = '/'.join(full_path.split('/')[:-1]) if '/' in full_path else 'root'
                
                # Parse date hierarchy from folder path (YYYY/MM/DD/HH pattern)
                path_parts = full_path.split('/')
                date_from_path = None
                hour_from_path = None
                
                # Look for date pattern in path: Toshiba/Historical Tickets/YYYY/MM/DD/HH/
                if len(path_parts) >= 6:
                    try:
                        year = path_parts[2]
                        month = path_parts[3]
                        day = path_parts[4]
                        hour = path_parts[5] if len(path_parts) > 5 else '00'
                        
                        if year.isdigit() and month.isdigit() and day.isdigit():
                            date_from_path = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            hour_from_path = hour.zfill(2)
                            
                            # Build date hierarchy
                            year_month = f"{year}-{month.zfill(2)}"
                            if year_month not in date_hierarchy:
                                date_hierarchy[year_month] = {
                                    'days': set(),
                                    'files_count': 0,
                                    'total_size_mb': 0
                                }
                            date_hierarchy[year_month]['days'].add(date_from_path)
                            date_hierarchy[year_month]['files_count'] += 1
                            date_hierarchy[year_month]['total_size_mb'] += f.get('Size', 0) / (1024 * 1024)
                            
                    except (ValueError, IndexError):
                        pass  # Not a date-based path
                
                # Count files per folder
                if folder_path not in folder_breakdown:
                    folder_breakdown[folder_path] = {
                        'files_count': 0,
                        'total_size_mb': 0
                    }
                folder_breakdown[folder_path]['files_count'] += 1
                folder_breakdown[folder_path]['total_size_mb'] += f.get('Size', 0) / (1024 * 1024)
                
                # Daily breakdown
                if date_from_path:
                    if date_from_path not in daily_breakdown:
                        daily_breakdown[date_from_path] = {
                            'files_count': 0,
                            'total_size_mb': 0,
                            'hours': set()
                        }
                    daily_breakdown[date_from_path]['files_count'] += 1
                    daily_breakdown[date_from_path]['total_size_mb'] += f.get('Size', 0) / (1024 * 1024)
                    if hour_from_path:
                        daily_breakdown[date_from_path]['hours'].add(hour_from_path)
                
                # Extract month-year for monthly breakdown
                if last_modified:
                    month_key = last_modified.strftime('%Y-%m')
                    if month_key not in monthly_breakdown:
                        monthly_breakdown[month_key] = {
                            'files_count': 0,
                            'total_size_mb': 0,
                            'month_name': last_modified.strftime('%Y %B')
                        }
                    monthly_breakdown[month_key]['files_count'] += 1
                    monthly_breakdown[month_key]['total_size_mb'] += f.get('Size', 0) / (1024 * 1024)
                
                file_details.append({
                    'filename': f['name'],
                    'size_mb': f.get('Size', 0) / (1024 * 1024),
                    'last_modified': last_modified_iso,
                    'full_path': full_path,
                    'folder_path': folder_path,
                    'date_from_path': date_from_path,
                    'hour_from_path': hour_from_path,
                    'estimated_records': self._estimate_records_from_file_size(f.get('Size', 0)),
                    'month_year': last_modified.strftime('%Y-%m') if last_modified else 'unknown'
                })
            
            # Sort by modification date (newest first for display)
            file_details.sort(key=lambda x: x['last_modified'] or '', reverse=True)
            
            # Get chronological order (oldest first)
            chronological_files = sorted([f for f in file_details if f['last_modified']], 
                                        key=lambda x: x['last_modified'])
            
            # Sort monthly breakdown
            sorted_months = sorted(monthly_breakdown.items(), key=lambda x: x[0], reverse=True)
            
            # Convert date_hierarchy sets to lists and sort
            for month_data in date_hierarchy.values():
                month_data['days'] = sorted(list(month_data['days']))
            
            # Sort daily breakdown
            sorted_daily = sorted(daily_breakdown.items(), key=lambda x: x[0], reverse=True)
            
            return {
                'status': 'success',
                'summary': file_summary,
                'files': file_details[:20],  # Top 20 most recent files
                'chronological_files': chronological_files[:10],  # 10 oldest files
                'all_files_count': len(file_details),
                'monthly_breakdown': dict(sorted_months),
                'months_with_data': list(monthly_breakdown.keys()),
                'folder_breakdown': folder_breakdown,
                'daily_breakdown': dict(sorted_daily),
                'date_hierarchy': date_hierarchy,
                'data_date_range': {
                    'earliest_path_date': min([f['date_from_path'] for f in file_details if f['date_from_path']], default=None),
                    'latest_path_date': max([f['date_from_path'] for f in file_details if f['date_from_path']], default=None),
                    'total_days_with_data': len(daily_breakdown)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting S3 summary: {e}")
            return {'status': 'error', 'error': str(e)}

    def _estimate_records_from_file_size(self, size_bytes):
        """Rough estimation of records based on file size"""
        if size_bytes == 0:
            return 0
        return int(size_bytes / 200)

    def check_processed_files_log(self):
        """Check what files have been processed according to logs"""
        processed_log_file = "processed_files_log.pkl"
        failed_log_file = "failed_files_log.json"
        
        processed_files = {}
        failed_files = []
        
        # Load processed files log
        if os.path.exists(processed_log_file):
            try:
                import pickle
                with open(processed_log_file, 'rb') as f:
                    processed_files = pickle.load(f)
            except Exception as e:
                logger.warning(f"Could not read processed files log: {e}")
        
        # Load failed files log
        if os.path.exists(failed_log_file):
            try:
                with open(failed_log_file, 'r') as f:
                    failed_files = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read failed files log: {e}")
        
        return {
            'processed_files_count': len(processed_files),
            'failed_files_count': len(failed_files),
            'processed_files': processed_files,
            'failed_files': failed_files,
            'logs_exist': os.path.exists(processed_log_file) or os.path.exists(failed_log_file)
        }

    def _analyze_monthly_gaps(self, postgres_data, s3_data):
        """Analyze monthly data gaps between S3 and PostgreSQL"""
        gaps_analysis = {
            'postgres_months': [],
            's3_months': [],
            'missing_in_postgres': [],
            'missing_in_s3': [],
            'common_months': []
        }
        
        try:
            # Get months from PostgreSQL
            if postgres_data['status'] == 'success' and 'monthly_breakdown' in postgres_data:
                postgres_months = set(postgres_data['monthly_breakdown'].keys())
                gaps_analysis['postgres_months'] = sorted(list(postgres_months), reverse=True)
            else:
                postgres_months = set()
            
            # Get months from S3
            if s3_data['status'] == 'success' and 'monthly_breakdown' in s3_data:
                s3_months = set(s3_data['monthly_breakdown'].keys())
                gaps_analysis['s3_months'] = sorted(list(s3_months), reverse=True)
            else:
                s3_months = set()
            
            # Find gaps
            gaps_analysis['missing_in_postgres'] = sorted(list(s3_months - postgres_months), reverse=True)
            gaps_analysis['missing_in_s3'] = sorted(list(postgres_months - s3_months), reverse=True)
            gaps_analysis['common_months'] = sorted(list(postgres_months & s3_months), reverse=True)
            
            # Convert to readable format
            def format_month_list(month_list):
                formatted = []
                for month in month_list:
                    try:
                        date_obj = datetime.strptime(month, '%Y-%m')
                        formatted.append(date_obj.strftime('%Y %B'))
                    except:
                        formatted.append(month)
                return formatted
            
            gaps_analysis['missing_in_postgres_readable'] = format_month_list(gaps_analysis['missing_in_postgres'])
            gaps_analysis['missing_in_s3_readable'] = format_month_list(gaps_analysis['missing_in_s3'])
            
        except Exception as e:
            gaps_analysis['error'] = str(e)
        
        return gaps_analysis

    async def generate_reconciliation_report(self):
        """Generate comprehensive reconciliation report"""
        logger.info("Starting data reconciliation analysis...")
        
        # Get all data
        postgres_data = await self.get_postgres_summary()
        s3_data = self.get_s3_file_summary()
        processing_logs = self.check_processed_files_log()
        
        # Calculate coverage and gaps
        coverage_analysis = self._analyze_data_coverage(postgres_data, s3_data, processing_logs)
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'data_reconciliation',
                'config_bucket': self.config.get('s3_bucket', 'unknown'),
                'config_folder': self.config.get('s3_folder', 'unknown')
            },
            'postgres_summary': postgres_data,
            's3_summary': s3_data,
            'processing_logs': processing_logs,
            'coverage_analysis': coverage_analysis,
            'recommendations': self._generate_recommendations(postgres_data, s3_data, processing_logs, coverage_analysis)
        }
        
        return report

    def _analyze_data_coverage(self, postgres_data, s3_data, processing_logs):
        """Analyze data coverage between S3 and PostgreSQL"""
        analysis = {
            'database_status': 'unknown',
            'files_vs_database': 'unknown',
            'processing_status': 'unknown'
        }
        
        try:
            # Database status
            if postgres_data['status'] == 'no_tables':
                analysis['database_status'] = 'empty_no_tables'
            elif postgres_data['status'] == 'error':
                analysis['database_status'] = 'error'
            elif postgres_data.get('total_records', 0) == 0:
                analysis['database_status'] = 'empty_with_tables'
            else:
                analysis['database_status'] = 'has_data'
            
            # S3 vs Database comparison
            if s3_data['status'] == 'success' and postgres_data['status'] == 'success':
                s3_files_count = s3_data['summary']['data_files']
                processed_files_count = processing_logs['processed_files_count']
                
                if processed_files_count == 0:
                    analysis['files_vs_database'] = 'no_files_processed'
                elif processed_files_count < s3_files_count:
                    analysis['files_vs_database'] = 'partial_processing'
                    analysis['missing_files'] = s3_files_count - processed_files_count
                else:
                    analysis['files_vs_database'] = 'full_processing'
            
            # Processing status
            if processing_logs['failed_files_count'] > 0:
                analysis['processing_status'] = f"has_failures_{processing_logs['failed_files_count']}_files"
            elif processing_logs['processed_files_count'] > 0:
                analysis['processing_status'] = 'processing_successful'
            else:
                analysis['processing_status'] = 'no_processing_attempted'
            
            # Calculate estimated data coverage percentage
            if s3_data['status'] == 'success' and postgres_data['status'] == 'success':
                estimated_s3_records = sum(f['estimated_records'] for f in s3_data['files'])
                actual_db_records = postgres_data.get('total_records', 0)
                
                if estimated_s3_records > 0:
                    coverage_percentage = min(100, (actual_db_records / estimated_s3_records) * 100)
                    analysis['estimated_data_coverage_percentage'] = round(coverage_percentage, 2)
                else:
                    analysis['estimated_data_coverage_percentage'] = 0
            
            # Monthly data gaps analysis
            analysis['monthly_gaps'] = self._analyze_monthly_gaps(postgres_data, s3_data)
        
        except Exception as e:
            analysis['analysis_error'] = str(e)
        
        return analysis

    def _generate_recommendations(self, postgres_data, s3_data, processing_logs, coverage_analysis):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Database recommendations
        if postgres_data['status'] == 'no_tables':
            recommendations.append({
                'priority': 'HIGH',
                'category': 'database',
                'action': 'Run initial ETL setup to create database tables',
                'command': 'python main.py'
            })
        elif postgres_data.get('total_records', 0) == 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'data',
                'action': 'Database tables exist but are empty - run ETL to load data',
                'command': 'python main.py'
            })
        
        # S3 processing recommendations
        if s3_data['status'] == 'success':
            if coverage_analysis.get('files_vs_database') == 'no_files_processed':
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'processing',
                    'action': f"Process {s3_data['summary']['data_files']} available S3 files",
                    'details': f"Found {s3_data['summary']['data_files']} CSV/Excel files in S3 but none have been processed"
                })
            elif coverage_analysis.get('files_vs_database') == 'partial_processing':
                missing = coverage_analysis.get('missing_files', 0)
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'processing',
                    'action': f"Process {missing} remaining S3 files",
                    'details': f"{missing} files have not been processed yet"
                })
        
        # Failed files recommendations
        if processing_logs['failed_files_count'] > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'data_quality',
                'action': f"Investigate and retry {processing_logs['failed_files_count']} failed files",
                'details': "Check failed_files_log.json for error details"
            })
        
        return recommendations

    def print_summary_report(self, report):
        """Print a human-readable summary of the report"""
        print("\n" + "="*80)
        print("           DATA RECONCILIATION REPORT")
        print("="*80)
        print(f"Generated: {report['report_metadata']['generated_at']}")
        print(f"S3 Bucket: {report['report_metadata']['config_bucket']}")
        print(f"S3 Folder: {report['report_metadata']['config_folder']}")
        
        # PostgreSQL Summary
        print(f"\nPostgreSQL DATABASE:")
        postgres = report['postgres_summary']
        if postgres['status'] == 'success':
            print(f"   Status: Connected")
            print(f"   Total Records: {postgres['total_records']:,}")
            print(f"   Tables with Data:")
            for table, data in postgres['tables'].items():
                status = "✓" if data['has_data'] else "Empty"
                print(f"     - {table}: {data['row_count']:,} records {status}")
        else:
            print(f"   Status: Error - {postgres.get('message', 'Unknown')}")
        
        # S3 Summary
        print(f"\nS3 BUCKET:")
        s3 = report['s3_summary']
        if s3['status'] == 'success':
            summary = s3['summary']
            print(f"   Status: Connected")
            print(f"   Total Files: {summary['total_files']}")
            print(f"   Data Files (CSV/Excel): {summary['data_files']}")
            print(f"   Total Data Size: {summary['data_files_size_mb']:.1f} MB")
            
            # Show data timeline from folder structure
            if s3.get('data_date_range'):
                date_range = s3['data_date_range']
                print(f"   DATA TIMELINE (from folder structure):")
                if date_range['earliest_path_date'] and date_range['latest_path_date']:
                    print(f"     First Data: {date_range['earliest_path_date']}")
                    print(f"     Latest Data: {date_range['latest_path_date']}")
                    print(f"     Total Days with Data: {date_range['total_days_with_data']}")
            
            # Show oldest and newest files (by upload time)
            if summary.get('oldest_file'):
                oldest = summary['oldest_file']
                print(f"   FIRST FILE UPLOADED TO S3:")
                print(f"     File: {oldest['filename']}")
                print(f"     Upload Date: {oldest['readable_date']}")
                print(f"     Folder: {oldest['folder']}")
            
            if summary.get('newest_file'):
                newest = summary['newest_file']
                print(f"   LATEST FILE UPLOADED TO S3:")
                print(f"     File: {newest['filename']}")
                print(f"     Upload Date: {newest['readable_date']}")
                print(f"     Folder: {newest['folder']}")
            
            # Show date hierarchy (YYYY/MM breakdown)
            if s3.get('date_hierarchy'):
                print(f"   MONTHLY DATA FOLDERS:")
                for month, info in list(s3['date_hierarchy'].items())[:6]:  # Show last 6 months
                    days_count = len(info['days'])
                    print(f"     - {month}: {info['files_count']} files across {days_count} days ({info['total_size_mb']:.1f} MB)")
            
            # Show daily breakdown (most recent days)
            if s3.get('daily_breakdown'):
                print(f"   RECENT DAILY DATA:")
                for date, info in list(s3['daily_breakdown'].items())[:5]:  # Show last 5 days
                    hours_count = len(info['hours']) if 'hours' in info else 0
                    print(f"     - {date}: {info['files_count']} files in {hours_count} hour folders ({info['total_size_mb']:.1f} MB)")
        else:
            print(f"   Status: Error - {s3.get('error', 'Unknown error')}")
        
        # Processing Logs
        print(f"\nPROCESSING LOGS:")
        logs = report['processing_logs']
        print(f"   Processed Files: {logs['processed_files_count']}")
        print(f"   Failed Files: {logs['failed_files_count']}")
        print(f"   Logs Available: {'Yes' if logs['logs_exist'] else 'No'}")
        
        # Coverage Analysis
        print(f"\nDATA COVERAGE ANALYSIS:")
        coverage = report['coverage_analysis']
        print(f"   Database Status: {coverage['database_status']}")
        print(f"   Processing Status: {coverage['processing_status']}")
        if 'estimated_data_coverage_percentage' in coverage:
            pct = coverage['estimated_data_coverage_percentage']
            status = "Good" if pct > 80 else "Partial" if pct > 50 else "Low"
            print(f"   Estimated Coverage: {pct}% ({status})")
        
        # Monthly Gaps Analysis
        if 'monthly_gaps' in coverage:
            gaps = coverage['monthly_gaps']
            print(f"\nMONTHLY DATA AVAILABILITY:")
            
            # PostgreSQL months
            if gaps.get('postgres_months'):
                print(f"   Database has data for: {len(gaps['postgres_months'])} months")
                recent_db_months = gaps['postgres_months'][:6]  # Show last 6 months
                print(f"   Recent months in DB: {', '.join(recent_db_months)}")
            
            # S3 months
            if gaps.get('s3_months'):
                print(f"   S3 has files for: {len(gaps['s3_months'])} months")
                recent_s3_months = gaps['s3_months'][:6]  # Show last 6 months
                print(f"   Recent months in S3: {', '.join(recent_s3_months)}")
            
            # Missing data alerts
            if gaps.get('missing_in_postgres'):
                print(f"   MISSING IN DATABASE: {', '.join(gaps['missing_in_postgres_readable'][:5])}")
                if len(gaps['missing_in_postgres']) > 5:
                    print(f"   ... and {len(gaps['missing_in_postgres']) - 5} more months")
            
            if gaps.get('missing_in_s3'):
                print(f"   MISSING IN S3: {', '.join(gaps['missing_in_s3_readable'][:5])}")
                if len(gaps['missing_in_s3']) > 5:
                    print(f"   ... and {len(gaps['missing_in_s3']) - 5} more months")
            
            if gaps.get('common_months'):
                print(f"   Data exists in both: {len(gaps['common_months'])} months")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        recommendations = report['recommendations']
        if not recommendations:
            print("   No immediate actions needed")
        else:
            for i, rec in enumerate(recommendations, 1):
                priority_symbol = "HIGH" if rec['priority'] == 'HIGH' else "MED"
                print(f"   {i}. [{priority_symbol}] {rec['action']}")
                if 'details' in rec:
                    print(f"      Details: {rec['details']}")
                if 'command' in rec:
                    print(f"      Command: {rec['command']}")
        
        print("\n" + "="*80)

    def save_to_excel(self, report, filename=None):
        """Save report to Excel using pandas"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data_reconciliation_report_{timestamp}.xlsx"
        
        try:
            # Prepare data for Excel sheets
            sheets_data = {}
            
            # 1. Summary sheet
            summary_data = []
            postgres = report['postgres_summary']
            s3 = report['s3_summary']
            coverage = report['coverage_analysis']
            
            summary_data.append(['Report Generated', report['report_metadata']['generated_at']])
            summary_data.append(['S3 Bucket', report['report_metadata']['config_bucket']])
            summary_data.append(['S3 Folder', report['report_metadata']['config_folder']])
            summary_data.append(['', ''])
            summary_data.append(['PostgreSQL Status', 'Connected' if postgres['status'] == 'success' else 'Error'])
            if postgres['status'] == 'success':
                summary_data.append(['Total DB Records', postgres['total_records']])
                for table, data in postgres['tables'].items():
                    summary_data.append([f'  {table}', f"{data['row_count']} records"])
            
            summary_data.append(['', ''])
            summary_data.append(['S3 Status', 'Connected' if s3['status'] == 'success' else 'Error'])
            if s3['status'] == 'success':
                summary_data.append(['Total S3 Files', s3['summary']['total_files']])
                summary_data.append(['Data Files', s3['summary']['data_files']])
                summary_data.append(['Data Size (MB)', f"{s3['summary']['data_files_size_mb']:.1f}"])
            
            summary_data.append(['', ''])
            summary_data.append(['Processing Status', coverage.get('processing_status', 'Unknown')])
            if 'estimated_data_coverage_percentage' in coverage:
                summary_data.append(['Data Coverage %', coverage['estimated_data_coverage_percentage']])
            
            sheets_data['Summary'] = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            
            # 2. S3 Files sheet (Recent files)
            if s3['status'] == 'success' and s3['files']:
                s3_files_data = []
                for f in s3['files']:
                    s3_files_data.append([
                        f['filename'],
                        f"{f['size_mb']:.2f}",
                        f['last_modified'][:19] if f['last_modified'] else 'Unknown',
                        f['estimated_records'],
                        f['month_year'],
                        f.get('folder_path', '')
                    ])
                sheets_data['S3_Recent_Files'] = pd.DataFrame(s3_files_data, 
                    columns=['Filename', 'Size_MB', 'Last_Modified', 'Est_Records', 'Month', 'Folder_Path'])
            
            # 2b. S3 Chronological Files sheet (Oldest files first)
            if s3['status'] == 'success' and s3.get('chronological_files'):
                chrono_data = []
                for f in s3['chronological_files']:
                    chrono_data.append([
                        f['filename'],
                        f"{f['size_mb']:.2f}",
                        f['last_modified'][:19] if f['last_modified'] else 'Unknown',
                        f['estimated_records'],
                        f['month_year'],
                        f.get('folder_path', '')
                    ])
                sheets_data['S3_Chronological'] = pd.DataFrame(chrono_data, 
                    columns=['Filename', 'Size_MB', 'Upload_Date', 'Est_Records', 'Month', 'Folder_Path'])
            
            # 2c. Folder Breakdown sheet
            if s3['status'] == 'success' and s3.get('folder_breakdown'):
                folder_data = []
                for folder_path, info in s3['folder_breakdown'].items():
                    folder_data.append([
                        folder_path,
                        info['files_count'],
                        f"{info['total_size_mb']:.2f}"
                    ])
                sheets_data['Folder_Breakdown'] = pd.DataFrame(folder_data,
                    columns=['Folder_Path', 'Files_Count', 'Total_Size_MB'])
            
            # 3. Monthly Gaps sheet
            gaps = coverage.get('monthly_gaps', {})
            if gaps:
                monthly_data = []
                all_months = set(gaps.get('postgres_months', []) + gaps.get('s3_months', []))
                for month in sorted(all_months, reverse=True):
                    in_postgres = month in gaps.get('postgres_months', [])
                    in_s3 = month in gaps.get('s3_months', [])
                    status = 'Both' if (in_postgres and in_s3) else 'DB Only' if in_postgres else 'S3 Only' if in_s3 else 'Neither'
                    
                    try:
                        date_obj = datetime.strptime(month, '%Y-%m')
                        month_name = date_obj.strftime('%Y %B')
                    except:
                        month_name = month
                    
                    monthly_data.append([month, month_name, in_postgres, in_s3, status])
                
                sheets_data['Monthly_Analysis'] = pd.DataFrame(monthly_data,
                    columns=['Month_Code', 'Month_Name', 'In_Database', 'In_S3', 'Status'])
            
            # 4. Recommendations sheet
            if report['recommendations']:
                rec_data = []
                for rec in report['recommendations']:
                    rec_data.append([
                        rec['priority'],
                        rec['category'],
                        rec['action'],
                        rec.get('details', ''),
                        rec.get('command', '')
                    ])
                sheets_data['Recommendations'] = pd.DataFrame(rec_data,
                    columns=['Priority', 'Category', 'Action', 'Details', 'Command'])
            
            # Write to Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for sheet_name, df in sheets_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"Excel report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving Excel report: {e}")
            # Fallback to JSON
            json_filename = filename.replace('.xlsx', '.json')
            return self.save_to_json(report, json_filename)

    def save_to_json(self, report, filename=None):
        """Save report as JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data_reconciliation_report_{timestamp}.json"
        
        try:
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            def process_dict(d):
                if isinstance(d, dict):
                    return {k: process_dict(v) for k, v in d.items()}
                elif isinstance(d, list):
                    return [process_dict(item) for item in d]
                else:
                    return convert_datetime(d)
            
            processed_report = process_dict(report)
            
            with open(filename, 'w') as f:
                json.dump(processed_report, f, indent=2, default=str)
            
            print(f"JSON report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
            return None

async def main():
    """Main function to run reconciliation report"""
    # Load configuration
    config_paths = ['config/settings.json', 'settings.json']
    config = None
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
            break
    
    if not config:
        print("Could not find settings.json configuration file")
        print("Please ensure config/settings.json exists with your S3 and database settings")
        return
    
    # Generate reconciliation report
    reconciler = DataReconciliationReport(config)
    report = await reconciler.generate_reconciliation_report()
    
    # Print summary
    reconciler.print_summary_report(report)
    
    # Ask user for export format
    print("\nExport Options:")
    print("1. Excel (.xlsx)")
    print("2. JSON (.json)")
    print("3. Both")
    print("4. No export")
    
    try:
        choice = input("\nChoose export format (1-4): ").strip()
        
        if choice == '1':
            # Excel only
            reconciler.save_to_excel(report)
        elif choice == '2':
            # JSON only
            reconciler.save_to_json(report)
        elif choice == '3':
            # Both formats
            reconciler.save_to_excel(report)
            reconciler.save_to_json(report)
        elif choice == '4':
            print("No export selected.")
        else:
            # Default to Excel
            print("Invalid choice, defaulting to Excel export...")
            reconciler.save_to_excel(report)
            
    except KeyboardInterrupt:
        print("\nExport cancelled.")
    except Exception as e:
        print(f"Export error: {e}")
        # Fallback to JSON
        reconciler.save_to_json(report)
    
    return report

if __name__ == "__main__":
    asyncio.run(main())