"""Deterministic payment for the bounded fictional gameplay contract.

This module plans payment only.  It neither generates mana nor chooses a
strategic action, and it never interprets card text.
"""

from collections.abc import Mapping, Sequence

from .errors import GameplayContractError
from .models import PaymentResult


def _integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GameplayContractError("invalid_payment", f"{label} must be a nonnegative integer")
    return value


def _amounts(value, label):
    if not isinstance(value, Mapping):
        raise GameplayContractError("invalid_payment", f"{label} must be a mana mapping")
    result = {}
    for key, amount in value.items():
        if not isinstance(key, str) or not key:
            raise GameplayContractError("invalid_payment", "mana symbols must be nonempty strings")
        result[key] = _integer(amount, label)
    return result


def plan_mana_payment(cost, pool, symbol_order, payment=None):
    """Return an immutable payment result without changing the supplied pool.

    Colored requirements are reserved first.  Generic payment then follows the
    explicit rules-snapshot order, or the caller's exact (non-overpaying) plan.
    Unsupported cost forms and unknown costs are never silently discarded.
    """
    if not isinstance(cost, Mapping) or set(cost) != {"kind", "generic", "colored", "known", "unsupported"}:
        raise GameplayContractError("invalid_cost", "cost must use the explicit mana-cost contract")
    if not isinstance(cost["kind"], str) or not cost["kind"]:
        raise GameplayContractError("invalid_cost", "cost kind must be a nonempty string")
    if not isinstance(cost["known"], bool):
        raise GameplayContractError("invalid_cost", "cost known state must be a boolean")
    generic = _integer(cost["generic"], "generic cost")
    colored = _amounts(cost["colored"], "colored cost")
    if not isinstance(cost["unsupported"], (list, tuple)) or any(not isinstance(item, str) or not item for item in cost["unsupported"]):
        raise GameplayContractError("invalid_cost", "unsupported cost forms must be explicit strings")
    if not isinstance(symbol_order, Sequence) or isinstance(symbol_order, (str, bytes)):
        raise GameplayContractError("invalid_payment_policy", "payment order must be an explicit sequence")
    order = tuple(symbol_order)
    if not order or any(not isinstance(symbol, str) or not symbol for symbol in order) or len(set(order)) != len(order):
        raise GameplayContractError("invalid_payment_policy", "payment order must have unique mana symbols")
    before = _amounts(pool, "mana pool")
    proposed = None if payment is None else _amounts(payment, "payment plan")
    if proposed is not None and set(proposed) - set(order):
        raise GameplayContractError("invalid_payment", "payment plan contains an unsupported mana symbol")
    normalized_cost = {"kind": cost["kind"], "generic": generic, "colored": colored, "known": cost["known"], "unsupported": list(cost["unsupported"])}

    def result(status, *, paid=None, after=None, failed=(), unknown=(), unsupported=()):
        return PaymentResult.create({
            "status": status,
            "cost": normalized_cost,
            "pool_before": before,
            "payment": {} if paid is None else paid,
            "pool_after": before if after is None else after,
            "failed_requirements": list(failed),
            "unknown_requirements": list(unknown),
            "unsupported_dimensions": list(unsupported),
        })

    unsupported = list(cost["unsupported"])
    if cost["kind"] != "mana":
        unsupported.append("cost_kind:" + cost["kind"])
    unsupported.extend("mana_symbol:" + item for item in sorted((set(colored) | set(before)) - set(order)))
    if unsupported:
        return result("UNSUPPORTED", unsupported=sorted(set(unsupported)))
    if not cost["known"]:
        return result("INDETERMINATE", unknown=("mana_cost_unknown",))
    if proposed is None:
        remaining = dict(before)
        paid = {}
        for symbol in order:
            amount = colored.get(symbol, 0)
            if amount > remaining.get(symbol, 0):
                return result("ILLEGAL", failed=("insufficient_colored_mana",))
            if amount:
                paid[symbol] = amount
                remaining[symbol] = remaining.get(symbol, 0) - amount
        generic_left = generic
        for symbol in order:
            amount = min(generic_left, remaining.get(symbol, 0))
            if amount:
                paid[symbol] = paid.get(symbol, 0) + amount
                remaining[symbol] -= amount
                generic_left -= amount
        if generic_left:
            return result("ILLEGAL", failed=("insufficient_generic_mana",))
    else:
        paid = {symbol: amount for symbol, amount in proposed.items() if amount}
        if any(amount > before.get(symbol, 0) for symbol, amount in paid.items()):
            return result("ILLEGAL", failed=("payment_exceeds_available_mana",))
        if any(paid.get(symbol, 0) < amount for symbol, amount in colored.items()):
            return result("ILLEGAL", failed=("payment_missing_colored_mana",))
        if sum(paid.values()) != generic + sum(colored.values()):
            return result("ILLEGAL", failed=("payment_not_exact",))
        remaining = {symbol: amount - paid.get(symbol, 0) for symbol, amount in before.items()}
    return result("LEGAL", paid=paid, after=remaining)
