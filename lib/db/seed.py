"""Database seeding utilities for the finance tracker application."""

from datetime import date, datetime, timedelta
import random
from typing import List, Dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import (
    get_db_session, init_db, User, Transaction, Budget, SavingsGoal, 
    TransactionType, Tag, UserProfile
)
from helpers import format_currency


def create_sample_users() -> List[User]:
    """Create sample users for testing."""
    sample_users = [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "default_currency": "USD",
            "monthly_income": 5000.0
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "default_currency": "USD",
            "monthly_income": 4500.0
        },
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "default_currency": "EUR",
            "monthly_income": 4200.0
        },
        {
            "name": "Bob Wilson",
            "email": "bob.wilson@example.com",
            "default_currency": "USD",
            "monthly_income": 6000.0
        },
        {
            "name": "Emma Davis",
            "email": "emma.davis@example.com",
            "default_currency": "GBP",
            "monthly_income": 3800.0
        }
    ]
    
    created_users = []
    
    with get_db_session() as session:
        for user_data in sample_users:
            # Check if user already exists
            existing_user = session.query(User).filter_by(email=user_data["email"]).first()
            if existing_user:
                created_users.append(existing_user)
                continue
            
            user = User(**user_data)
            session.add(user)
            session.flush()  # Get the ID
            created_users.append(user)
    
    return created_users


def create_sample_user_profiles(users: List[User]) -> List[UserProfile]:
    """Create sample user profiles."""
    profile_data = [
        {
            "phone_number": "+1-555-0101",
            "address": "123 Main St, New York, NY 10001",
            "occupation": "Software Engineer",
            "annual_income": 60000.0,
            "financial_goal": "Save for a house down payment",
            "risk_tolerance": "medium"
        },
        {
            "phone_number": "+1-555-0102",
            "address": "456 Oak Ave, Los Angeles, CA 90210",
            "occupation": "Marketing Manager",
            "annual_income": 54000.0,
            "financial_goal": "Build emergency fund and retirement savings",
            "risk_tolerance": "low"
        },
        {
            "phone_number": "+33-1-23-45-67-89",
            "address": "789 Rue de la Paix, Paris, France",
            "occupation": "Graphic Designer",
            "annual_income": 50400.0,
            "financial_goal": "Travel fund and creative equipment",
            "risk_tolerance": "high"
        },
        {
            "phone_number": "+1-555-0104",
            "address": "321 Pine St, Seattle, WA 98101",
            "occupation": "Data Analyst",
            "annual_income": 72000.0,
            "financial_goal": "Investment portfolio growth",
            "risk_tolerance": "medium"
        },
        {
            "phone_number": "+44-20-7946-0958",
            "address": "654 Baker Street, London, UK",
            "occupation": "Teacher",
            "annual_income": 45600.0,
            "financial_goal": "Education fund for children",
            "risk_tolerance": "low"
        }
    ]
    
    created_profiles = []
    
    with get_db_session() as session:
        for i, user in enumerate(users):
            if i < len(profile_data):
                # Check if profile already exists
                existing_profile = session.query(UserProfile).filter_by(user_id=user.id).first()
                if existing_profile:
                    created_profiles.append(existing_profile)
                    continue
                
                profile = UserProfile(user_id=user.id, **profile_data[i])
                session.add(profile)
                session.flush()
                created_profiles.append(profile)
    
    return created_profiles


