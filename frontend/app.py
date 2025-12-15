"""
Personal Finance Advisor - Streamlit Frontend
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for backend imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.services import FinanceService
from backend.models import Category, TransactionType
from backend.utils import format_currency, format_percentage
from backend.utils import format_date

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Personal Finance Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {
        color: #28a745;
    }
    .negative {
        color: #dc3545;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 24px;
        padding-right: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZE SERVICE
# ============================================================================

@st.cache_resource
def get_service():
    """Initialize and cache the finance service"""
    return FinanceService()

service = get_service()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("💰 Finance Advisor")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "➕ Add Transaction",
            "📝 Transactions",
            "📈 Analytics",
            "💰 Budgets",
            "🎯 Goals",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    try:
        stats = service.get_database_stats()
        dashboard_data = service.get_dashboard_data(days=30)
        
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Transactions", stats['total_transactions'])
        st.metric("This Month Net", format_currency(dashboard_data['summary']['net']))
        st.metric(
            "Savings Rate", 
            format_percentage(dashboard_data['summary']['savings_rate'])
        )
    except Exception as e:
        st.warning("Loading stats...")
    
    st.markdown("---")
    st.caption("Last updated: Just now")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def display_transaction_form(transaction=None):
    """Display transaction form for add/edit"""
    is_edit = transaction is not None
    
    with st.form("transaction_form", clear_on_submit=not is_edit):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input(
                "Date",
                value=transaction.date if is_edit else datetime.now()
            )
            merchant = st.text_input(
                "Merchant/Description",
                value=transaction.merchant if is_edit else "",
                placeholder="e.g., Starbucks, Salary, etc."
            )
        
        with col2:
            amount = st.number_input(
                "Amount ($)",
                min_value=0.01,
                value=abs(transaction.amount) if is_edit else 0.01,
                step=0.01,
                format="%.2f"
            )           

            trans_type = st.selectbox(
                "Type",
                ["Expense", "Income"],
                index=0 if not is_edit else (1 if transaction.transaction_type == TransactionType.INCOME else 0)
            )
        
        # Category selection
        if trans_type == "Expense":
            categories = [
                "Groceries", "Dining & Restaurants", "Transportation",
                "Utilities", "Rent/Mortgage", "Entertainment", "Shopping",
                "Healthcare", "Education", "Travel", "Insurance", "Other Expense"
            ]
        else:
            categories = ["Salary", "Freelance", "Investment Income", "Other Income"]
        
        category = st.selectbox(
            "Category",
            categories,
            index=categories.index(transaction.category.value) if is_edit and transaction.category.value in categories else 0
        )
        
        notes = st.text_area(
            "Notes (Optional)",
            value=transaction.notes if is_edit else "",
            placeholder="Add any additional details..."
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button(
                "💾 Update Transaction" if is_edit else "💾 Save Transaction",
                use_container_width=True
            )
        
        with col2:
            if not is_edit:
                predict = st.form_submit_button(
                    "🤖 Auto-Predict",
                    use_container_width=True
                )
            else:
                predict = False
        
        if submitted:
            try:
                final_amount = amount if trans_type == "Income" else -amount
                category_enum = Category(category)
                
                if is_edit:
                    transaction.date = datetime.combine(date, datetime.min.time())
                    transaction.amount = final_amount
                    transaction.merchant = merchant
                    transaction.category = category_enum
                    transaction.transaction_type = TransactionType.INCOME if trans_type == "Income" else TransactionType.EXPENSE
                    transaction.notes = notes
                    
                    service.update_transaction(transaction)
                    st.success("✅ Transaction updated successfully!")
                else:
                    service.add_transaction(
                        date=datetime.combine(date, datetime.min.time()),
                        amount=final_amount,
                        merchant=merchant,
                        category=category_enum,
                        notes=notes
                    )
                    st.success("✅ Transaction added successfully!")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if predict:
            prediction = service.predict_category(merchant, amount)
            st.info(f"""
            🤖 **AI Prediction**
            
            Based on "{merchant}", I predict:
            - **Category**: {prediction['category']}
            - **Confidence**: {prediction['confidence']:.0%}
            """)

# ============================================================================
# PAGE 1
# ============================================================================

if page == "📊 Dashboard":
    st.markdown("<h1 class='main-header'>Financial Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Your complete financial overview</p>", unsafe_allow_html=True)
    
    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Year", "Custom"],
            index=1
        )
    
    if date_range == "Last 7 Days":
        days = 7
    elif date_range == "Last 30 Days":
        days = 30
    elif date_range == "Last 90 Days":
        days = 90
    elif date_range == "This Year":
        days = 365
    else:
        with col2:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col3:
            end_date = st.date_input("End Date", datetime.now())
        days = (end_date - start_date).days
    
    # Get dashboard data
    try:
        dashboard = service.get_dashboard_data(days=days)
        summary = dashboard['summary']
        categories = dashboard['category_breakdown']
        trends = dashboard['trends']
        
        st.markdown("---")
        
        # Key Metrics
        st.subheader("📌 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Income",
                format_currency(summary['total_income']),
                delta=f"{summary['income_count']} transactions"
            )
        
        with col2:
            st.metric(
                "Total Expenses",
                format_currency(summary['total_expenses']),
                delta=f"{summary['expense_count']} transactions",
                delta_color="inverse"
            )
        
        with col3:
            delta_color = "normal" if summary['net'] >= 0 else "inverse"
            st.metric(
                "Net Savings",
                format_currency(summary['net']),
                delta=f"{summary['savings_rate']:.1f}% rate",
                delta_color=delta_color
            )
        
        with col4:
            st.metric(
                "Avg Transaction",
                format_currency(summary['average_transaction']),
                delta=f"{summary['transaction_count']} total"
            )
        
        st.markdown("---")
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💸 Spending by Category")
            if categories['totals']:
                fig = px.pie(
                    values=list(categories['totals'].values()),
                    names=list(categories['totals'].keys()),
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data available for this period")
        
        with col2:
            st.subheader("📊 Category Breakdown")
            if categories['totals']:
                category_df = pd.DataFrame({
                    'Category': list(categories['totals'].keys()),
                    'Amount': list(categories['totals'].values()),
                    'Count': [categories['counts'].get(cat, 0) for cat in categories['totals'].keys()]
                }).sort_values('Amount', ascending=True)
                
                fig = px.bar(
                    category_df,
                    x='Amount',
                    y='Category',
                    orientation='h',
                    text='Amount',
                    color='Amount',
                    color_continuous_scale='Reds',
                    hover_data={'Count': True}
                )
                fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        st.markdown("---")
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Daily Spending Trend")
            if trends['daily_data']:
                daily_df = pd.DataFrame(
                    [(datetime.fromisoformat(k), v) for k, v in trends['daily_data'].items()],
                    columns=['Date', 'Amount']
                ).sort_values('Date')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_df['Date'],
                    y=daily_df['Amount'],
                    mode='lines+markers',
                    name='Daily Spending',
                    line=dict(color='#ff6b6b', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(255, 107, 107, 0.2)'
                ))
                
                # Add average line
                avg = trends['average_daily_spending']
                fig.add_hline(
                    y=avg,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"Avg: ${avg:.2f}"
                )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No daily data available")
        
        with col2:
            st.subheader("🎯 Insights & Recommendations")
            
            # Trend insight
            trend = trends['trend']
            trend_icon = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
            trend_color = "🔴" if trend == "increasing" else "🟢" if trend == "decreasing" else "🟡"
            
            st.info(f"""
            **{trend_icon} Spending Trend: {trend.title()}** {trend_color}
            
            - Average daily: ${trends['average_daily_spending']:.2f}
            - Recent average: ${trends['recent_average']:.2f}
            - Change: {trends['change_percentage']:+.1f}%
            """)
            
            # Top category
            if categories['top_category']:
                top_cat = categories['top_category']
                top_amount = categories['totals'][top_cat]
                top_pct = categories['percentages'][top_cat]
                
                st.warning(f"""
                **🔍 Top Spending Category**
                
                **{top_cat}**: ${top_amount:.2f}
                
                This is {top_pct:.1f}% of your total expenses.
                """)
            
            # Savings rate feedback
            savings_rate = summary['savings_rate']
            if savings_rate > 30:
                st.success(f"""
                **✅ Excellent Savings!**
                
                You're saving {savings_rate:.1f}% of your income.
                Keep up the great work!
                """)
            elif savings_rate > 15:
                st.info(f"""
                **👍 Good Savings**
                
                You're saving {savings_rate:.1f}% of your income.
                Consider increasing to 30%+
                """)
            else:
                st.error(f"""
                **⚠️ Low Savings Rate**
                
                You're only saving {savings_rate:.1f}%.
                Review your expenses to save more.
                """)
        
        # Anomalies
        if dashboard.get('anomalies'):
            st.markdown("---")
            st.subheader("⚠️ Unusual Transactions Detected")
            
            anomaly_df = pd.DataFrame([
                {
                    'Date': a['date'][:10],
                    'Merchant': a['merchant'],
                    'Amount': format_currency(abs(a['amount'])),
                    'Category': a['category']
                }
                for a in dashboard['anomalies']
            ])
            
            st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
            st.caption("💡 These transactions are significantly higher than your usual spending patterns")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# ============================================================================
# PAGE 2
# ============================================================================

elif page == "➕ Add Transaction":
    st.markdown("<h1 class='main-header'>Add Transaction</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Record a new financial transaction</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Transaction Details")
        display_transaction_form()
    
    with col2:
        st.subheader("Recent Transactions")
        try:
            recent = service.get_all_transactions(limit=5)
            if recent:
                for t in recent:
                    with st.container():
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.markdown(f"**{t.merchant}**")
                            st.caption(f"{t.date.strftime('%b %d, %Y')} • {t.category.value}")
                        with col_b:
                            amount_color = "green" if t.amount > 0 else "red"
                            st.markdown(f"<p style='color:{amount_color};font-weight:bold;text-align:right'>{format_currency(t.amount)}</p>", unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.info("No transactions yet")
        except Exception as e:
            st.error(f"Error loading recent transactions: {str(e)}")
        
        st.markdown("### 📤 Bulk Import")
        st.caption("Import transactions from CSV file")
        
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file:
            csv_content = uploaded_file.getvalue().decode('utf-8')
            if st.button("📥 Process CSV", use_container_width=True):
                try:
                    result = service.import_from_csv(csv_content)
                    if result['imported'] > 0:
                        st.success(f"✅ Imported {result['imported']} transactions!")
                    if result['failed'] > 0:
                        st.warning(f"⚠️ Failed to import {result['failed']} rows")
                        if result['errors']:
                            with st.expander("View Errors"):
                                for error in result['errors']:
                                    st.text(error)
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

# ============================================================================
# PAGE 3
# ============================================================================

elif page == "📝 Transactions":
    st.markdown("<h1 class='main-header'>Transaction History</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>View and manage all your transactions</p>", unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_type = st.selectbox("Type", ["All", "Expense", "Income"])
    
    with col2:
        all_categories = [c.value for c in Category]
        filter_category = st.selectbox("Category", ["All"] + all_categories)
    
    with col3:
        search_query = st.text_input("🔍 Search", placeholder="Merchant or notes...")
    
    with col4:
        limit = st.selectbox("Show", [25, 50, 100, "All"])
    
    st.markdown("---")
    
    try:
        # Get transactions
        if search_query:
            transactions = service.search_transactions(search_query)
        else:
            transactions = service.get_all_transactions(limit=None if limit == "All" else int(limit))
        
        # Apply filters
        if filter_type != "All":
            trans_type = TransactionType.INCOME if filter_type == "Income" else TransactionType.EXPENSE
            transactions = [t for t in transactions if t.transaction_type == trans_type]
        
        if filter_category != "All":
            transactions = [t for t in transactions if t.category.value == filter_category]
        
        # Display stats
        if transactions:
            total_amount = sum(abs(t.amount) for t in transactions if t.transaction_type == TransactionType.EXPENSE)
            avg_amount = total_amount / len([t for t in transactions if t.transaction_type == TransactionType.EXPENSE]) if transactions else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Transactions", len(transactions))
            with col2:
                st.metric("Total Spent", format_currency(total_amount))
            with col3:
                st.metric("Average", format_currency(avg_amount))
            
            st.markdown("---")
            
            # Transactions table
            df = pd.DataFrame([
                {
                    'Date': t.date.strftime('%Y-%m-%d'),
                    'Merchant': t.merchant,
                    'Amount': t.amount,
                    'Category': t.category.value,
                    'Type': t.transaction_type.value,
                    'Notes': t.notes[:50] + '...' if len(t.notes) > 50 else t.notes,
                    'ID': t.id
                }
                for t in transactions
            ])
            
            # Format amount column with color
            def color_amount(val):
                color = 'green' if val > 0 else 'red'
                return f'color: {color}'
            
            st.dataframe(
                df.style.applymap(color_amount, subset=['Amount']),
                use_container_width=True,
                height=400
            )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Export to CSV", use_container_width=True):
                    csv_data = service.export_to_csv()
                    st.download_button(
                        "Download CSV",
                        csv_data,
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            # Transaction details in expander
            with st.expander("📋 View Transaction Details"):
                transaction_id = st.number_input("Enter Transaction ID", min_value=1, step=1)
                if st.button("Load Transaction"):
                    transaction = service.get_transaction_by_id(transaction_id)
                    if transaction:
                        st.json(transaction.to_dict())
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✏️ Edit Transaction", use_container_width=True):
                                st.session_state.edit_transaction = transaction
                                st.rerun()
                        
                        with col_b:
                            if st.button("🗑️ Delete Transaction", use_container_width=True, type="secondary"):
                                if service.delete_transaction(transaction_id):
                                    st.success("Transaction deleted!")
                                    st.rerun()
                    else:
                        st.error("Transaction not found")
        else:
            st.info("No transactions found matching your filters")
    
    except Exception as e:
        st.error(f"Error loading transactions: {str(e)}")

# ============================================================================
# PAGE 4
# ===========================================================================

elif page == "📈 Analytics":
    st.markdown("<h1 class='main-header'>Advanced Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Deep insights into your financial data</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎯 Predictions", "⚠️ Anomalies", "🔄 Recurring"])
    
    with tab1:
        st.subheader("Financial Insights")
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("To", datetime.now())
        
        try:
            analytics = service.get_analytics(
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.min.time())
            )
            
            # Merchant analysis
            st.markdown("### 🏪 Top Merchants")
            merchant_data = analytics['merchant_analysis']['merchant_details']
            if merchant_data:
                merchant_df = pd.DataFrame([
                    {
                        'Merchant': merchant,
                        'Total': format_currency(data['total']),
                        'Count': data['count'],
                        'Average': format_currency(data['average'])
                    }
                    for merchant, data in list(merchant_data.items())[:10]
                ])
                st.dataframe(merchant_df, use_container_width=True, hide_index=True)
            else:
                st.info("No merchant data available")
            
            # Time analysis
            st.markdown("### 📅 Spending by Day of Week")
            time_analysis = analytics['time_analysis']
            if time_analysis['by_day_of_week']:
                day_df = pd.DataFrame([
                    {'Day': day, 'Amount': amount}
                    for day, amount in time_analysis['by_day_of_week'].items()
                ])
                
                fig = px.bar(day_df, x='Day', y='Amount', color='Amount', 
                            color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"📊 Highest spending day: **{time_analysis['highest_spending_day']}**")
        
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")
    
    with tab2:
        st.subheader("🎯 Predictive Analytics")
        
        try:
            # Next month prediction
            st.markdown("### 📈 Next Month Spending Forecast")
            
            prediction = service.predict_spending()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Predicted Spending",
                    format_currency(prediction['predicted_amount']),
                    delta=f"{prediction['confidence']:.0%} confidence"
                )
            with col2:
                st.metric("Historical Avg", format_currency(prediction['historical_average']))
            with col3:
                st.metric("Expected Range", f"${prediction['min']:.0f} - ${prediction['max']:.0f}")
            
            # Budget suggestions
            st.markdown("### 💰 Suggested Budget Allocation")
            total_budget = st.number_input("Enter Total Monthly Budget ($)", min_value=100.0, value=3000.0, step=100.0)
            
            if st.button("Generate Suggestions"):
                suggestions = service.suggest_budgets(total_budget)
                if suggestions:
                    sugg_df = pd.DataFrame([
                        {'Category': cat, 'Suggested Budget': format_currency(amount)}
                        for cat, amount in suggestions.items()
                    ])
                    st.dataframe(sugg_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Need more historical data for suggestions")
        
        except Exception as e:
            st.error(f"Error loading predictions: {str(e)}")
    
    with tab3:
        st.subheader("⚠️ Anomaly Detection")
        
        try:
            dashboard = service.get_dashboard_data(days=30)
            anomalies = [service.get_transaction_by_id(a['id']) for a in dashboard['anomalies'] if a.get('id')]
            anomalies = [a for a in anomalies if a]
            
            if anomalies:
                st.warning(f"Found {len(anomalies)} unusual transactions")
                
                anomaly_df = pd.DataFrame([
                    {
                        'Date': a.date.strftime('%Y-%m-%d'),
                        'Merchant': a.merchant,
                        'Amount': format_currency(abs(a.amount)),
                        'Category': a.category.value,
                        'Notes': a.notes
                    }
                    for a in anomalies
                ])
                
                st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
                st.caption("💡 These transactions deviate significantly from your normal spending patterns")
            else:
                st.success("No anomalies detected! All spending appears normal.")
        
        except Exception as e:
            st.error(f"Error detecting anomalies: {str(e)}")
    
    with tab4:
        st.subheader("🔄 Recurring Transactions")
        
        try:
            recurring = service.get_recurring_transactions()
            
            if recurring:
                st.info(f"Found {len(recurring)} potential recurring transactions")
                
                recurring_df = pd.DataFrame([
                    {
                        'Merchant': r['merchant'],
                        'Amount': format_currency(r['amount']),
                        'Frequency': f"Every {r['frequency_days']} days",
                        'Last Date': r['last_date'][:10],
                        'Next Expected': r['next_expected'][:10],
                        'Confidence': format_percentage(r['confidence'] * 100)
                    }
                    for r in recurring
                ])
                
                st.dataframe(recurring_df, use_container_width=True, hide_index=True)
                
                st.caption("💡 Set up automatic budget allocations for these recurring expenses")
            else:
                st.info("No recurring patterns detected yet. Add more transactions to identify patterns.")
        
        except Exception as e:
            st.error(f"Error detecting recurring transactions: {str(e)}")

# ============================================================================
# PAGE 5
# ============================================================================

elif page == "💰 Budgets":
    st.markdown("<h1 class='main-header'>Budget Management</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Track and manage your spending budgets</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 Budget Overview", "➕ Manage Budgets"])
    
    with tab1:
        try:
            budget_status = service.get_budget_status(days=30)
            
            if budget_status['budgets']:
                # Overall progress
                total_budgeted = budget_status['total_budgeted']
                total_spent = budget_status['total_spent']
                overall_pct = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
                
                st.markdown("### 📊 Overall Budget Status")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Budgeted", format_currency(total_budgeted))
                with col2:
                    st.metric("Total Spent", format_currency(total_spent))
                with col3:
                    st.metric("Remaining", format_currency(total_budgeted - total_spent))
                
                st.progress(min(overall_pct / 100, 1.0))
                st.caption(f"{overall_pct:.1f}% of total budget used")
                
                st.markdown("---")
                
                # Individual budgets
                st.markdown("### 💰 Budget Details")
                
                for budget in budget_status['budgets']:
                    status = budget['status']
                    
                    if status == 'exceeded':
                        status_icon = "🚨"
                        status_color = "red"
                    elif status == 'warning':
                        status_icon = "⚠️"
                        status_color = "orange"
                    else:
                        status_icon = "✅"
                        status_color = "green"
                    
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown(f"{status_icon} **{budget['category']}**")
                            progress_val = min(budget['percentage_used'] / 100, 1.0)
                            st.progress(progress_val)
                        
                        with col2:
                            st.markdown(f"**Spent:** {format_currency(budget['spent'])}")
                            st.markdown(f"**Budget:** {format_currency(budget['budget'])}")
                        
                        with col3:
                            st.markdown(f"**Remaining:** {format_currency(budget['remaining'])}")
                            st.markdown(f"**Used:** {budget['percentage_used']:.1f}%")
                        
                        st.markdown("---")
            else:
                st.info("No budgets set yet. Create your first budget in the 'Manage Budgets' tab!")
        
        except Exception as e:
            st.error(f"Error loading budget status: {str(e)}")
    
    with tab2:
        st.subheader("Create New Budget")
        
        with st.form("budget_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_categories = [c.value for c in Category if 'Other Income' not in c.value and 'Salary' not in c.value and 'Freelance' not in c.value and 'Investment' not in c.value]
                budget_category = st.selectbox("Category", expense_categories)
            
            with col2:
                budget_amount = st.number_input("Monthly Budget ($)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("💾 Create Budget", use_container_width=True):
                try:
                    service.create_budget(
                        category=Category(budget_category),
                        amount=budget_amount
                    )
                    st.success("✅ Budget created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating budget: {str(e)}")
        
        st.markdown("---")
        st.subheader("Existing Budgets")
        
        try:
            budgets = service.get_all_budgets()
            if budgets:
                for budget in budgets:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.text(f"{budget.category.value}")
                    with col2:
                        st.text(format_currency(budget.amount))
                    with col3:
                        if st.button("🗑️", key=f"del_budget_{budget.id}"):
                            service.delete_budget(budget.id)
                            st.rerun()
            else:
                st.info("No budgets created yet")
        except Exception as e:
            st.error(f"Error loading budgets: {str(e)}")

# ============================================================================
# PAGE 6
# ============================================================================

elif page == "🎯 Goals":
    st.markdown("<h1 class='main-header'>Financial Goals</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Track your savings and financial objectives</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 Goal Progress", "➕ Manage Goals"])
    
    with tab1:
        try:
            goals = service.get_all_goals()
            
            if goals:
                for goal in goals:
                    progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                    
                    with st.container():
                        st.markdown(f"### 🎯 {goal.name}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Target", format_currency(goal.target_amount))
                        with col2:
                            st.metric("Current", format_currency(goal.current_amount))
                        with col3:
                            st.metric("Remaining", format_currency(goal.target_amount - goal.current_amount))
                        
                        st.progress(min(progress / 100, 1.0))
                        st.caption(f"{progress:.1f}% complete")
                        
                        if goal.deadline:
                            days_left = (goal.deadline - datetime.now()).days
                            if days_left > 0:
                                st.info(f"📅 {days_left} days remaining until {goal.deadline.strftime('%Y-%m-%d')}")
                            else:
                                st.warning("⏰ Deadline passed!")
                        
                        st.markdown("---")
            else:
                st.info("No goals set yet. Create your first financial goal!")
        
        except Exception as e:
            st.error(f"Error loading goals: {str(e)}")
    
    with tab2:
        st.subheader("Create New Goal")
        
        with st.form("goal_form"):
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, Vacation")
            
            col1, col2 = st.columns(2)
            with col1:
                target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=100.0)
            with col2:
                deadline = st.date_input("Deadline (Optional)", value=None)
            
            if st.form_submit_button("💾 Create Goal", use_container_width=True):
                try:
                    service.create_goal(
                        name=goal_name,
                        target_amount=target_amount,
                        deadline=datetime.combine(deadline, datetime.min.time()) if deadline else None
                    )
                    st.success("✅ Goal created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating goal: {str(e)}")
        
        st.markdown("---")
        st.subheader("Manage Existing Goals")
        
        try:
            goals = service.get_all_goals()
            if goals:
                for goal in goals:
                    with st.expander(f"🎯 {goal.name}"):
                        st.write(f"**Target:** {format_currency(goal.target_amount)}")
                        st.write(f"**Current:** {format_currency(goal.current_amount)}")
                        
                        new_amount = st.number_input(
                            "Update Current Amount",
                            value=float(goal.current_amount),
                            key=f"goal_{goal.id}"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 Update", key=f"update_{goal.id}", use_container_width=True):
                                goal.current_amount = new_amount
                                service.update_goal(goal)
                                st.success("Goal updated!")
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_{goal.id}", use_container_width=True):
                                service.delete_goal(goal.id)
                                st.success("Goal deleted!")
                                st.rerun()
        except Exception as e:
            st.error(f"Error managing goals: {str(e)}")

# ============================================================================
# PAGE 7
# ============================================================================

elif page == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>Settings</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Configure your preferences and manage data</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🗄️ Database", "📤 Export/Import", "ℹ️ About"])
    
    with tab1:
        st.subheader("Database Management")
        
        try:
            stats = service.get_database_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Transactions", stats['total_transactions'])
            with col2:
                st.metric("Budgets", stats['total_budgets'])
            with col3:
                st.metric("Goals", stats['total_goals'])
            
            st.metric("Database Size", f"{stats['db_size_mb']:.2f} MB")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Backup Database", use_container_width=True):
                    try:
                        backup_path = service.backup_database()
                        st.success(f"✅ Backup created: {backup_path}")
                    except Exception as e:
                        st.error(f"Backup failed: {str(e)}")
            
            with col2:
                if st.button("🔧 Optimize Database", use_container_width=True):
                    try:
                        service.optimize_database()
                        st.success("✅ Database optimized!")
                    except Exception as e:
                        st.error(f"Optimization failed: {str(e)}")
            
            st.markdown("---")
            st.warning("⚠️ Danger Zone")
            
            if st.checkbox("Enable dangerous operations"):
                if st.button("🗑️ Clear All Data", type="secondary"):
                    st.error("This operation is not available in this version for safety")
        
        except Exception as e:
            st.error(f"Error loading database stats: {str(e)}")
    
    with tab2:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        with col1:
            export_start = st.date_input("From", datetime.now() - timedelta(days=90))
        with col2:
            export_end = st.date_input("To", datetime.now())
        
        if st.button("📥 Export Transactions", use_container_width=True):
            try:
                csv_data = service.export_to_csv(
                    datetime.combine(export_start, datetime.min.time()),
                    datetime.combine(export_end, datetime.min.time())
                )
                st.download_button(
                    "Download CSV",
                    csv_data,
                    file_name=f"transactions_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
        
        st.markdown("---")
        st.subheader("Import Data")
        st.caption("CSV format: date, amount, merchant, category (optional), notes (optional)")
        
        sample_csv = """date,amount,merchant,category,notes
