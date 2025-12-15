"""
Analytics engine for financial insights and calculations
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .repositories import TransactionRepository
from .models import Transaction, TransactionType, Category


class AnalyticsEngine:
    """Analytics and reporting engine"""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo
    
    def get_summary(self, start_date: datetime, end_date: datetime) -> dict:
        """Get financial summary for date range"""
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        
        total_income = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.INCOME
        )
        
        total_expenses = sum(
            abs(t.amount) for t in transactions 
            if t.transaction_type == TransactionType.EXPENSE
        )
        
        net = total_income - total_expenses
        
        # Calculate average transaction
        expense_transactions = [
            t for t in transactions 
            if t.transaction_type == TransactionType.EXPENSE
        ]
        avg_transaction = (
            total_expenses / len(expense_transactions) 
            if expense_transactions else 0
        )
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net': net,
            'transaction_count': len(transactions),
            'expense_count': len(expense_transactions),
            'income_count': len(transactions) - len(expense_transactions),
            'average_transaction': avg_transaction,
            'savings_rate': (net / total_income * 100) if total_income > 0 else 0
        }
    
    def get_category_breakdown(self, start_date: datetime, end_date: datetime) -> dict:
        """Get spending breakdown by category"""
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        
        category_totals = defaultdict(float)
        category_counts = defaultdict(int)
        
        for t in expenses:
            category_totals[t.category.value] += abs(t.amount)
            category_counts[t.category.value] += 1
        
        total = sum(category_totals.values())
        
        return {
            'totals': dict(category_totals),
            'counts': dict(category_counts),
            'percentages': {
                k: (v/total*100) if total > 0 else 0 
                for k, v in category_totals.items()
            },
            'top_category': (
                max(category_totals.items(), key=lambda x: x[1])[0] 
                if category_totals else None
            ),
            'total_spent': total
        }
    
    def detect_spending_trends(self, days: int = 30) -> dict:
        """Detect spending trends"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        
        # Group by day
        daily_spending = defaultdict(float)
        for t in transactions:
            if t.transaction_type == TransactionType.EXPENSE:
                day = t.date.date()
                daily_spending[day] += abs(t.amount)
        
        # Calculate trend
        values = list(daily_spending.values())
        if len(values) > 7:
            avg_spending = sum(values) / len(values)
            recent_avg = sum(values[-7:]) / min(7, len(values))
            
            # Calculate percentage change
            change_pct = ((recent_avg - avg_spending) / avg_spending * 100) if avg_spending > 0 else 0
            
            if abs(change_pct) < 5:
                trend = "stable"
            elif recent_avg > avg_spending:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            avg_spending = values[0] if values else 0
            recent_avg = avg_spending
            trend = "stable"
            change_pct = 0
        
        return {
            'average_daily_spending': avg_spending,
            'recent_average': recent_avg,
            'trend': trend,
            'change_percentage': change_pct,
            'daily_data': {str(k): v for k, v in daily_spending.items()}
        }
    
    def find_anomalies(self, threshold: float = 2.0) -> List[Transaction]:
        """Find unusual transactions (spending anomalies)"""
        transactions = self.transaction_repo.get_all()
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        
        if len(expenses) < 10:
            return []
        
        amounts = [abs(t.amount) for t in expenses]
        mean = sum(amounts) / len(amounts)
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        std_dev = variance ** 0.5
        
        anomalies = []
        for t in expenses:
            if abs(t.amount) > mean + (threshold * std_dev):
                anomalies.append(t)
        
        return sorted(anomalies, key=lambda x: abs(x.amount), reverse=True)
    
    def get_merchant_analysis(self, start_date: datetime, end_date: datetime) -> dict:
        """Analyze spending by merchant"""
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        
        merchant_data = defaultdict(lambda: {'total': 0, 'count': 0, 'transactions': []})
        
        for t in expenses:
            merchant_data[t.merchant]['total'] += abs(t.amount)
            merchant_data[t.merchant]['count'] += 1
            merchant_data[t.merchant]['transactions'].append(t.to_dict())
        
        # Calculate averages
        for merchant in merchant_data:
            merchant_data[merchant]['average'] = (
                merchant_data[merchant]['total'] / merchant_data[merchant]['count']
            )
        
        # Sort by total spending
        sorted_merchants = sorted(
            merchant_data.items(), 
            key=lambda x: x[1]['total'], 
            reverse=True
        )
        
        return {
            'merchant_details': dict(sorted_merchants[:10]),  # Top 10
            'total_merchants': len(merchant_data),
            'top_merchant': sorted_merchants[0][0] if sorted_merchants else None
        }
    
    def get_time_analysis(self, start_date: datetime, end_date: datetime) -> dict:
        """Analyze spending patterns by time"""
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        
        # By day of week
        day_of_week_spending = defaultdict(float)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for t in expenses:
            day = t.date.weekday()
            day_of_week_spending[day_names[day]] += abs(t.amount)
        
        # By week
        weekly_spending = defaultdict(float)
        for t in expenses:
            week = t.date.isocalendar()[1]  # ISO week number
            weekly_spending[f"Week {week}"] += abs(t.amount)
        
        return {
            'by_day_of_week': dict(day_of_week_spending),
            'by_week': dict(weekly_spending),
            'highest_spending_day': (
                max(day_of_week_spending.items(), key=lambda x: x[1])[0]
                if day_of_week_spending else None
            )
        }
    
    def compare_periods(
        self, 
        period1_start: datetime, 
        period1_end: datetime,
        period2_start: datetime, 
        period2_end: datetime
    ) -> dict:
        """Compare two time periods"""
        summary1 = self.get_summary(period1_start, period1_end)
        summary2 = self.get_summary(period2_start, period2_end)
        
        def calculate_change(old, new):
            if old == 0:
                return 0
            return ((new - old) / old) * 100
        
        return {
            'period1': summary1,
            'period2': summary2,
            'changes': {
                'income_change': calculate_change(
                    summary1['total_income'], 
                    summary2['total_income']
                ),
                'expense_change': calculate_change(
                    summary1['total_expenses'], 
                    summary2['total_expenses']
                ),
                'net_change': calculate_change(
                    summary1['net'], 
                    summary2['net']
                )
            }
        }
    
    def get_budget_status(
        self, 
        budgets: List[Dict], 
        start_date: datetime, 
        end_date: datetime
    ) -> dict:
        """Get status of budgets"""
        category_breakdown = self.get_category_breakdown(start_date, end_date)
        
        budget_status = []
        for budget in budgets:
            category = budget['category']
            spent = category_breakdown['totals'].get(category, 0)
            budget_amount = budget['amount']
            
            percentage_used = (spent / budget_amount * 100) if budget_amount > 0 else 0
            remaining = budget_amount - spent
            
            status = 'good'
            if percentage_used >= 100:
                status = 'exceeded'
            elif percentage_used >= budget.get('alert_threshold', 0.8) * 100:
                status = 'warning'
            
            budget_status.append({
                'category': category,
                'budget': budget_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage_used': percentage_used,
                'status': status
            })
        
        return {
            'budgets': budget_status,
            'total_budgeted': sum(b['amount'] for b in budgets),
            'total_spent': sum(bs['spent'] for bs in budget_status)
        }