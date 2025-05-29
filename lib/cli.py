"""CLI interface for the finance tracker application."""

import click
from datetime import datetime, date
from typing import List, Dict, Tuple
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.text import Text
from rich.align import Align

from lib.db.models import (
    get_db_session, init_db, init_db_with_alembic, User, Transaction, Budget, SavingsGoal, 
    TransactionType, Tag, UserProfile
)
from lib.helpers import (
    format_currency, format_date, format_percentage,
    validate_amount, validate_email, validate_category, 
    validate_date, validate_month, validate_name, validate_description
)


class FinanceTrackerCLI:
    """Main CLI class for finance tracker operations."""
    
    def __init__(self):
        self.current_user_id = None
        self.current_user = None
        self.console = Console()
    
    def get_or_create_user(self, name: str, email: str) -> User:
        """Get existing user or create new one."""
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                user = User(name=name, email=email)
                session.add(user)
                session.flush()
                user_id = user.id
                user_name = user.name
                self.console.print(f"[green]Created new user: {name} ({email})[/green]")
            else:
                user_id = user.id
                user_name = user.name
                self.console.print(f"[blue]Welcome back, {user.name}![/blue]")
            
            self.current_user_id = user_id
            return user
    
    def add_transaction(self, amount: float, category: str, description: str, 
                       transaction_type: str, transaction_date: date = None) -> bool:
        """Add a new transaction."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        try:
            with get_db_session() as session:
                trans_type = TransactionType.INCOME if transaction_type.lower() == 'income' else TransactionType.EXPENSE
                
                transaction = Transaction(
                    amount=amount,
                    category=category,
                    description=description,
                    transaction_type=trans_type,
                    transaction_date=transaction_date or date.today(),
                    user_id=self.current_user_id
                )
                
                session.add(transaction)
                self.console.print(f"[green]✓ {transaction_type.capitalize()} of {format_currency(amount)} added to {category}[/green]")
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error adding transaction: {str(e)}[/red]")
            return False
    
    def view_transactions(self, limit: int = 10) -> List[Dict]:
        """View recent transactions."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return []
        
        try:
            with get_db_session() as session:
                transactions = session.query(Transaction).filter_by(
                    user_id=self.current_user_id
                ).order_by(Transaction.transaction_date.desc()).limit(limit).all()
                
                if not transactions:
                    self.console.print("[yellow]No transactions found.[/yellow]")
                    return []
                
                # Create Rich table for transactions
                table = Table(title=f"Recent {limit} Transactions", show_header=True, header_style="bold magenta")
                table.add_column("Date", style="cyan", width=12)
                table.add_column("Type", style="yellow", width=8)
                table.add_column("Amount", style="green", width=12, justify="right")
                table.add_column("Category", style="blue", width=15)
                table.add_column("Description", style="white", width=20)
                table.add_column("Tags", style="purple", width=15)
                
                transaction_list = []
                for transaction in transactions:
                    amount_str = format_currency(transaction.amount)
                    type_color = "green" if transaction.transaction_type == TransactionType.INCOME else "red"
                    tags_str = ", ".join([tag.name for tag in transaction.tags]) if transaction.tags else ""
                    
                    table.add_row(
                        format_date(transaction.transaction_date),
                        f"[{type_color}]{transaction.transaction_type.value}[/{type_color}]",
                        f"[{type_color}]{amount_str}[/{type_color}]",
                        transaction.category,
                        transaction.description,
                        tags_str
                    )
                    transaction_list.append(transaction.to_dict())
                
                self.console.print(table)
                return transaction_list
                
        except Exception as e:
            self.console.print(f"[red]Error viewing transactions: {str(e)}[/red]")
            return []
    
    def add_budget(self, category: str, limit_amount: float, month: str = None) -> bool:
        """Add or update a budget."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        try:
            with get_db_session() as session:
                # Remove existing budget for this category and month
                existing_budget = session.query(Budget).filter_by(
                    user_id=self.current_user_id,
                    category=category,
                    month=month
                ).first()
                
                if existing_budget:
                    existing_budget.limit_amount = limit_amount
                    self.console.print(f"[green]✓ Updated budget for {category} to {format_currency(limit_amount)}[/green]")
                else:
                    budget = Budget(
                        category=category,
                        limit_amount=limit_amount,
                        month=month,
                        user_id=self.current_user_id
                    )
                    session.add(budget)
                    self.console.print(f"[green]✓ Budget of {format_currency(limit_amount)} set for {category}[/green]")
                
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error adding budget: {str(e)}[/red]")
            return False
    
    def view_budgets(self, month: str = None) -> List[Dict]:
        """View budgets and spending."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return []
        
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        try:
            with get_db_session() as session:
                budgets = session.query(Budget).filter_by(
                    user_id=self.current_user_id,
                    month=month
                ).all()
                
                if not budgets:
                    self.console.print(f"[yellow]No budgets set for {month}.[/yellow]")
                    return []
                
                # Get transactions for the month
                transactions = session.query(Transaction).filter(
                    Transaction.user_id == self.current_user_id,
                    Transaction.transaction_date.like(f"{month}%")
                ).all()
                
                # Create Rich table for budgets
                table = Table(title=f"Budget Overview for {month}", show_header=True, header_style="bold magenta")
                table.add_column("Category", style="cyan", width=15)
                table.add_column("Budget", style="blue", width=12, justify="right")
                table.add_column("Spent", style="yellow", width=12, justify="right")
                table.add_column("Remaining", style="green", width=12, justify="right")
                table.add_column("Progress", style="purple", width=12, justify="center")
                table.add_column("Status", style="white", width=10, justify="center")
                
                budget_list = []
                for budget in budgets:
                    spent = budget.get_spent_amount(transactions)
                    remaining = budget.get_remaining_amount(transactions)
                    progress_pct = (spent / budget.limit_amount) * 100 if budget.limit_amount > 0 else 0
                    
                    if remaining >= 0:
                        status = "[green]✓ Good[/green]"
                        remaining_color = "green"
                    else:
                        status = "[red]⚠ Over[/red]"
                        remaining_color = "red"
                    
                    table.add_row(
                        budget.category,
                        format_currency(budget.limit_amount),
                        f"[yellow]{format_currency(spent)}[/yellow]",
                        f"[{remaining_color}]{format_currency(remaining)}[/{remaining_color}]",
                        f"{progress_pct:.1f}%",
                        status
                    )
                    
                    budget_data = budget.to_dict()
                    budget_data['spent'] = spent
                    budget_data['remaining'] = remaining
                    budget_list.append(budget_data)
                
                self.console.print(table)
                return budget_list
                
        except Exception as e:
            self.console.print(f"[red]Error viewing budgets: {str(e)}[/red]")
            return []
    
    def add_savings_goal(self, name: str, target_amount: float, description: str = "") -> bool:
        """Add a new savings goal."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        try:
            with get_db_session() as session:
                goal = SavingsGoal(
                    name=name,
                    target_amount=target_amount,
                    description=description,
                    user_id=self.current_user_id
                )
                
                session.add(goal)
                self.console.print(f"[green]✓ Savings goal '{name}' of {format_currency(target_amount)} created[/green]")
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error adding savings goal: {str(e)}[/red]")
            return False
    
    def update_savings_goal(self, name: str, amount: float) -> bool:
        """Update progress on a savings goal."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        try:
            with get_db_session() as session:
                goal = session.query(SavingsGoal).filter_by(
                    user_id=self.current_user_id,
                    name=name
                ).first()
                
                if not goal:
                    self.console.print(f"[yellow]Savings goal '{name}' not found[/yellow]")
                    return False
                
                goal.add_contribution(amount)
                self.console.print(f"[green]✓ Added {format_currency(amount)} to '{goal.name}' savings goal[/green]")
                self.console.print(f"Progress: {format_currency(goal.current_amount)} / "
                          f"{format_currency(goal.target_amount)} "
                          f"({format_percentage(goal.get_progress_percentage())})")
                
                if goal.is_achieved:
                    self.console.print("[green]🎉 Congratulations! Goal achieved![/green]")
                
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error updating savings goal: {str(e)}[/red]")
            return False
    
    def view_savings_goals(self) -> List[Dict]:
        """View all savings goals."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return []
        
        try:
            with get_db_session() as session:
                goals = session.query(SavingsGoal).filter_by(
                    user_id=self.current_user_id
                ).all()
                
                if not goals:
                    self.console.print("[yellow]No savings goals set.[/yellow]")
                    return []
                
                # Create Rich table for savings goals with progress bars
                table = Table(title="Savings Goals", show_header=True, header_style="bold magenta")
                table.add_column("Goal", style="cyan", width=20)
                table.add_column("Target", style="blue", width=12, justify="right")
                table.add_column("Current", style="green", width=12, justify="right")
                table.add_column("Progress", style="purple", width=30)
                table.add_column("Status", style="white", width=10, justify="center")
                
                goals_list = []
                for goal in goals:
                    progress_pct = goal.get_progress_percentage()
                    
                    # Create progress bar
                    progress_bar = self._create_progress_bar(progress_pct)
                    
                    if goal.is_achieved:
                        status = "[green]✓ Complete[/green]"
                    else:
                        status = f"{format_percentage(progress_pct)}"
                    
                    table.add_row(
                        goal.name,
                        format_currency(goal.target_amount),
                        f"[green]{format_currency(goal.current_amount)}[/green]",
                        progress_bar,
                        status
                    )
                    
                    goals_list.append(goal.to_dict())
                
                self.console.print(table)
                return goals_list
                
        except Exception as e:
            self.console.print(f"[red]Error viewing savings goals: {str(e)}[/red]")
            return []
    
    def generate_report(self, month: str = None) -> Dict:
        """Generate comprehensive financial report."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return {}
        
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        try:
            with get_db_session() as session:
                # Get transactions for the month
                transactions = session.query(Transaction).filter(
                    Transaction.user_id == self.current_user_id,
                    Transaction.transaction_date.like(f"{month}%")
                ).all()
                
                if not transactions:
                    self.console.print(f"[yellow]No transactions found for {month}[/yellow]")
                    return {}
                
                # Calculate totals
                income_transactions = [t for t in transactions if t.transaction_type == TransactionType.INCOME]
                expense_transactions = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
                
                total_income = sum(t.amount for t in income_transactions)
                total_expenses = sum(t.amount for t in expense_transactions)
                net_income = total_income - total_expenses
                
                # Category breakdown using defaultdict
                category_expenses = defaultdict(float)
                category_income = defaultdict(float)
                
                for transaction in expense_transactions:
                    category_expenses[transaction.category] += transaction.amount
                
                for transaction in income_transactions:
                    category_income[transaction.category] += transaction.amount
                
                # Display report
                self.console.print(f"\n[bold magenta]--- Financial Report for {month} ---[/bold magenta]")
                self.console.print(f"[cyan]Total Income:[/cyan]   {format_currency(total_income)}")
                self.console.print(f"[red]Total Expenses:[/red] {format_currency(total_expenses)}")
                net_color = "green" if net_income >= 0 else "red"
                self.console.print(f"[{net_color}]Net Income:[/{net_color}]     {format_currency(net_income)}")
                
                if category_expenses:
                    self.console.print(f"\n[bold]--- Expenses by Category ---[/bold]")
                    sorted_expenses = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
                    for category, amount in sorted_expenses:
                        percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
                        self.console.print(f"[yellow]{category:<15}[/yellow] {format_currency(amount):>12} "
                                          f"([cyan]{format_percentage(percentage)}[/cyan])")
                
                if category_income:
                    self.console.print(f"\n[bold]--- Income by Category ---[/bold]")
                    sorted_income = sorted(category_income.items(), key=lambda x: x[1], reverse=True)
                    for category, amount in sorted_income:
                        percentage = (amount / total_income) * 100 if total_income > 0 else 0
                        self.console.print(f"[green]{category:<15}[/green] {format_currency(amount):>12} "
                                          f"([cyan]{format_percentage(percentage)}[/cyan])")
                
                # Return data as dict (using dicts as required)
                report_data = {
                    'month': month,
                    'total_income': total_income,
                    'total_expenses': total_expenses,
                    'net_income': net_income,
                    'category_expenses': dict(category_expenses),
                    'category_income': dict(category_income),
                    'transactions_count': len(transactions)
                }
                
                return report_data
                
        except Exception as e:
            self.console.print(f"[red]Error generating report: {str(e)}[/red]")
            return {}
    
    def _create_progress_bar(self, percentage: float) -> str:
        """Create a visual progress bar for Rich display."""
        filled_length = int(25 * percentage / 100)
        bar = "█" * filled_length + "░" * (25 - filled_length)
        
        if percentage >= 100:
            return f"[green]{bar}[/green] {percentage:.1f}%"
        elif percentage >= 75:
            return f"[yellow]{bar}[/yellow] {percentage:.1f}%"
        elif percentage >= 50:
            return f"[blue]{bar}[/blue] {percentage:.1f}%"
        else:
            return f"[red]{bar}[/red] {percentage:.1f}%"
    
    def add_tag(self, name: str, description: str = "", color: str = "#007bff") -> bool:
        """Add a new tag."""
        try:
            with get_db_session() as session:
                # Check if tag already exists
                existing_tag = session.query(Tag).filter_by(name=name).first()
                if existing_tag:
                    self.console.print(f"[yellow]Tag '{name}' already exists.[/yellow]")
                    return False
                
                tag = Tag(name=name, description=description, color=color)
                session.add(tag)
                self.console.print(f"[green]✓ Tag '{name}' created successfully.[/green]")
                return True
        except Exception as e:
            self.console.print(f"[red]Error adding tag: {str(e)}[/red]")
            return False
    
    def add_transaction_with_tags(self, amount: float, category: str, description: str, 
                                  transaction_type: str, tag_names: List[str] = None, 
                                  transaction_date: date = None) -> bool:
        """Add a transaction with tags."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        try:
            with get_db_session() as session:
                trans_type = TransactionType.INCOME if transaction_type.lower() == 'income' else TransactionType.EXPENSE
                
                transaction = Transaction(
                    amount=amount,
                    category=category,
                    description=description,
                    transaction_type=trans_type,
                    transaction_date=transaction_date or date.today(),
                    user_id=self.current_user_id
                )
                
                # Add tags if provided
                if tag_names:
                    for tag_name in tag_names:
                        tag = session.query(Tag).filter_by(name=tag_name).first()
                        if tag:
                            transaction.tags.append(tag)
                        else:
                            self.console.print(f"[yellow]Warning: Tag '{tag_name}' not found, skipping.[/yellow]")
                
                session.add(transaction)
                tags_str = ", ".join(tag_names) if tag_names else "none"
                self.console.print(f"[green]✓ {transaction_type.capitalize()} of {format_currency(amount)} added to {category} with tags: {tags_str}[/green]")
                return True
                
        except Exception as e:
            self.console.print(f"[red]Error adding transaction: {str(e)}[/red]")
            return False
    
    def create_user_profile(self, phone: str = "", address: str = "", occupation: str = "", 
                           annual_income: float = 0, financial_goal: str = "", 
                           risk_tolerance: str = "medium") -> bool:
        """Create or update user profile."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return False
        
        try:
            with get_db_session() as session:
                # Check if profile already exists
                existing_profile = session.query(UserProfile).filter_by(user_id=self.current_user_id).first()
                
                if existing_profile:
                    # Update existing profile
                    if phone: existing_profile.phone_number = phone
                    if address: existing_profile.address = address
                    if occupation: existing_profile.occupation = occupation
                    if annual_income: existing_profile.annual_income = annual_income
                    if financial_goal: existing_profile.financial_goal = financial_goal
                    if risk_tolerance: existing_profile.risk_tolerance = risk_tolerance
                    
                    self.console.print("[green]✓ User profile updated successfully.[/green]")
                else:
                    # Create new profile
                    profile = UserProfile(
                        user_id=self.current_user_id,
                        phone_number=phone,
                        address=address,
                        occupation=occupation,
                        annual_income=annual_income,
                        financial_goal=financial_goal,
                        risk_tolerance=risk_tolerance
                    )
                    session.add(profile)
                    self.console.print("[green]✓ User profile created successfully.[/green]")
                
                return True
        except Exception as e:
            self.console.print(f"[red]Error creating/updating profile: {str(e)}[/red]")
            return False
    
    def view_user_profile(self) -> Dict:
        """View user profile information."""
        if not self.current_user_id:
            self.console.print("[red]Error: No user logged in[/red]")
            return {}
        
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(id=self.current_user_id).first()
                profile = session.query(UserProfile).filter_by(user_id=self.current_user_id).first()
                
                if not user:
                    self.console.print("[red]User not found.[/red]")
                    return {}
                
                # Create a panel with user information
                user_info = f"""
[bold cyan]Name:[/bold cyan] {user.name}
[bold cyan]Email:[/bold cyan] {user.email}
[bold cyan]Default Currency:[/bold cyan] {user.default_currency}
[bold cyan]Monthly Income:[/bold cyan] {format_currency(user.monthly_income)}
"""
                
                if profile:
                    profile_info = f"""
[bold green]Phone:[/bold green] {profile.phone_number or 'Not set'}
[bold green]Address:[/bold green] {profile.address or 'Not set'}
[bold green]Occupation:[/bold green] {profile.occupation or 'Not set'}
[bold green]Annual Income:[/bold green] {format_currency(profile.annual_income) if profile.annual_income else 'Not set'}
[bold green]Financial Goal:[/bold green] {profile.financial_goal or 'Not set'}
[bold green]Risk Tolerance:[/bold green] {profile.risk_tolerance}
[bold green]Dark Mode:[/bold green] {'Yes' if profile.dark_mode else 'No'}
"""
                    full_info = user_info + profile_info
                else:
                    full_info = user_info + "\n[yellow]No profile information available.[/yellow]"
                
                panel = Panel(full_info, title="[bold magenta]User Profile[/bold magenta]", border_style="blue")
                self.console.print(panel)
                
                return {"user": user.to_dict(), "profile": profile.to_dict() if profile else {}}
                
        except Exception as e:
            self.console.print(f"[red]Error viewing profile: {str(e)}[/red]")
            return {}