2024-12-15,-50.00,Starbucks,Dining & Restaurants,Morning coffee
2024-12-14,-120.50,Whole Foods,Groceries,Weekly shopping
2024-12-13,3000.00,Acme Corp,Salary,Monthly salary"""
        
        st.download_button(
            "📄 Download Sample CSV",
            sample_csv,
            file_name="sample_transactions.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("About Personal Finance Advisor")
        
        st.markdown("""
        ### 💰 Personal Finance Advisor
        **Version:** 1.0.0
        
        An AI-powered personal finance management system with:
        - 📊 Comprehensive financial dashboard
        - 🤖 ML-powered transaction categorization
        - 📈 Advanced analytics and insights
        - 💰 Budget tracking and management
        - 🎯 Financial goal tracking
        - 🔄 Recurring transaction detection
        - ⚠️ Anomaly detection
        
        ### 🛠️ Built With
        - **Backend:** Python, SQLite
        - **Frontend:** Streamlit
        - **Analytics:** Pandas, Plotly
        - **ML:** Custom ML engine
        
        ### 📚 Resources
        - [Documentation](#)
        - [GitHub Repository](#)
        - [Report Issues](#)
        
        ### 📧 Support
        For support, contact: support@financeadvisor.com
        
        ---
        
        Made with ❤️ for better financial management
        """)



st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💰 Personal Finance Advisor v1.0.0 | Your data stays private and secure</p>
    <p>🔒 All data stored locally | Last updated: Just now</p>
</div>
""", unsafe_allow_html=True)