def create_sample_tags() -> List[Tag]:
    """Create sample tags for transactions."""
    tag_data = [
        {"name": "work", "description": "Work-related expenses", "color": "#007bff"},
        {"name": "food", "description": "Food and dining", "color": "#28a745"},
        {"name": "transport", "description": "Transportation costs", "color": "#ffc107"},
        {"name": "entertainment", "description": "Entertainment and leisure", "color": "#e83e8c"},
        {"name": "health", "description": "Healthcare expenses", "color": "#20c997"},
        {"name": "education", "description": "Educational expenses", "color": "#6f42c1"},
        {"name": "shopping", "description": "Shopping and retail", "color": "#fd7e14"},
        {"name": "utilities", "description": "Utility bills", "color": "#6c757d"},
        {"name": "rent", "description": "Housing and rent", "color": "#dc3545"},
        {"name": "investment", "description": "Investment related", "color": "#17a2b8"},
        {"name": "recurring", "description": "Recurring transactions", "color": "#343a40"},
        {"name": "one-time", "description": "One-time expenses", "color": "#f8f9fa"}
    ]
    
    created_tags = []
    
    with get_db_session() as session:
        for tag_info in tag_data:
            # Check if tag already exists
            existing_tag = session.query(Tag).filter_by(name=tag_info["name"]).first()
            if existing_tag:
                created_tags.append(existing_tag)
                continue
            
            tag = Tag(**tag_info)
            session.add(tag)
            session.flush()
            created_tags.append(tag)
    
    return created_tags


def create_sample_transactions(users: List[User], tags: List[Tag]) -> List[Transaction]:
    """Create sample transactions for users."""
    
    # Common transaction categories and amounts
    income_categories = [
        ("Salary", [3000, 5000, 4500, 6000]),
        ("Freelance", [500, 1500, 800, 1200]),
        ("Bonus", [1000, 2000, 1500]),
        ("Investment", [100, 500, 300, 200])
    ]
    
    expense_categories = [
        ("Rent", [1200, 1500, 1800, 2000]),
        ("Groceries", [150, 300, 200, 250]),
        ("Gas", [40, 80, 60, 70]),
        ("Utilities", [100, 150, 120, 180]),
        ("Internet", [50, 80, 60]),
        ("Phone", [30, 50, 40]),
        ("Dining", [25, 75, 50, 100]),
        ("Entertainment", [20, 100, 50, 80]),
        ("Shopping", [50, 200, 100, 150]),
        ("Health", [50, 300, 100, 200]),
        ("Transportation", [30, 100, 50, 80]),
        ("Coffee", [5, 15, 10, 8]),
        ("Gym", [30, 50, 40]),
        ("Subscription", [10, 20, 15])
    ]
    
    created_transactions = []
    
    with get_db_session() as session:
        for user in users:
            # Generate transactions for the last 6 months
            start_date = date.today() - timedelta(days=180)
            current_date = start_date
            
            while current_date <= date.today():
                # Income transactions (1-2 per month)
                if current_date.day in [1, 15]:  # Bi-monthly salary
                    category, amounts = random.choice(income_categories)
                    amount = random.choice(amounts)
                    
                    transaction = Transaction(
                        amount=amount,
                        category=category,
                        description=f"Monthly {category.lower()}",
                        transaction_type=TransactionType.INCOME,
                        transaction_date=current_date,
                        user_id=user.id
                    )
                    
                    # Add random tags
                    if category == "Salary":
                        work_tag = next((t for t in tags if t.name == "work"), None)
                        recurring_tag = next((t for t in tags if t.name == "recurring"), None)
                        if work_tag:
                            transaction.tags.append(work_tag)
                        if recurring_tag:
                            transaction.tags.append(recurring_tag)
                    
                    session.add(transaction)
                    created_transactions.append(transaction)
                
                # Expense transactions (3-8 per week)
                if random.random() < 0.7:  # 70% chance of expense on any day
                    num_expenses = random.randint(1, 3)
                    
                    for _ in range(num_expenses):
                        category, amounts = random.choice(expense_categories)
                        amount = random.choice(amounts)
                        
                        descriptions = {
                            "Rent": ["Monthly rent payment", "Rent for apartment"],
                            "Groceries": ["Weekly shopping", "Grocery store visit", "Food shopping"],
                            "Gas": ["Gas station fill-up", "Fuel for car"],
                            "Utilities": ["Electric bill", "Water bill", "Gas bill"],
                            "Dining": ["Restaurant dinner", "Lunch out", "Fast food", "Coffee shop"],
                            "Entertainment": ["Movie tickets", "Concert", "Games", "Books"],
                            "Shopping": ["Clothing", "Electronics", "Home goods", "Personal items"],
                            "Health": ["Doctor visit", "Pharmacy", "Dental", "Medical supplies"],
                            "Transportation": ["Bus fare", "Uber ride", "Taxi", "Parking"],
                            "Coffee": ["Morning coffee", "Afternoon coffee", "Coffee meeting"]
                        }
                        
                        desc_options = descriptions.get(category, [f"{category} expense"])
                        description = random.choice(desc_options)
                        
                        transaction = Transaction(
                            amount=amount,
                            category=category,
                            description=description,
                            transaction_type=TransactionType.EXPENSE,
                            transaction_date=current_date,
                            user_id=user.id
                        )
                        
                        # Add appropriate tags
                        tag_mapping = {
                            "Groceries": ["food"],
                            "Dining": ["food"],
                            "Coffee": ["food"],
                            "Gas": ["transport"],
                            "Transportation": ["transport"],
                            "Entertainment": ["entertainment"],
                            "Shopping": ["shopping"],
                            "Health": ["health"],
                            "Utilities": ["utilities", "recurring"],
                            "Rent": ["rent", "recurring"],
                            "Internet": ["utilities", "recurring"],
                            "Phone": ["utilities", "recurring"],
                            "Gym": ["health", "recurring"],
                            "Subscription": ["recurring"]
                        }
                        
                        tag_names = tag_mapping.get(category, [])
                        for tag_name in tag_names:
                            tag = next((t for t in tags if t.name == tag_name), None)
                            if tag:
                                transaction.tags.append(tag)
                        
                        # Add one-time or recurring tag
                        if category in ["Rent", "Utilities", "Internet", "Phone", "Gym", "Subscription"]:
                            recurring_tag = next((t for t in tags if t.name == "recurring"), None)
                            if recurring_tag and recurring_tag not in transaction.tags:
                                transaction.tags.append(recurring_tag)
                        else:
                            one_time_tag = next((t for t in tags if t.name == "one-time"), None)
                            if one_time_tag and random.random() < 0.3:
                                transaction.tags.append(one_time_tag)
                        
                        session.add(transaction)
                        created_transactions.append(transaction)
                
                current_date += timedelta(days=1)
    
    return created_transactions