# Click CLI Commands
@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Personal Finance Tracker & Budget Analyzer CLI
    
    A comprehensive tool for tracking income, expenses, budgets, and savings goals.
    """
    pass


@cli.command()
@click.option('--use-alembic/--no-alembic', default=True, help='Use Alembic migrations (default: True)')
def init(use_alembic):
    """Initialize the database."""
    try:
        if use_alembic:
            init_db_with_alembic()
        else:
            init_db()
        click.echo("✓ Database initialized successfully!")
    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}")


@cli.command()
@click.option('--message', '-m', prompt='Migration message', help='Description of the migration')
def create_migration(message):
    """Create a new Alembic migration."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the path to alembic.ini (go up from lib/cli.py to project root)
        # lib/cli.py -> lib -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        # Set the script location to the correct path
        migrations_path = os.path.join(project_root, "lib", "db", "migrations")
        alembic_cfg.set_main_option("script_location", migrations_path)
        
        # Create new migration
        command.revision(alembic_cfg, message=message, autogenerate=True)
        click.echo(f"✓ Migration '{message}' created successfully!")
        
    except Exception as e:
        click.echo(f"Error creating migration: {str(e)}")


@cli.command()
@click.option('--revision', default='head', help='Target revision (default: head)')
def migrate(revision):
    """Run Alembic migrations."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the path to alembic.ini (go up from lib/cli.py to project root)
        # lib/cli.py -> lib -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        # Set the script location to the correct path
        migrations_path = os.path.join(project_root, "lib", "db", "migrations")
        alembic_cfg.set_main_option("script_location", migrations_path)
        
        # Run migrations
        command.upgrade(alembic_cfg, revision)
        click.echo(f"✓ Migrations applied to {revision}!")
        
    except Exception as e:
        click.echo(f"Error running migrations: {str(e)}")


@cli.command()
def migration_history():
    """Show Alembic migration history."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the path to alembic.ini (go up from lib/cli.py to project root)
        # lib/cli.py -> lib -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        # Set the script location to the correct path
        migrations_path = os.path.join(project_root, "lib", "db", "migrations")
        alembic_cfg.set_main_option("script_location", migrations_path)
        
        # Show history
        command.history(alembic_cfg)
        
    except Exception as e:
        click.echo(f"Error showing migration history: {str(e)}")


