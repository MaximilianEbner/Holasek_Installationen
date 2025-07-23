#!/usr/bin/env python3
"""
Migration script to add WorkStep and WorkPart models and update WorkInstruction field
"""

import os
import sys
import sqlite3
from datetime import datetime

def run_migration():
    """Run the database migration"""
    db_path = 'instance/installation_business.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    # Create backup
    backup_path = f'instance/installation_business_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting migration...")
        
        # 1. Update WorkInstruction table - rename safety_notes to sonstiges
        print("1. Updating WorkInstruction table...")
        try:
            # Check if safety_notes column exists
            cursor.execute("PRAGMA table_info(work_instruction)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'safety_notes' in column_names and 'sonstiges' not in column_names:
                # Rename safety_notes to sonstiges
                cursor.execute("ALTER TABLE work_instruction RENAME COLUMN safety_notes TO sonstiges")
                print("   - Renamed safety_notes to sonstiges")
            elif 'sonstiges' not in column_names:
                # Add sonstiges column if it doesn't exist
                cursor.execute("ALTER TABLE work_instruction ADD COLUMN sonstiges TEXT")
                print("   - Added sonstiges column")
            else:
                print("   - sonstiges column already exists")
                
        except Exception as e:
            print(f"   - Error updating WorkInstruction: {e}")
        
        # 2. Create WorkStep table
        print("2. Creating WorkStep table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_step (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_instruction_id INTEGER NOT NULL,
                    step_number INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    notes TEXT,
                    estimated_time INTEGER,
                    is_completed BOOLEAN DEFAULT 0,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_instruction_id) REFERENCES work_instruction (id)
                )
            """)
            print("   - WorkStep table created successfully")
        except Exception as e:
            print(f"   - Error creating WorkStep table: {e}")
        
        # 3. Create WorkPart table
        print("3. Creating WorkPart table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_part (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_instruction_id INTEGER NOT NULL,
                    part_name VARCHAR(255) NOT NULL,
                    part_number VARCHAR(100),
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit VARCHAR(20) DEFAULT 'Stk',
                    storage_location VARCHAR(255),
                    notes TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_instruction_id) REFERENCES work_instruction (id)
                )
            """)
            print("   - WorkPart table created successfully")
        except Exception as e:
            print(f"   - Error creating WorkPart table: {e}")
        
        # Commit all changes
        conn.commit()
        print("Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
