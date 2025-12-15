"""
Data models for the finance application
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TransactionType(Enum):
    """Transaction type enumeration"""
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class Category(Enum):
    """Category enumeration for transactions"""
    # Expense categories
    GROCERIES = "Groceries"
    DINING = "Dining & Restaurants"
    TRANSPORT = "Transportation"
    UTILITIES = "Utilities"
    RENT = "Rent/Mortgage"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    TRAVEL = "Travel"
    INSURANCE = "Insurance"
    OTHER_EXPENSE = "Other Expense"
    
    # Income categories
    SALARY = "Salary"
    FREELANCE = "Freelance"
    INVESTMENT = "Investment Income"
    OTHER_INCOME = "Other Income"


@dataclass
class Transaction:
    """Transaction data model"""
    id: Optional[int] = None
    date: datetime = field(default_factory=datetime.now)
    amount: float = 0.0
    merchant: str = ""
    category: Category = Category.OTHER_EXPENSE
    transaction_type: TransactionType = TransactionType.EXPENSE
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_recurring: bool = False
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'amount': self.amount,
            'merchant': self.merchant,
            'category': self.category.value,
            'transaction_type': self.transaction_type.value,
            'notes': self.notes,
            'tags': self.tags,
            'is_recurring': self.is_recurring,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Budget:
    """Budget data model"""
    id: Optional[int] = None
    category: Category = Category.OTHER_EXPENSE
    amount: float = 0.0
    period: str = "monthly"  # monthly, weekly, yearly
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    alert_threshold: float = 0.8  # Alert at 80% of budget
    
    def to_dict(self) -> dict:
        """Convert budget to dictionary"""
        return {
            'id': self.id,
            'category': self.category.value,
            'amount': self.amount,
            'period': self.period,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'alert_threshold': self.alert_threshold
        }


@dataclass
class FinancialGoal:
    """Financial goal data model"""
    id: Optional[int] = None
    name: str = ""
    target_amount: float = 0.0
    current_amount: float = 0.0
    deadline: Optional[datetime] = None
    category: str = "savings"
    priority: int = 1
    
    def to_dict(self) -> dict:
        """Convert goal to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'category': self.category,
            'priority': self.priority,
            'progress': (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        }