@cli.command()
def migration_current():
    """Show current migration revision."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the path to alembic.ini (go up from lib/cli.py to project root)
        # lib/cli.py -> lib -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        # Set the script location to the correct path
        migrations_path = os.path.join(project_root, "lib", "db", "migrations")
        alembic_cfg.set_main_option("script_location", migrations_path)
        
        # Show current revision
        command.current(alembic_cfg)
        
    except Exception as e:
        click.echo(f"Error showing current revision: {str(e)}")


@cli.command()
@click.option('--name', prompt='Your name', help='Your full name')
@click.option('--email', prompt='Your email', help='Your email address')
def login(name, email):
    """Login or create a new user account."""
    # Validate inputs
    name_valid, name_result = validate_name(name)
    if not name_valid:
        click.echo(f"Error: {name_result}")
        return
    
    email_valid, email_result = validate_email(email)
    if not email_valid:
        click.echo(f"Error: {email_result}")
        return
    
    try:
        cli_app = FinanceTrackerCLI()
        user = cli_app.get_or_create_user(name_result, email_result)
        
        # Store user session (simplified for demo)
        with open('.current_user', 'w') as f:
            f.write(f"{cli_app.current_user_id},{name_result},{email_result}")
        
        click.echo("✓ Login successful!")
        
    except Exception as e:
        click.echo(f"Error during login: {str(e)}")


@cli.command()
@click.option('--amount', prompt='Amount', help='Transaction amount')
@click.option('--category', prompt='Category', help='Transaction category')
@click.option('--description', prompt='Description', help='Transaction description')
@click.option('--type', 'transaction_type', prompt='Type (income/expense)', 
              type=click.Choice(['income', 'expense']), help='Transaction type')
@click.option('--date', 'trans_date', help='Transaction date (YYYY-MM-DD)', default=None)
def add_transaction(amount, category, description, transaction_type, trans_date):
    """Add a new transaction."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    # Validate inputs
    amount_valid, amount_result = validate_amount(amount)
    if not amount_valid:
        click.echo(f"Error: {amount_result}")
        return
    
    category_valid, category_result = validate_category(category)
    if not category_valid:
        click.echo(f"Error: {category_result}")
        return
    
    desc_valid, desc_result = validate_description(description)
    if not desc_valid:
        click.echo(f"Error: {desc_result}")
        return
    
    transaction_date = None
    if trans_date:
        date_valid, date_result = validate_date(trans_date)
        if not date_valid:
            click.echo(f"Error: {date_result}")
            return
        transaction_date = date_result
    
    cli_app.add_transaction(amount_result, category_result, desc_result, 
                           transaction_type, transaction_date)


