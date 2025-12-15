"""
Machine Learning engine for predictions and classifications
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List

from .repositories import TransactionRepository
from .models import Transaction, Category, TransactionType


class MLEngine:
    """Machine Learning engine for predictions and classifications"""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo
        self.category_keywords = self._build_keyword_map()
        self.merchant_history = {}
    
    def _build_keyword_map(self) -> Dict[Category, List[str]]:
        """Build keyword to category mapping"""
        return {
            Category.GROCERIES: [
                'grocery', 'supermarket', 'walmart', 'target', 'whole foods',
                'trader joe', 'safeway', 'kroger', 'albertsons', 'market'
            ],
            Category.DINING: [
                'restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald',
                'chipotle', 'pizza', 'subway', 'taco bell', 'burger',
                'kitchen', 'grill', 'diner', 'bistro'
            ],
            Category.TRANSPORT: [
                'uber', 'lyft', 'gas', 'fuel', 'parking', 'transit',
                'metro', 'taxi', 'shell', 'chevron', 'exxon', 'bp'
            ],
            Category.UTILITIES: [
                'electric', 'water', 'internet', 'phone', 'gas bill',
                'utility', 'comcast', 'verizon', 'att', 'sprint'
            ],
            Category.RENT: [
                'rent', 'mortgage', 'lease', 'property', 'landlord'
            ],
            Category.ENTERTAINMENT: [
                'netflix', 'spotify', 'movie', 'theater', 'concert',
                'game', 'steam', 'xbox', 'playstation', 'hulu',
                'disney', 'amazon prime', 'apple music'
            ],
            Category.SHOPPING: [
                'amazon', 'ebay', 'mall', 'store', 'shop', 'clothing',
                'fashion', 'retail', 'bestbuy', 'macy'
            ],
            Category.HEALTHCARE: [
                'pharmacy', 'doctor', 'hospital', 'medical', 'cvs',
                'walgreens', 'health', 'clinic', 'dental'
            ],
            Category.EDUCATION: [
                'school', 'university', 'college', 'tuition', 'course',
                'textbook', 'udemy', 'coursera'
            ],
            Category.INSURANCE: [
                'insurance', 'policy', 'premium', 'geico', 'state farm'
            ],
            Category.SALARY: [
                'salary', 'payroll', 'paycheck', 'wages', 'income',
                'direct deposit'
            ],
            Category.FREELANCE: [
                'freelance', 'contract', 'consulting', 'commission',
                'upwork', 'fiverr'
            ]
        }
    
    def predict_category(
        self, 
        merchant: str, 
        amount: float
    ) -> Tuple[Category, float]:
        """Predict transaction category based on merchant name and amount"""
        merchant_lower = merchant.lower()
        
        # First, check merchant history
        if merchant in self.merchant_history:
            return self.merchant_history[merchant], 0.95
        
        # Check keyword matching
        scores = Counter()
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in merchant_lower:
                    scores[category] += 1
        
        if scores:
            best_category = scores.most_common(1)[0][0]
            # Confidence based on number of keyword matches
            confidence = min(scores[best_category] / 3, 1.0)
            return best_category, confidence
        
        # Default categorization based on amount
        if amount > 0:
            return Category.OTHER_INCOME, 0.3
        else:
            return Category.OTHER_EXPENSE, 0.3
    
    def train_from_history(self) -> dict:
        """Train model from historical transactions"""
        transactions = self.transaction_repo.get_all()
        
        # Build merchant -> category mapping
        merchant_category_map = defaultdict(list)
        for t in transactions:
            merchant_category_map[t.merchant].append(t.category)
        
        # Find most common category for each merchant
        self.merchant_history = {}
        for merchant, categories in merchant_category_map.items():
            most_common = Counter(categories).most_common(1)[0][0]
            self.merchant_history[merchant] = most_common
        
        return {
            'merchant_map': {k: v.value for k, v in self.merchant_history.items()},
            'training_samples': len(transactions),
            'unique_merchants': len(self.merchant_history)
        }
    
    def predict_next_month_spending(
        self, 
        category: Optional[Category] = None
    ) -> dict:
        """Predict next month's spending"""
        # Get last 3 months data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        
        if category:
            transactions = [t for t in transactions if t.category == category]
        
        expenses = [
            abs(t.amount) for t in transactions 
            if t.transaction_type == TransactionType.EXPENSE
        ]
        
        if not expenses:
            return {
                'predicted_amount': 0, 
                'confidence': 0,
                'method': 'no_data'
            }
        
        # Simple moving average prediction
        avg_monthly = sum(expenses) / 3
        
        # Calculate confidence based on consistency
        monthly_totals = []
        for month_offset in range(3):
            month_start = end_date - timedelta(days=(month_offset + 1) * 30)
            month_end = end_date - timedelta(days=month_offset * 30)
            month_trans = [
                t for t in transactions 
                if month_start <= t.date <= month_end
            ]
            monthly_total = sum(abs(t.amount) for t in month_trans)
            monthly_totals.append(monthly_total)
        
        # Lower variance = higher confidence
        if monthly_totals:
            variance = sum((x - avg_monthly) ** 2 for x in monthly_totals) / len(monthly_totals)
            std_dev = variance ** 0.5
            confidence = max(0.3, min(0.9, 1 - (std_dev / avg_monthly) if avg_monthly > 0 else 0.3))
        else:
            confidence = 0.5
        
        return {
            'predicted_amount': avg_monthly,
            'confidence': confidence,
            'historical_average': avg_monthly,
            'min': min(expenses),
            'max': max(expenses),
            'std_dev': std_dev if monthly_totals else 0,
            'monthly_breakdown': monthly_totals,
            'method': 'moving_average'
        }
    
    def predict_recurring_transactions(self) -> List[Dict]:
        """Identify potentially recurring transactions"""
        transactions = self.transaction_repo.get_all()
        
        # Group by merchant and amount (with some tolerance)
        recurring_candidates = defaultdict(list)
        
        for t in transactions:
            if t.transaction_type == TransactionType.EXPENSE:
                # Round amount to nearest dollar for grouping
                rounded_amount = round(abs(t.amount))
                key = (t.merchant, rounded_amount)
                recurring_candidates[key].append(t)
        
        # Find patterns (at least 3 occurrences)
        recurring_patterns = []
        for (merchant, amount), trans_list in recurring_candidates.items():
            if len(trans_list) >= 3:
                # Calculate average interval
                sorted_trans = sorted(trans_list, key=lambda x: x.date)
                intervals = []
                for i in range(1, len(sorted_trans)):
                    days = (sorted_trans[i].date - sorted_trans[i-1].date).days
                    intervals.append(days)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    
                    # Check if intervals are consistent (within 20%)
                    is_consistent = all(
                        abs(interval - avg_interval) / avg_interval < 0.2
                        for interval in intervals
                    )
                    
                    if is_consistent:
                        last_transaction = sorted_trans[-1]
                        next_expected = last_transaction.date + timedelta(days=avg_interval)
                        
                        recurring_patterns.append({
                            'merchant': merchant,
                            'amount': amount,
                            'frequency_days': round(avg_interval),
                            'occurrences': len(trans_list),
                            'last_date': last_transaction.date.isoformat(),
                            'next_expected': next_expected.isoformat(),
                            'confidence': min(len(trans_list) / 10, 0.95)
                        })
        
        return sorted(recurring_patterns, key=lambda x: x['confidence'], reverse=True)
    
    def suggest_budget_allocation(
        self, 
        total_budget: float
    ) -> Dict[str, float]:
        """Suggest budget allocation based on spending history"""
        # Get last 3 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        
        # Calculate average monthly spending by category
        category_spending = defaultdict(float)
        for t in transactions:
            if t.transaction_type == TransactionType.EXPENSE:
                category_spending[t.category.value] += abs(t.amount)
        
        # Average over 3 months
        for category in category_spending:
            category_spending[category] /= 3
        
        total_spending = sum(category_spending.values())
        
        # Calculate proportional allocation
        suggested_budget = {}
        if total_spending > 0:
            for category, amount in category_spending.items():
                proportion = amount / total_spending
                suggested_budget[category] = round(total_budget * proportion, 2)
        
        return suggested_budget
    
    def detect_unusual_patterns(self) -> List[Dict]:
        """Detect unusual spending patterns"""
        patterns = []
        
        # Get recent transactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        recent_trans = self.transaction_repo.get_by_date_range(start_date, end_date)
        
        # Check for sudden increase in category spending
        current_spending = defaultdict(float)
        for t in recent_trans:
            if t.transaction_type == TransactionType.EXPENSE:
                current_spending[t.category.value] += abs(t.amount)
        
        # Compare with previous month
        prev_start = start_date - timedelta(days=30)
        prev_trans = self.transaction_repo.get_by_date_range(prev_start, start_date)
        prev_spending = defaultdict(float)
        for t in prev_trans:
            if t.transaction_type == TransactionType.EXPENSE:
                prev_spending[t.category.value] += abs(t.amount)
        
        # Find significant increases
        for category in current_spending:
            if prev_spending[category] > 0:
                increase_pct = (
                    (current_spending[category] - prev_spending[category]) 
                    / prev_spending[category] * 100
                )
                if increase_pct > 50:  # 50% increase
                    patterns.append({
                        'type': 'category_spike',
                        'category': category,
                        'increase_percentage': round(increase_pct, 2),
                        'previous_amount': prev_spending[category],
                        'current_amount': current_spending[category],
                        'severity': 'high' if increase_pct > 100 else 'medium'
                    })
        
        return patterns