#!/usr/bin/env python
import os
import sys
import sqlite3
import pandas as pd
import django
import json
import traceback
from django.db import connections
from django.conf import settings
from datetime import datetime, date

# Setup Django environment
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniversityApp.settings')
django.setup()

def adapt_complex_data(obj):
    """Convert complex data types to SQLite-compatible formats"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict) or isinstance(obj, list):
        return json.dumps(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    return str(obj)

def postgres_to_sqlite(sqlite_file='django_db_dump.sqlite'):
    """
    Export Django's PostgreSQL database to SQLite format with improved error handling
    """
    print(f"Starting export from PostgreSQL to SQLite: {sqlite_file}")
    
    # Get database settings from Django
    db_settings = settings.DATABASES['default']
    db_name = db_settings['NAME']
    
    print(f"Exporting database: {db_name}")
    
    # Create connection to SQLite database
    sqlite_conn = sqlite3.connect(sqlite_file)
    sqlite_conn.execute("PRAGMA foreign_keys = OFF")  # Disable foreign key checks during import
    
    # Get Django database connection
    postgres_conn = connections['default']
    postgres_cursor = postgres_conn.cursor()
    
    # Get list of tables (excluding Django migrations and SQLite-specific tables)
    postgres_cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name NOT LIKE 'sqlite_%'
        ORDER BY table_name
    """)
    
    tables = [table[0] for table in postgres_cursor.fetchall()]
    
    print(f"Found {len(tables)} tables to migrate")
    
    # Process each table
    for i, table_name in enumerate(tables):
        print(f"Processing table {i+1}/{len(tables)}: {table_name}")
        
        try:
            # Get table schema
            postgres_cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [table_name])
            
            columns = postgres_cursor.fetchall()
            column_names = [col[0] for col in columns]
            
            # Generate CREATE TABLE statement for SQLite
            create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            
            # Get primary key
            postgres_cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, [table_name])
            
            pk_columns = [pk[0] for pk in postgres_cursor.fetchall()]
            
            # Build column definitions
            column_defs = []
            for col_name, col_type, is_nullable in columns:
                # Map PostgreSQL types to SQLite types
                sqlite_type = "TEXT"  # Default to TEXT
                if col_type in ('integer', 'bigint', 'smallint'):
                    sqlite_type = "INTEGER"
                elif col_type in ('numeric', 'decimal', 'real', 'double precision'):
                    sqlite_type = "REAL"
                elif col_type in ('boolean'):
                    sqlite_type = "INTEGER"  # SQLite uses 0/1 for booleans
                
                # Handle NULL constraints
                null_constraint = "" if is_nullable == 'YES' else " NOT NULL"
                
                # Add primary key constraint if applicable
                if col_name in pk_columns:
                    column_defs.append(f"{col_name} {sqlite_type} PRIMARY KEY{null_constraint}")
                else:
                    column_defs.append(f"{col_name} {sqlite_type}{null_constraint}")
            
            create_statement += ", ".join(column_defs) + ")"
            
            # Create table in SQLite
            try:
                sqlite_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                sqlite_conn.execute(create_statement)
                sqlite_conn.commit()
            except sqlite3.Error as e:
                print(f"Error creating table {table_name}: {e}")
                continue
            
            # Fetch data in batches
            batch_size = 1000  # Smaller batch size for better error handling
            offset = 0
            total_rows = 0
            
            while True:
                try:
                    # Fetch a batch of data
                    postgres_cursor.execute(f"SELECT * FROM {table_name} LIMIT %s OFFSET %s", 
                                        [batch_size, offset])
                    rows = postgres_cursor.fetchall()
                    
                    if not rows:
                        break
                    
                    # Convert rows directly to list of tuples with proper type handling
                    processed_rows = []
                    for row in rows:
                        processed_row = []
                        for item in row:
                            if item is None:
                                processed_row.append(None)
                            elif isinstance(item, (datetime, date, dict, list, bytes)):
                                processed_row.append(adapt_complex_data(item))
                            else:
                                processed_row.append(item)
                        processed_rows.append(tuple(processed_row))
                    
                    # Insert directly using executemany instead of pandas
                    cursor = sqlite_conn.cursor()
                    placeholders = ','.join(['?' for _ in column_names])
                    cursor.executemany(
                        f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})",
                        processed_rows
                    )
                    sqlite_conn.commit()
                    
                    total_rows += len(rows)
                    print(f"  Migrated {len(rows)} rows (offset {offset})")
                    offset += batch_size
                    
                    if len(rows) < batch_size:
                        break
                        
                except Exception as e:
                    print(f"  Error processing batch at offset {offset}: {e}")
                    print("  Attempting row-by-row insertion...")
                    
                    # Try inserting rows one by one
                    inserted = 0
                    cursor = sqlite_conn.cursor()
                    placeholders = ','.join(['?' for _ in column_names])
                    
                    for row in rows:
                        try:
                            processed_row = []
                            for item in row:
                                if item is None:
                                    processed_row.append(None)
                                elif isinstance(item, (datetime, date, dict, list, bytes)):
                                    processed_row.append(adapt_complex_data(item))
                                else:
                                    processed_row.append(item)
                                    
                            cursor.execute(
                                f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})",
                                processed_row
                            )
                            inserted += 1
                        except Exception as row_error:
                            print(f"    Skipping row due to error: {str(row_error)[:100]}...")
                    
                    sqlite_conn.commit()
                    print(f"  Successfully inserted {inserted}/{len(rows)} rows individually")
                    offset += batch_size
            
            print(f"  Completed table {table_name}, total rows: {total_rows}")
            
        except Exception as table_error:
            print(f"Failed to process table {table_name}: {table_error}")
            traceback.print_exc()
            print("Continuing with next table...")
    
    # Re-enable foreign key checks
    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    sqlite_conn.commit()
    sqlite_conn.close()
    
    print(f"Export completed successfully. SQLite database saved as: {sqlite_file}")

if __name__ == "__main__":
    # Allow specifying output file as command line argument
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'django_db_dump.sqlite'
    postgres_to_sqlite(output_file)