@cli.command()
@click.option('--limit', default=10, help='Number of transactions to show')
def view_transactions(limit):
    """View recent transactions."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    cli_app.view_transactions(limit)


@cli.command()
@click.option('--category', prompt='Category', help='Budget category')
@click.option('--limit', prompt='Monthly limit', help='Budget limit amount')
@click.option('--month', help='Month (YYYY-MM)', default=None)
def add_budget(category, limit, month):
    """Add or update a budget."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    # Validate inputs
    limit_valid, limit_result = validate_amount(limit)
    if not limit_valid:
        click.echo(f"Error: {limit_result}")
        return
    
    category_valid, category_result = validate_category(category)
    if not category_valid:
        click.echo(f"Error: {category_result}")
        return
    
    if month:
        month_valid, month_result = validate_month(month)
        if not month_valid:
            click.echo(f"Error: {month_result}")
            return
        month = month_result
    
    cli_app.add_budget(category_result, limit_result, month)


@cli.command()
@click.option('--month', help='Month (YYYY-MM)', default=None)
def view_budgets(month):
    """View budgets and spending."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    if month:
        month_valid, month_result = validate_month(month)
        if not month_valid:
            click.echo(f"Error: {month_result}")
            return
        month = month_result
    
    cli_app.view_budgets(month)


@cli.command()
@click.option('--name', prompt='Goal name', help='Savings goal name')
@click.option('--target', prompt='Target amount', help='Target amount to save')
@click.option('--description', help='Goal description', default='')
def add_savings_goal(name, target, description):
    """Add a new savings goal."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    # Validate inputs
    name_valid, name_result = validate_name(name)
    if not name_valid:
        click.echo(f"Error: {name_result}")
        return
    
    target_valid, target_result = validate_amount(target)
    if not target_valid:
        click.echo(f"Error: {target_result}")
        return
    
    desc_valid, desc_result = validate_description(description)
    if not desc_valid:
        click.echo(f"Error: {desc_result}")
        return
    
    cli_app.add_savings_goal(name_result, target_result, desc_result)


