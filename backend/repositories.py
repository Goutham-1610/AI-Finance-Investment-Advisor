"""
Data access layer - Repository pattern implementation
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime

from .database import Database
from .models import Transaction, Budget, FinancialGoal, Category, TransactionType


class TransactionRepository:
    """Repository for transaction data access"""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, transaction: Transaction) -> int:
        """Create a new transaction"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions 
                (date, amount, merchant, category, transaction_type, notes, tags, 
                 is_recurring, confidence_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.date.isoformat(),
                transaction.amount,
                transaction.merchant,
                transaction.category.value,
                transaction.transaction_type.value,
                transaction.notes,
                json.dumps(transaction.tags),
                transaction.is_recurring,
                transaction.confidence_score,
                transaction.created_at.isoformat(),
                transaction.updated_at.isoformat()
            ))
            return cursor.lastrowid
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            return self._row_to_transaction(row) if row else None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Transaction]:
        """Get all transactions with optional limit and offset"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM transactions ORDER BY date DESC"
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            cursor.execute(query)
            return [self._row_to_transaction(row) for row in cursor.fetchall()]
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions within date range"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            return [self._row_to_transaction(row) for row in cursor.fetchall()]
    
    def get_by_category(self, category: Category) -> List[Transaction]:
        """Get transactions by category"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions WHERE category = ?
                ORDER BY date DESC
            """, (category.value,))
            return [self._row_to_transaction(row) for row in cursor.fetchall()]
    
    def get_by_merchant(self, merchant: str) -> List[Transaction]:
        """Get transactions by merchant"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE merchant LIKE ?
                ORDER BY date DESC
            """, (f"%{merchant}%",))
            return [self._row_to_transaction(row) for row in cursor.fetchall()]
    
    def search(self, query: str) -> List[Transaction]:
        """Search transactions by merchant or notes"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE merchant LIKE ? OR notes LIKE ?
                ORDER BY date DESC
            """, (f"%{query}%", f"%{query}%"))
            return [self._row_to_transaction(row) for row in cursor.fetchall()]
    
    def update(self, transaction: Transaction) -> bool:
        """Update existing transaction"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            transaction.updated_at = datetime.now()
            cursor.execute("""
                UPDATE transactions SET
                    date = ?, amount = ?, merchant = ?, category = ?,
                    transaction_type = ?, notes = ?, tags = ?,
                    is_recurring = ?, confidence_score = ?, updated_at = ?
                WHERE id = ?
            """, (
                transaction.date.isoformat(),
                transaction.amount,
                transaction.merchant,
                transaction.category.value,
                transaction.transaction_type.value,
                transaction.notes,
                json.dumps(transaction.tags),
                transaction.is_recurring,
                transaction.confidence_score,
                transaction.updated_at.isoformat(),
                transaction.id
            ))
            return cursor.rowcount > 0
    
    def delete(self, transaction_id: int) -> bool:
        """Delete transaction"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            return cursor.rowcount > 0
    
    def get_count(self) -> int:
        """Get total transaction count"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            return cursor.fetchone()[0]
    
    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """Convert database row to Transaction object"""
        return Transaction(
            id=row['id'],
            date=datetime.fromisoformat(row['date']),
            amount=row['amount'],
            merchant=row['merchant'],
            category=Category(row['category']),
            transaction_type=TransactionType(row['transaction_type']),
            notes=row['notes'] or "",
            tags=json.loads(row['tags']) if row['tags'] else [],
            is_recurring=bool(row['is_recurring']),
            confidence_score=row['confidence_score'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


class BudgetRepository:
    """Repository for budget data access"""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, budget: Budget) -> int:
        """Create new budget"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets 
                (category, amount, period, start_date, end_date, alert_threshold, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget.category.value,
                budget.amount,
                budget.period,
                budget.start_date.isoformat(),
                budget.end_date.isoformat() if budget.end_date else None,
                budget.alert_threshold,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def get_by_id(self, budget_id: int) -> Optional[Budget]:
        """Get budget by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budgets WHERE id = ?", (budget_id,))
            row = cursor.fetchone()
            return self._row_to_budget(row) if row else None
    
    def get_all(self) -> List[Budget]:
        """Get all budgets"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budgets ORDER BY category")
            return [self._row_to_budget(row) for row in cursor.fetchall()]
    
    def get_by_category(self, category: Category) -> Optional[Budget]:
        """Get budget for specific category"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM budgets WHERE category = ?
                ORDER BY created_at DESC LIMIT 1
            """, (category.value,))
            row = cursor.fetchone()
            return self._row_to_budget(row) if row else None
    
    def update(self, budget: Budget) -> bool:
        """Update budget"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE budgets SET
                    amount = ?, period = ?, start_date = ?, 
                    end_date = ?, alert_threshold = ?, updated_at = ?
                WHERE id = ?
            """, (
                budget.amount,
                budget.period,
                budget.start_date.isoformat(),
                budget.end_date.isoformat() if budget.end_date else None,
                budget.alert_threshold,
                datetime.now().isoformat(),
                budget.id
            ))
            return cursor.rowcount > 0
    
    def delete(self, budget_id: int) -> bool:
        """Delete budget"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
            return cursor.rowcount > 0
    
    def _row_to_budget(self, row: sqlite3.Row) -> Budget:
        """Convert database row to Budget object"""
        return Budget(
            id=row['id'],
            category=Category(row['category']),
            amount=row['amount'],
            period=row['period'],
            start_date=datetime.fromisoformat(row['start_date']),
            end_date=datetime.fromisoformat(row['end_date']) if row['end_date'] else None,
            alert_threshold=row['alert_threshold']
        )


class GoalRepository:
    """Repository for financial goals data access"""
    
    def __init__(self, database: Database):
        self.db = database
    
    def create(self, goal: FinancialGoal) -> int:
        """Create new goal"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO goals 
                (name, target_amount, current_amount, deadline, category, priority,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.name,
                goal.target_amount,
                goal.current_amount,
                goal.deadline.isoformat() if goal.deadline else None,
                goal.category,
                goal.priority,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def get_all(self) -> List[FinancialGoal]:
        """Get all goals"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals ORDER BY priority, deadline")
            return [self._row_to_goal(row) for row in cursor.fetchall()]
    
    def update(self, goal: FinancialGoal) -> bool:
        """Update goal"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE goals SET
                    name = ?, target_amount = ?, current_amount = ?,
                    deadline = ?, category = ?, priority = ?, updated_at = ?
                WHERE id = ?
            """, (
                goal.name,
                goal.target_amount,
                goal.current_amount,
                goal.deadline.isoformat() if goal.deadline else None,
                goal.category,
                goal.priority,
                datetime.now().isoformat(),
                goal.id
            ))
            return cursor.rowcount > 0
    
    def delete(self, goal_id: int) -> bool:
        """Delete goal"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0
    
    def _row_to_goal(self, row: sqlite3.Row) -> FinancialGoal:
        """Convert database row to FinancialGoal object"""
        return FinancialGoal(
            id=row['id'],
            name=row['name'],
            target_amount=row['target_amount'],
            current_amount=row['current_amount'],
            deadline=datetime.fromisoformat(row['deadline']) if row['deadline'] else None,
            category=row['category'],
            priority=row['priority']
        )