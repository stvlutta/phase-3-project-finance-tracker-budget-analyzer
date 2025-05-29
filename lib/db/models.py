"""Database models for the finance tracker application."""

import enum
from datetime import datetime, date
from typing import List, Dict, Optional, Union
from collections import defaultdict

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Enum, Text, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database configuration
DATABASE_URL = "sqlite:///finance_tracker.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TransactionType(enum.Enum):
    """Enum for transaction types."""
    INCOME = "income"
    EXPENSE = "expense"


# Association table for many-to-many relationship between transactions and tags
transaction_tags = Table(
    'transaction_tags',
    Base.metadata,
    Column('transaction_id', Integer, ForeignKey('transactions.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(Date, default=lambda: date.today())
    updated_at = Column(Date, default=lambda: date.today(), onupdate=lambda: date.today())


class User(BaseModel):
    """User model to represent application users."""
    
    __tablename__ = 'users'
    
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    default_currency = Column(String(3), default='USD', nullable=False)
    monthly_income = Column(Float, default=0.0)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    savings_goals = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    
    # One-to-one relationship with user profile
    profile = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'default_currency': self.default_currency,
            'monthly_income': self.monthly_income,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserProfile(BaseModel):
    """User profile model for one-to-one relationship with user."""
    
    __tablename__ = 'user_profiles'
    
    # One-to-one relationship with user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Profile information
    phone_number = Column(String(20))
    address = Column(Text)
    occupation = Column(String(100))
    annual_income = Column(Float)
    financial_goal = Column(Text)
    risk_tolerance = Column(String(20), default='medium')  # low, medium, high
    currency_preference = Column(String(3), default='USD')
    notifications_enabled = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)
    
    # One-to-one relationship
    user = relationship("User", back_populates="profile", uselist=False)
    
    def to_dict(self) -> dict:
        """Convert user profile to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'address': self.address,
            'occupation': self.occupation,
            'annual_income': self.annual_income,
            'financial_goal': self.financial_goal,
            'risk_tolerance': self.risk_tolerance,
            'currency_preference': self.currency_preference,
            'notifications_enabled': self.notifications_enabled,
            'dark_mode': self.dark_mode,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, occupation='{self.occupation}')>"


class Transaction(BaseModel):
    """Transaction model to represent financial transactions."""
    
    __tablename__ = 'transactions'
    
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_date = Column(Date, default=date.today, nullable=False)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    # Many-to-many relationship with tags
    tags = relationship(
        'Tag',
        secondary='transaction_tags',
        back_populates='transactions'
    )
    
    def __repr__(self):
        return (f"<Transaction(id={self.id}, amount={self.amount}, "
                f"type={self.transaction_type.value}, category='{self.category}')>")
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'category': self.category,
            'transaction_type': self.transaction_type.value,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'user_id': self.user_id,
            'tags': [tag.name for tag in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Tag(BaseModel):
    """Tag model for many-to-many relationship with transactions."""
    
    __tablename__ = 'tags'
    
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7), default='#007bff')  # Hex color code
    
    # Many-to-many relationship with transactions
    transactions = relationship(
        'Transaction',
        secondary='transaction_tags',
        back_populates='tags'
    )
    
    def to_dict(self) -> dict:
        """Convert tag to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'transaction_count': len(self.transactions),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f"<Tag(name='{self.name}', color='{self.color}')>"


class Budget(BaseModel):
    """Budget model to represent monthly budgets."""
    
    __tablename__ = 'budgets'
    
    category = Column(String(100), nullable=False)
    limit_amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    description = Column(Text)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="budgets")
    
    def get_spent_amount(self, transactions: List[Transaction]) -> float:
        """Calculate amount spent in this budget category for the month."""
        spent = 0.0
        for transaction in transactions:
            if (transaction.category == self.category and 
                transaction.transaction_type == TransactionType.EXPENSE and
                transaction.transaction_date.strftime("%Y-%m") == self.month):
                spent += transaction.amount
        return spent
    
    def get_remaining_amount(self, transactions: List[Transaction]) -> float:
        """Calculate remaining budget amount."""
        spent = self.get_spent_amount(transactions)
        return self.limit_amount - spent
    
    def is_over_budget(self, transactions: List[Transaction]) -> bool:
        """Check if budget is exceeded."""
        return self.get_remaining_amount(transactions) < 0
    
    def __repr__(self):
        return (f"<Budget(id={self.id}, category='{self.category}', "
                f"limit={self.limit_amount}, month='{self.month}')>")
    
    def to_dict(self):
        """Convert budget to dictionary."""
        return {
            'id': self.id,
            'category': self.category,
            'limit_amount': self.limit_amount,
            'month': self.month,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SavingsGoal(BaseModel):
    """Savings goal model to represent financial targets."""
    
    __tablename__ = 'savings_goals'
    
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0, nullable=False)
    description = Column(Text)
    is_achieved = Column(Boolean, default=False, nullable=False)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="savings_goals")
    
    def add_contribution(self, amount: float):
        """Add contribution to savings goal."""
        self.current_amount += amount
        if self.current_amount >= self.target_amount:
            self.is_achieved = True
    
    def get_progress_percentage(self) -> float:
        """Calculate progress as percentage."""
        if self.target_amount <= 0:
            return 0.0
        return min((self.current_amount / self.target_amount) * 100, 100.0)
    
    def get_remaining_amount(self) -> float:
        """Calculate remaining amount to reach goal."""
        return max(self.target_amount - self.current_amount, 0.0)
    
    def __repr__(self):
        return (f"<SavingsGoal(id={self.id}, name='{self.name}', "
                f"target={self.target_amount}, current={self.current_amount})>")
    
    def to_dict(self):
        """Convert savings goal to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'description': self.description,
            'is_achieved': self.is_achieved,
            'progress_percentage': self.get_progress_percentage(),
            'remaining_amount': self.get_remaining_amount(),
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


from contextlib import contextmanager

@contextmanager
def get_db_session():
    """Get database session context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def init_db_with_alembic():
    """Initialize database using Alembic migrations."""
    from alembic.config import Config
    from alembic import command
    import os
    
    # Get the path to alembic.ini
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_cfg = Config(os.path.join(current_dir, "alembic.ini"))
    
    try:
        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
        print("Database initialized with Alembic migrations!")
    except Exception as e:
        print(f"Error running Alembic migrations: {e}")
        # Fallback to direct table creation
        init_db()


if __name__ == "__main__":
    # Create all tables
    init_db()