from typing import Any, Dict
from app.tools.base import BaseTool
from app.schemas.tool import ToolMetadata
from app.repository.account import AccountRepository
from app.repository.transaction import TransactionRepository

class TransferMoneyTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="transfer_money",
            description="Transfers specified amount of money to the designated recipient.",
            input_schema={
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Name or account identifier of the recipient"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount in currency to be transferred"
                    }
                },
                "required": ["recipient", "amount"]
            },
            scopes=["banking_transfer"]
        )

    def execute(self, recipient: str, amount: float, **kwargs: Any) -> str:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")
        
        account_repo = AccountRepository()
        tx_repo = TransactionRepository()

        # John Doe (customer 1) is the source account
        src_acc = account_repo.get_by_customer_id(1, "Savings")
        if not src_acc:
            raise ValueError("Source savings account not found.")

        if src_acc["balance"] < amount:
            raise ValueError(f"Insufficient funds. Current balance: ₹{src_acc['balance']:.2f}")

        # Resolve destination account
        dest_acc = None
        if recipient.lower() in ["ravi", "ravi sharma"]:
            dest_acc = account_repo.get_by_account_number("67890")
        else:
            dest_acc = account_repo.get_by_account_number(recipient)

        if not dest_acc:
            raise ValueError(f"Recipient account or identifier '{recipient}' not found.")

        # Update balances
        new_src_bal = src_acc["balance"] - amount
        new_dest_bal = dest_acc["balance"] + amount

        account_repo.update_balance(src_acc["id"], new_src_bal)
        account_repo.update_balance(dest_acc["id"], new_dest_bal)

        # Log debit and credit transactions
        tx_repo.create_transaction(src_acc["id"], "DEBIT", amount, f"Transfer to {recipient}")
        tx_repo.create_transaction(dest_acc["id"], "CREDIT", amount, "Transfer from John Doe")

        return f"Successfully transferred ₹{amount:.2f} to {recipient}."

class CheckBalanceTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="check_balance",
            description="Retrieves current balance details for the specified account type.",
            input_schema={
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "description": "Type of account, e.g. Savings or Current",
                        "default": "Savings"
                    }
                }
            },
            scopes=["banking_info"]
        )

    def execute(self, account_type: str = "Savings", **kwargs: Any) -> str:
        account_repo = AccountRepository()
        account = account_repo.get_by_customer_id(1, account_type)
        if not account:
            return f"No account found for type: {account_type}."
        return f"Your {account_type} account balance is ₹{account['balance']:.2f}."

class GetTransactionHistoryTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_transaction_history",
            description="Fetches latest transaction history entries for user accounts.",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of transactions to retrieve",
                        "default": 5
                    }
                }
            },
            scopes=["banking_info"]
        )

    def execute(self, limit: int = 5, **kwargs: Any) -> str:
        account_repo = AccountRepository()
        tx_repo = TransactionRepository()

        # Retrieve savings account
        account = account_repo.get_by_customer_id(1, "Savings")
        if not account:
            return "No active savings account found to retrieve history."

        history = tx_repo.get_history(account["id"], limit=int(limit))
        if not history:
            return "No transaction history entries found."

        lines = []
        for idx, tx in enumerate(history, 1):
            ts = tx["timestamp"][:10]  # Show YYYY-MM-DD
            lines.append(f"{idx}. {ts}: {tx['type']} ₹{tx['amount']:.2f} - {tx['description']}")
        
        return "Recent Transactions:\n" + "\n".join(lines)