def create_sample_budgets(users: List[User]) -> List[Budget]:
    """Create sample budgets for users."""
    
    budget_templates = [
        {"category": "Groceries", "limit": 400},
        {"category": "Dining", "limit": 200},
        {"category": "Entertainment", "limit": 150},
        {"category": "Shopping", "limit": 300},
        {"category": "Transportation", "limit": 200},
        {"category": "Health", "limit": 250},
        {"category": "Utilities", "limit": 200}
    ]
    
    created_budgets = []
    current_month = date.today().strftime("%Y-%m")
    
    with get_db_session() as session:
        for user in users:
            # Create 3-5 random budgets per user
            num_budgets = random.randint(3, 5)
            selected_budgets = random.sample(budget_templates, num_budgets)
            
            for budget_template in selected_budgets:
                # Check if budget already exists
                existing_budget = session.query(Budget).filter_by(
                    user_id=user.id,
                    category=budget_template["category"],
                    month=current_month
                ).first()
                
                if existing_budget:
                    created_budgets.append(existing_budget)
                    continue
                
                # Add some variation to the budget limit
                base_limit = budget_template["limit"]
                variation = random.uniform(0.8, 1.2)  # ±20% variation
                limit = round(base_limit * variation, 2)
                
                budget = Budget(
                    category=budget_template["category"],
                    limit_amount=limit,
                    month=current_month,
                    description=f"Monthly budget for {budget_template['category'].lower()}",
                    user_id=user.id
                )
                
                session.add(budget)
                created_budgets.append(budget)
    
    return created_budgets


