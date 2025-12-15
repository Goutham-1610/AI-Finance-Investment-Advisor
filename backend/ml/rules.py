RULES = {
    "starbucks": "Dining & Restaurants",
    "uber": "Transportation",
    "ola": "Transportation",
    "zomato": "Dining & Restaurants",
    "swiggy": "Dining & Restaurants",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "netflix": "Entertainment",
    "rent": "Rent/Mortgage",
    "salary": "Salary",
    "bonus": "Salary",
}

def rule_based_category(merchant: str):
    merchant = merchant.lower()
    for keyword, category in RULES.items():
        if keyword in merchant:
            return category
    return None