@cli.command()
@click.option('--name', prompt='Goal name', help='Savings goal name')
@click.option('--amount', prompt='Amount to add', help='Amount to contribute')
def update_savings_goal(name, amount):
    """Update progress on a savings goal."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    # Validate inputs
    amount_valid, amount_result = validate_amount(amount)
    if not amount_valid:
        click.echo(f"Error: {amount_result}")
        return
    
    cli_app.update_savings_goal(name, amount_result)


@cli.command()
def view_savings_goals():
    """View all savings goals."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    cli_app.view_savings_goals()


@cli.command()
@click.option('--month', help='Month (YYYY-MM)', default=None)
def generate_report(month):
    """Generate comprehensive financial report."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    if month:
        month_valid, month_result = validate_month(month)
        if not month_valid:
            click.echo(f"Error: {month_result}")
            return
        month = month_result
    
    cli_app.generate_report(month)


@cli.command()
@click.option('--name', prompt='Tag name', help='Tag name')
@click.option('--description', help='Tag description', default='')
@click.option('--color', help='Tag color (hex code)', default='#007bff')
def add_tag(name, description, color):
    """Add a new tag for transactions."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    cli_app.add_tag(name, description, color)


@cli.command()
@click.option('--amount', prompt='Amount', help='Transaction amount')
@click.option('--category', prompt='Category', help='Transaction category')
@click.option('--description', prompt='Description', help='Transaction description')
@click.option('--type', 'transaction_type', prompt='Type (income/expense)', 
              type=click.Choice(['income', 'expense']), help='Transaction type')
