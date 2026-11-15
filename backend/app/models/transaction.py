from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.money import money_str
from app.timeutil import iso, utcnow


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "txn_type IN ('deposit', 'withdrawal')",
            name="ck_transactions_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    txn_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    account: Mapped["BankAccount"] = relationship(back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "account_number": self.account.account_number if self.account else None,
            "user_id": self.user_id,
            "txn_type": self.txn_type,
            "amount": money_str(self.amount),
            "balance_after": money_str(self.balance_after),
            "description": self.description,
            "created_at": iso(self.created_at),
        }
