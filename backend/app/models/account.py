from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.money import money_str
from app.timeutil import iso, utcnow


class BankAccount(db.Model):
    __tablename__ = "bank_accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    holder_name: Mapped[str] = mapped_column(String(80), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")

    def to_dict(self, include_owner=False):
        payload = {
            "id": self.id,
            "account_number": self.account_number,
            "holder_name": self.holder_name,
            "balance": money_str(self.balance),
            "is_active": self.is_active,
            "created_at": iso(self.created_at),
            "user_id": self.user_id,
        }
        if include_owner and self.owner is not None:
            payload["owner"] = self.owner.username
            payload["owner_email"] = self.owner.email
        return payload