@click.option('--tags', help='Comma-separated tag names', default='')
@click.option('--date', 'trans_date', help='Transaction date (YYYY-MM-DD)', default=None)
def add_transaction_with_tags(amount, category, description, transaction_type, tags, trans_date):
    """Add a new transaction with tags."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    # Validate inputs
    amount_valid, amount_result = validate_amount(amount)
    if not amount_valid:
        click.echo(f"Error: {amount_result}")
        return
    
    category_valid, category_result = validate_category(category)
    if not category_valid:
        click.echo(f"Error: {category_result}")
        return
    
    desc_valid, desc_result = validate_description(description)
    if not desc_valid:
        click.echo(f"Error: {desc_result}")
        return
    
    transaction_date = None
    if trans_date:
        date_valid, date_result = validate_date(trans_date)
        if not date_valid:
            click.echo(f"Error: {date_result}")
            return
        transaction_date = date_result
    
    tag_names = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    
    cli_app.add_transaction_with_tags(amount_result, category_result, desc_result, 
                                     transaction_type, tag_names, transaction_date)


@cli.command()
@click.option('--phone', help='Phone number', default='')
@click.option('--address', help='Address', default='')
@click.option('--occupation', help='Occupation', default='')
@click.option('--annual-income', help='Annual income', type=float, default=0)
@click.option('--financial-goal', help='Financial goal', default='')
@click.option('--risk-tolerance', help='Risk tolerance', 
              type=click.Choice(['low', 'medium', 'high']), default='medium')
def create_profile(phone, address, occupation, annual_income, financial_goal, risk_tolerance):
    """Create or update user profile."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    cli_app.create_user_profile(phone, address, occupation, annual_income, 
                               financial_goal, risk_tolerance)


