"""
Database management and operations
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional
from pathlib import Path
import shutil
from datetime import datetime

from .config import DATABASE_PATH, DATABASE_BACKUP_DIR


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    merchant TEXT NOT NULL,
                    category TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    notes TEXT,
                    tags TEXT,
                    is_recurring BOOLEAN DEFAULT 0,
                    confidence_score REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Budgets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    period TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    alert_threshold REAL DEFAULT 0.8,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Goals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    deadline TEXT,
                    category TEXT,
                    priority INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # ML Models metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ml_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    accuracy REAL,
                    trained_at TEXT NOT NULL,
                    model_data BLOB
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_date 
                ON transactions(date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_category 
                ON transactions(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_merchant 
                ON transactions(merchant)
            """)
    
    def backup(self) -> Path:
        """Create a backup of the database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = DATABASE_BACKUP_DIR / f"finance_backup_{timestamp}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path
    
    def restore(self, backup_path: Path):
        """Restore database from backup"""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        shutil.copy2(backup_path, self.db_path)
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Transaction count
            cursor.execute("SELECT COUNT(*) FROM transactions")
            stats['total_transactions'] = cursor.fetchone()[0]
            
            # Budget count
            cursor.execute("SELECT COUNT(*) FROM budgets")
            stats['total_budgets'] = cursor.fetchone()[0]
            
            # Goal count
            cursor.execute("SELECT COUNT(*) FROM goals")
            stats['total_goals'] = cursor.fetchone()[0]
            
            # Database size
            stats['db_size_bytes'] = self.db_path.stat().st_size
            stats['db_size_mb'] = stats['db_size_bytes'] / (1024 * 1024)
            
            return stats
    
    def vacuum(self):
        """Optimize database (reclaim space)"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
    
    def clear_all_data(self):
        """Clear all data from database (use with caution!)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM budgets")
            cursor.execute("DELETE FROM goals")
            cursor.execute("DELETE FROM ml_models")