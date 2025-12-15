"""
Business logic layer - Main service orchestrator
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import csv
import io

from .database import Database
from .repositories import TransactionRepository, BudgetRepository, GoalRepository
from .analytics import AnalyticsEngine
from .ml_engine import MLEngine
from .models import Transaction, Budget, FinancialGoal, Category, TransactionType
from .config import DATABASE_PATH
from backend.ml.categorizer import TransactionCategorizer
from backend.ml.rules import rule_based_category



class FinanceService:
    """Main service orchestrating all operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = Database(db_path or DATABASE_PATH)
        self.transaction_repo = TransactionRepository(self.db)
        self.budget_repo = BudgetRepository(self.db)
        self.goal_repo = GoalRepository(self.db)
        self.analytics = AnalyticsEngine(self.transaction_repo)
        self.ml_engine = MLEngine(self.transaction_repo)
        self.categorizer = TransactionCategorizer()
        self.categorizer.load()
    
        
        # Train ML engine on startup
        self._initialize_ml_engine()
    
    def _initialize_ml_engine(self):
        """Initialize ML engine with historical data"""
        try:
            self.ml_engine.train_from_history()
        except Exception as e:
            print(f"Warning: Could not train ML engine: {e}")
    
    # ========================================================================
    # Transaction Operations
    # ========================================================================
    
    def add_transaction(
        self,
        date: datetime,
        amount: float,
        merchant: str,
        category: Optional[Category] = None,
        transaction_type: Optional[TransactionType] = None,
        notes: str = "",
        tags: List[str] = None
    ) -> Transaction:
        """Add new transaction with auto-categorization"""
        
        # Auto-detect transaction type if not provided
        if transaction_type is None:
            transaction_type = (
                TransactionType.INCOME if amount > 0 
                else TransactionType.EXPENSE
            )
        
        # Auto-predict category if not provided
        if category is None:
            category, confidence = self.ml_engine.predict_category(merchant, amount)
        else:
            confidence = 1.0
        
        transaction = Transaction(
            date=date,
            amount=amount,
            merchant=merchant,
            category=category,
            transaction_type=transaction_type,
            notes=notes,
            tags=tags or [],
            confidence_score=confidence
        )
        
        transaction_id = self.transaction_repo.create(transaction)
        transaction.id = transaction_id
        
        # Retrain ML engine with new data
        self.ml_engine.train_from_history()
        
        return transaction
    
    def get_all_transactions(
        self, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Transaction]:
        """Get all transactions with pagination"""
        return self.transaction_repo.get_all(limit=limit, offset=offset)
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get single transaction by ID"""
        return self.transaction_repo.get_by_id(transaction_id)
    
    def update_transaction(self, transaction: Transaction) -> bool:
        """Update existing transaction"""
        success = self.transaction_repo.update(transaction)
        if success:
            self.ml_engine.train_from_history()
        return success
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction"""
        success = self.transaction_repo.delete(transaction_id)
        if success:
            self.ml_engine.train_from_history()
        return success
    
    def search_transactions(self, query: str) -> List[Transaction]:
        """Search transactions"""
        return self.transaction_repo.search(query)
    
    # ========================================================================
    # Dashboard & Analytics
    # ========================================================================
    
    def get_dashboard_data(self, days: int = 30) -> dict:
        """Get comprehensive dashboard data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        summary = self.analytics.get_summary(start_date, end_date)
        category_breakdown = self.analytics.get_category_breakdown(start_date, end_date)
        trends = self.analytics.detect_spending_trends(days)
        anomalies = self.analytics.find_anomalies()
        merchant_analysis = self.analytics.get_merchant_analysis(start_date, end_date)
        
        return {
            'summary': summary,
            'category_breakdown': category_breakdown,
            'trends': trends,
            'anomalies': [a.to_dict() for a in anomalies[:5]],  # Top 5
            'merchant_analysis': merchant_analysis,
            'period': {
                'start': start_date.isoformat(), 
                'end': end_date.isoformat(),
                'days': days
            }
        }
    
    def get_analytics(self, start_date: datetime, end_date: datetime) -> dict:
        """Get detailed analytics for date range"""
        return {
            'summary': self.analytics.get_summary(start_date, end_date),
            'category_breakdown': self.analytics.get_category_breakdown(start_date, end_date),
            'merchant_analysis': self.analytics.get_merchant_analysis(start_date, end_date),
            'time_analysis': self.analytics.get_time_analysis(start_date, end_date)
        }
    
    def compare_periods(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> dict:
        """Compare two time periods"""
        return self.analytics.compare_periods(
            period1_start, period1_end,
            period2_start, period2_end
        )
    
    # ========================================================================
    # ML & Predictions
    # ========================================================================
    
    def predict_category(self, merchant: str, amount: float) -> dict:
        """
        Predict category using:
        1. Rule-based fallback (cold start)
        2. ML engine (once data exists)
        """

        # 1️⃣ Rule-based fallback
        rule_cat = rule_based_category(merchant)
        if rule_cat:
            return {
                'category': rule_cat,
                'confidence': 0.95
            }

        # 2️⃣ ML-based prediction
        try:
            category, confidence = self.ml_engine.predict_category(merchant, amount)
            return {
                'category': category.value,
                'confidence': confidence
            }
        except Exception:
            pass

        # 3️⃣ Final fallback
        return {
            'category': Category.OTHER_EXPENSE.value,
            'confidence': 0.0
        }

    
    def predict_spending(
        self, 
        category: Optional[Category] = None
    ) -> dict:
        """Predict next month's spending"""
        return self.ml_engine.predict_next_month_spending(category)
    
    def get_recurring_transactions(self) -> List[Dict]:
        """Get potentially recurring transactions"""
        return self.ml_engine.predict_recurring_transactions()
    
    def get_spending_insights(self) -> dict:
        """Get AI-powered spending insights"""
        unusual_patterns = self.ml_engine.detect_unusual_patterns()
        recurring = self.ml_engine.predict_recurring_transactions()
        
        return {
            'unusual_patterns': unusual_patterns,
            'recurring_transactions': recurring[:5],  # Top 5
            'generated_at': datetime.now().isoformat()
        }
    
    # ========================================================================
    # Budget Operations
    # ========================================================================
    
    def create_budget(
        self,
        category: Category,
        amount: float,
        period: str = "monthly"
    ) -> Budget:
        """Create a new budget"""
        budget = Budget(
            category=category,
            amount=amount,
            period=period
        )
        budget_id = self.budget_repo.create(budget)
        budget.id = budget_id
        return budget
    
    def get_all_budgets(self) -> List[Budget]:
        """Get all budgets"""
        return self.budget_repo.get_all()
    
    def update_budget(self, budget: Budget) -> bool:
        """Update budget"""
        return self.budget_repo.update(budget)
    
    def delete_budget(self, budget_id: int) -> bool:
        """Delete budget"""
        return self.budget_repo.delete(budget_id)
    
    def get_budget_status(self, days: int = 30) -> dict:
        """Get current budget status"""
        budgets = self.budget_repo.get_all()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        budget_dicts = [b.to_dict() for b in budgets]
        return self.analytics.get_budget_status(budget_dicts, start_date, end_date)
    
    def suggest_budgets(self, total_budget: float) -> Dict[str, float]:
        """Suggest budget allocation"""
        return self.ml_engine.suggest_budget_allocation(total_budget)
    
    # ========================================================================
    # Goal Operations
    # ========================================================================
    
    def create_goal(
        self,
        name: str,
        target_amount: float,
        deadline: Optional[datetime] = None,
        category: str = "savings"
    ) -> FinancialGoal:
        """Create a financial goal"""
        goal = FinancialGoal(
            name=name,
            target_amount=target_amount,
            deadline=deadline,
            category=category
        )
        goal_id = self.goal_repo.create(goal)
        goal.id = goal_id
        return goal
    
    def get_all_goals(self) -> List[FinancialGoal]:
        """Get all goals"""
        return self.goal_repo.get_all()
    
    def update_goal(self, goal: FinancialGoal) -> bool:
        """Update goal"""
        return self.goal_repo.update(goal)
    
    def delete_goal(self, goal_id: int) -> bool:
        """Delete goal"""
        return self.goal_repo.delete(goal_id)
    
    # ========================================================================
    # Import/Export
    # ========================================================================
    

    def generate_demo_data(self, n: int = 100):
        """Generate synthetic demo transactions for ML bootstrapping"""
        import random

        demo_data = [
            ("Starbucks", Category.DINING, -250),
            ("Uber", Category.TRANSPORT, -320),
            ("Amazon", Category.SHOPPING, -1500),
            ("Netflix", Category.ENTERTAINMENT, -499),
            ("Rent", Category.RENT, -15000),
            ("Salary", Category.SALARY, 60000),
            ("Zomato", Category.DINING, -450),
            ("Swiggy", Category.DINING, -380),
            ("Electricity Bill", Category.UTILITIES, -2200),
            ("Gym", Category.HEALTHCARE, -1200),
        ]

        for _ in range(n):
            merchant, category, amount = random.choice(demo_data)
            days_ago = random.randint(1, 180)

            self.add_transaction(
                date=datetime.now() - timedelta(days=days_ago),
                amount=amount,
                merchant=merchant,
                category=category,
                notes="Demo data"
            )

    def import_from_csv(self, csv_content: str) -> dict:
        """Import transactions from CSV content"""
        imported = 0
        failed = 0
        errors = []
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for row in reader:
                try:
                    # Parse date
                    date_str = row.get('date', row.get('Date', ''))
                    date = datetime.fromisoformat(date_str)
                    
                    # Parse amount
                    amount_str = row.get('amount', row.get('Amount', '0'))
                    amount = float(amount_str)
                    
                    # Get merchant
                    merchant = row.get('merchant', row.get('Merchant', 'Unknown'))
                    
                    # Get optional fields
                    notes = row.get('notes', row.get('Notes', ''))
                    category_str = row.get('category', row.get('Category', ''))
                    
                    # Try to map category
                    category = None
                    if category_str:
                        try:
                            category = Category(category_str)
                        except ValueError:
                            pass
                    
                    self.add_transaction(
                        date=date,
                        amount=amount,
                        merchant=merchant,
                        category=category,
                        notes=notes
                    )
                    imported += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Row error: {str(e)}")
        
        except Exception as e:
            errors.append(f"CSV parse error: {str(e)}")
        
        return {
            'imported': imported,
            'failed': failed,
            'errors': errors[:10]  # Limit error messages
        }
    
    def export_to_csv(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export transactions to CSV"""
        if start_date and end_date:
            transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        else:
            transactions = self.transaction_repo.get_all()
        
        output = io.StringIO()
        fieldnames = [
            'id', 'date', 'merchant', 'amount', 'category', 
            'transaction_type', 'notes', 'tags'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for t in transactions:
            writer.writerow({
                'id': t.id,
                'date': t.date.strftime('%Y-%m-%d'),
                'merchant': t.merchant,
                'amount': t.amount,
                'category': t.category.value,
                'transaction_type': t.transaction_type.value,
                'notes': t.notes,
                'tags': ','.join(t.tags)
            })
        
        return output.getvalue()
    
    # ========================================================================
    # Database Management
    # ========================================================================
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        return self.db.get_stats()
    
    def backup_database(self):
        """Create database backup"""
        return self.db.backup()
    
    def optimize_database(self):
        """Optimize database"""
        self.db.vacuum()