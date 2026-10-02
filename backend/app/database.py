import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
import app.config as config

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path if db_path is not None else config.DB_FILE
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path: Optional[str] = None) -> None:
    with get_db(db_path) as conn:
        # Patients table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_code TEXT UNIQUE,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                contact TEXT,
                blood_group TEXT,
                medical_history TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Assessments table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                patient_code TEXT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                bmi REAL NOT NULL,
                systolic_bp REAL NOT NULL,
                glucose REAL NOT NULL,
                cholesterol REAL NOT NULL,
                heart_rate REAL NOT NULL,
                smoking TEXT NOT NULL,
                activity TEXT NOT NULL,
                diabetes_risk REAL NOT NULL,
                heart_risk REAL NOT NULL,
                hypertension_risk REAL NOT NULL,
                overall_risk TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
            )
        """)

        # Auto-migration columns check for backward compatibility
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(assessments)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        if "patient_id" not in existing_cols:
            cursor.execute("ALTER TABLE assessments ADD COLUMN patient_id INTEGER")
        if "patient_code" not in existing_cols:
            cursor.execute("ALTER TABLE assessments ADD COLUMN patient_code TEXT")
            
        # Create helpful indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_patient_id ON assessments(patient_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_code ON patients(patient_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name COLLATE NOCASE)")