@cli.command()
def view_profile():
    """View user profile information."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    cli_app.view_user_profile()


@cli.command()
def interactive():
    """Start interactive mode."""
    cli_app = _get_logged_in_cli()
    if not cli_app:
        return
    
    click.echo("🏦 Personal Finance Tracker - Interactive Mode")
    click.echo("=" * 50)
    
    while True:
        click.echo("\n--- Main Menu ---")
        options = [
            "Add Transaction",
            "Add Transaction with Tags",
            "View Transactions", 
            "Add Tag",
            "Add Budget",
            "View Budgets",
            "Add Savings Goal",
            "Update Savings Goal",
            "View Savings Goals",
            "View Profile",
            "Create/Update Profile",
            "Generate Report",
            "Exit"
        ]
        
        for i, option in enumerate(options, 1):
            click.echo(f"{i}. {option}")
        
        try:
            choice = click.prompt(f"\nEnter your choice (1-{len(options)})", type=int)
            
            if choice == 1:
                _interactive_add_transaction(cli_app)
            elif choice == 2:
                _interactive_add_transaction_with_tags(cli_app)
            elif choice == 3:
                limit = click.prompt("Number of transactions to show", default=10, type=int)
                cli_app.view_transactions(limit)
            elif choice == 4:
                _interactive_add_tag(cli_app)
            elif choice == 5:
                _interactive_add_budget(cli_app)
            elif choice == 6:
                month = click.prompt("Month (YYYY-MM)", default="", show_default=False)
                cli_app.view_budgets(month if month else None)
            elif choice == 7:
                _interactive_add_savings_goal(cli_app)
            elif choice == 8:
                _interactive_update_savings_goal(cli_app)
            elif choice == 9:
                cli_app.view_savings_goals()
            elif choice == 10:
                cli_app.view_user_profile()
            elif choice == 11:
                _interactive_create_profile(cli_app)
            elif choice == 12:
                month = click.prompt("Month (YYYY-MM)", default="", show_default=False)
                cli_app.generate_report(month if month else None)
            elif choice == 13:
                click.echo("Thank you for using Personal Finance Tracker! 💰")
                break
            else:
                click.echo(f"Invalid choice. Please enter a number between 1-{len(options)}.")
                
        except (ValueError, KeyboardInterrupt):
            click.echo("\nThank you for using Personal Finance Tracker! 💰")
            break


def _get_logged_in_cli():
    """Get CLI instance with logged in user."""
    try:
        with open('.current_user', 'r') as f:
            user_data = f.read().strip().split(',')
            if len(user_data) == 3:
                cli_app = FinanceTrackerCLI()
                cli_app.current_user_id = int(user_data[0])
                return cli_app
    except FileNotFoundError:
        pass
    
    click.echo("Error: Not logged in. Please run 'python -m lib.cli login' first.")
    return None


def _interactive_add_transaction(cli_app):
    """Interactive transaction addition."""
    try:
        transaction_type = click.prompt("Type", type=click.Choice(['income', 'expense']))
        amount = click.prompt("Amount", type=str)
        category = click.prompt("Category", type=str)
        description = click.prompt("Description", type=str)
        
        # Validate
        amount_valid, amount_result = validate_amount(amount)
        if not amount_valid:
            click.echo(f"Error: {amount_result}")
            return
        
        category_valid, category_result = validate_category(category)
        if not category_valid:
            click.echo(f"Error: {category_result}")
            return
        
        desc_valid, desc_result = validate_description(description)
        if not desc_valid:
            click.echo(f"Error: {desc_result}")
            return
        
        cli_app.add_transaction(amount_result, category_result, desc_result, transaction_type)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_add_budget(cli_app):
    """Interactive budget addition."""
    try:
        category = click.prompt("Category", type=str)
        limit_amount = click.prompt("Monthly limit", type=str)
        
        # Validate
        limit_valid, limit_result = validate_amount(limit_amount)
        if not limit_valid:
            click.echo(f"Error: {limit_result}")
            return
        
        category_valid, category_result = validate_category(category)
        if not category_valid:
            click.echo(f"Error: {category_result}")
            return
        
        cli_app.add_budget(category_result, limit_result)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_add_savings_goal(cli_app):
    """Interactive savings goal addition."""
    try:
        name = click.prompt("Goal name", type=str)
        target = click.prompt("Target amount", type=str)
        description = click.prompt("Description (optional)", default="", show_default=False)
        
        # Validate
        name_valid, name_result = validate_name(name)
        if not name_valid:
            click.echo(f"Error: {name_result}")
            return
        
        target_valid, target_result = validate_amount(target)
        if not target_valid:
            click.echo(f"Error: {target_result}")
            return
        
        desc_valid, desc_result = validate_description(description)
        if not desc_valid:
            click.echo(f"Error: {desc_result}")
            return
        
        cli_app.add_savings_goal(name_result, target_result, desc_result)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_update_savings_goal(cli_app):
    """Interactive savings goal update."""
    try:
        name = click.prompt("Goal name", type=str)
        amount = click.prompt("Amount to add", type=str)
        
        # Validate
        amount_valid, amount_result = validate_amount(amount)
        if not amount_valid:
            click.echo(f"Error: {amount_result}")
            return
        
        cli_app.update_savings_goal(name, amount_result)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_add_tag(cli_app):
    """Interactive tag addition."""
    try:
        name = click.prompt("Tag name", type=str)
        description = click.prompt("Description (optional)", default="", show_default=False)
        color = click.prompt("Color (hex code)", default="#007bff", show_default=False)
        
        cli_app.add_tag(name, description, color)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_add_transaction_with_tags(cli_app):
    """Interactive transaction addition with tags."""
    try:
        transaction_type = click.prompt("Type", type=click.Choice(['income', 'expense']))
        amount = click.prompt("Amount", type=str)
        category = click.prompt("Category", type=str)
        description = click.prompt("Description", type=str)
        tags = click.prompt("Tags (comma-separated, optional)", default="", show_default=False)
        
        # Validate
        amount_valid, amount_result = validate_amount(amount)
        if not amount_valid:
            click.echo(f"Error: {amount_result}")
            return
        
        category_valid, category_result = validate_category(category)
        if not category_valid:
            click.echo(f"Error: {category_result}")
            return
        
        desc_valid, desc_result = validate_description(description)
        if not desc_valid:
            click.echo(f"Error: {desc_result}")
            return
        
        tag_names = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        cli_app.add_transaction_with_tags(amount_result, category_result, desc_result, 
                                         transaction_type, tag_names)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


def _interactive_create_profile(cli_app):
    """Interactive profile creation/update."""
    try:
        phone = click.prompt("Phone number (optional)", default="", show_default=False)
        address = click.prompt("Address (optional)", default="", show_default=False)
        occupation = click.prompt("Occupation (optional)", default="", show_default=False)
        annual_income = click.prompt("Annual income (optional)", default=0, type=float, show_default=False)
        financial_goal = click.prompt("Financial goal (optional)", default="", show_default=False)
        risk_tolerance = click.prompt("Risk tolerance", 
                                    type=click.Choice(['low', 'medium', 'high']), 
                                    default='medium')
        
        cli_app.create_user_profile(phone, address, occupation, annual_income, 
                                   financial_goal, risk_tolerance)
        
    except (ValueError, KeyboardInterrupt):
        click.echo("Operation cancelled.")


if __name__ == '__main__':
    cli()