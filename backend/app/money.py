from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

TWOPLACES = Decimal("0.01")


def as_decimal(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid amount")
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def money_str(value):
    return f"{as_decimal(value)}"