def create_sample_savings_goals(users: List[User]) -> List[SavingsGoal]:
    """Create sample savings goals for users."""
    
    goal_templates = [
        {"name": "Emergency Fund", "target": 10000, "description": "6 months of expenses"},
        {"name": "Vacation", "target": 3000, "description": "Summer vacation fund"},
        {"name": "New Car", "target": 15000, "description": "Down payment for new car"},
        {"name": "House Down Payment", "target": 50000, "description": "20% down payment for house"},
        {"name": "Retirement", "target": 100000, "description": "Long-term retirement savings"},
        {"name": "Education", "target": 20000, "description": "Masters degree funding"},
        {"name": "Home Improvement", "target": 8000, "description": "Kitchen renovation"},
        {"name": "Technology Fund", "target": 2500, "description": "New laptop and gadgets"}
    ]
    
    created_goals = []
    
    with get_db_session() as session:
        for user in users:
            # Create 2-4 random goals per user
            num_goals = random.randint(2, 4)
            selected_goals = random.sample(goal_templates, num_goals)
            
            for goal_template in selected_goals:
                # Check if goal already exists
                existing_goal = session.query(SavingsGoal).filter_by(
                    user_id=user.id,
                    name=goal_template["name"]
                ).first()
                
                if existing_goal:
                    created_goals.append(existing_goal)
                    continue
                
                # Add some variation to target amount
                base_target = goal_template["target"]
                variation = random.uniform(0.8, 1.3)  # ±20-30% variation
                target = round(base_target * variation, 2)
                
                # Random current progress (0-80% of target)
                progress_percentage = random.uniform(0, 0.8)
                current_amount = round(target * progress_percentage, 2)
                
                goal = SavingsGoal(
                    name=goal_template["name"],
                    target_amount=target,
                    current_amount=current_amount,
                    description=goal_template["description"],
                    is_achieved=current_amount >= target,
                    user_id=user.id
                )
                
                session.add(goal)
                created_goals.append(goal)
    
    return created_goals


def seed_database(include_transactions: bool = True, include_budgets: bool = True, 
                 include_goals: bool = True) -> Dict:
    """Seed the database with sample data."""
    
    print("🌱 Seeding database with sample data...")
    
    # Initialize database
    init_db()
    
    # Create sample data
    users = create_sample_users()
    print(f"✓ Created {len(users)} users")
    
    # Get fresh user instances for subsequent operations
    with get_db_session() as session:
        fresh_users = session.query(User).all()
    
    profiles = create_sample_user_profiles(fresh_users)
    print(f"✓ Created {len(profiles)} user profiles")
    
    tags = create_sample_tags()
    print(f"✓ Created {len(tags)} tags")
    
    # Get fresh instances again
    with get_db_session() as session:
        fresh_users = session.query(User).all()
        fresh_tags = session.query(Tag).all()
    
    transactions = []
    if include_transactions:
        transactions = create_sample_transactions(fresh_users, fresh_tags)
        print(f"✓ Created {len(transactions)} transactions")
    
    budgets = []
    if include_budgets:
        with get_db_session() as session:
            fresh_users = session.query(User).all()
        budgets = create_sample_budgets(fresh_users)
        print(f"✓ Created {len(budgets)} budgets")
    
    goals = []
    if include_goals:
        with get_db_session() as session:
            fresh_users = session.query(User).all()
        goals = create_sample_savings_goals(fresh_users)
        print(f"✓ Created {len(goals)} savings goals")
    
    summary = {
        "users": len(users),
        "profiles": len(profiles),
        "tags": len(tags),
        "transactions": len(transactions),
        "budgets": len(budgets),
        "savings_goals": len(goals)
    }
    
    print(f"\n🎉 Database seeding completed!")
    print(f"Summary: {summary}")
    
    return summary


def clear_database():
    """Clear all data from the database (use with caution!)."""
    
    print("⚠️  Clearing all database data...")
    
    with get_db_session() as session:
        # Delete in proper order to respect foreign key constraints
        session.query(UserProfile).delete()
        session.query(SavingsGoal).delete()
        session.query(Budget).delete()
        session.query(Transaction).delete()
        session.query(Tag).delete()
        session.query(User).delete()
    
    print("✓ Database cleared")


def reset_and_seed():
    """Clear database and reseed with fresh data."""
    clear_database()
    return seed_database()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "seed":
            seed_database()
        elif command == "clear":
            clear_database()
        elif command == "reset":
            reset_and_seed()
        else:
            print("Usage: python seed.py [seed|clear|reset]")
    else:
        # Default action
        seed_database()