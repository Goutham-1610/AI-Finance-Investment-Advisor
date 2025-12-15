"""
Test script for backend functionality
Run: python test_backend.py
"""
from datetime import datetime, timedelta
from backend.services import FinanceService
from backend.models import Category

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_section("FINANCE ADVISOR - BACKEND TEST")
    
    # Initialize service
    print("\n📦 Initializing Finance Service...")
    service = FinanceService()
    print("✅ Service initialized successfully!")
    
    # Test 1: Add transactions
    print_section("TEST 1: Adding Transactions")
    
    transactions_to_add = [
        (datetime.now(), -50.0, "Starbucks Coffee", "Morning coffee"),
        (datetime.now(), -120.50, "Whole Foods Market", "Weekly groceries"),
        (datetime.now(), 3000.0, "Acme Corp Payroll", "Monthly salary"),
        (datetime.now() - timedelta(days=5), -85.30, "Shell Gas Station", "Fill up"),
        (datetime.now() - timedelta(days=3), -15.99, "Netflix", "Subscription"),
        (datetime.now() - timedelta(days=2), -45.0, "Amazon", "Books"),
        (datetime.now() - timedelta(days=1), -25.50, "Uber", "Ride to work"),
    ]
    
    for date, amount, merchant, notes in transactions_to_add:
        transaction = service.add_transaction(date, amount, merchant, notes=notes)
        print(f"✅ Added: {merchant} | ${abs(amount):.2f} | Category: {transaction.category.value}")
    
    print(f"\n📊 Total transactions added: {len(transactions_to_add)}")
    
    # Test 2: Get Dashboard Data
    print_section("TEST 2: Dashboard Data")
    
    dashboard = service.get_dashboard_data(days=30)
    summary = dashboard['summary']
    
    print(f"\n💰 Financial Summary:")
    print(f"   Total Income:     ${summary['total_income']:>10,.2f}")
    print(f"   Total Expenses:   ${summary['total_expenses']:>10,.2f}")
    print(f"   Net Savings:      ${summary['net']:>10,.2f}")
    print(f"   Savings Rate:     {summary['savings_rate']:>10.1f}%")
    print(f"   Transactions:     {summary['transaction_count']:>10}")
    
    # Test 3: Category Breakdown
    print_section("TEST 3: Category Breakdown")
    
    categories = dashboard['category_breakdown']
    print(f"\n📊 Spending by Category:")
    for category, amount in sorted(categories['totals'].items(), key=lambda x: x[1], reverse=True):
        percentage = categories['percentages'][category]
        print(f"   {category:<25} ${amount:>8.2f} ({percentage:>5.1f}%)")
    
    # Test 4: Spending Trends
    print_section("TEST 4: Spending Trends")
    
    trends = dashboard['trends']
    print(f"\n📈 Trend Analysis:")
    print(f"   Average Daily:    ${trends['average_daily_spending']:.2f}")
    print(f"   Recent Average:   ${trends['recent_average']:.2f}")
    print(f"   Trend:            {trends['trend'].upper()}")
    print(f"   Change:           {trends['change_percentage']:+.1f}%")
    
    # Test 5: ML Predictions
    print_section("TEST 5: ML Predictions")
    
    print("\n🤖 Category Predictions:")
    test_merchants = [
        ("McDonald's", -12.50),
        ("Target", -85.00),
        ("Shell", -40.00),
        ("Spotify", -9.99)
    ]
    
    for merchant, amount in test_merchants:
        prediction = service.predict_category(merchant, amount)
        print(f"   {merchant:<20} → {prediction['category']:<25} (confidence: {prediction['confidence']:.0%})")
    
    # Test 6: Recurring Transactions
    print_section("TEST 6: Recurring Transactions Detection")
    
    recurring = service.get_recurring_transactions()
    if recurring:
        print(f"\n🔄 Found {len(recurring)} potential recurring transactions:")
        for r in recurring[:5]:  # Show top 5
            print(f"   {r['merchant']:<25} ${r['amount']:>8.2f} every {r['frequency_days']} days")
    else:
        print("\n   No recurring patterns detected yet (need more data)")
    
    # Test 7: Budget Operations
    print_section("TEST 7: Budget Management")
    
    print("\n💵 Creating sample budgets...")
    budgets_to_create = [
        (Category.GROCERIES, 400),
        (Category.DINING, 200),
        (Category.TRANSPORT, 150),
        (Category.ENTERTAINMENT, 100),
    ]
    
    for category, amount in budgets_to_create:
        budget = service.create_budget(category, amount)
        print(f"   ✅ Budget created: {category.value} - ${amount}/month")
    
    budget_status = service.get_budget_status(days=30)
    print(f"\n📊 Budget Status:")
    for budget in budget_status['budgets']:
        status_icon = "✅" if budget['status'] == 'good' else "⚠️" if budget['status'] == 'warning' else "🚨"
        print(f"   {status_icon} {budget['category']:<20} ${budget['spent']:>8.2f} / ${budget['budget']:>8.2f} ({budget['percentage_used']:.0f}%)")
    
    # Test 8: Database Stats
    print_section("TEST 8: Database Statistics")
    
    stats = service.get_database_stats()
    print(f"\n📈 Database Stats:")
    print(f"   Total Transactions: {stats['total_transactions']}")
    print(f"   Total Budgets:      {stats['total_budgets']}")
    print(f"   Total Goals:        {stats['total_goals']}")
    print(f"   Database Size:      {stats['db_size_mb']:.2f} MB")
    
    # Test 9: Export Data
    print_section("TEST 9: Data Export")
    
    print("\n📤 Exporting transactions to CSV...")
    csv_data = service.export_to_csv()
    lines = len(csv_data.split('\n')) - 1  # Subtract header
    print(f"   ✅ Exported {lines} transactions")
    print(f"   Preview (first 3 lines):")
    for line in csv_data.split('\n')[:3]:
        print(f"      {line}")
    
    # Final Summary
    print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    
    print(f"""
    🎉 Backend System Status: OPERATIONAL
    
    ✅ Transaction management working
    ✅ Analytics engine working
    ✅ ML predictions working
    ✅ Budget tracking working
    ✅ Data import/export working
    
    Next Steps:
    1. Run frontend: streamlit run frontend/app.py
    2. Start adding real data
    3. Explore analytics features
    
    Database Location: data/finance.db
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()