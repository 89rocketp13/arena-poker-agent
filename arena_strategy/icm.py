from __future__ import annotations


def icm_equities(stacks: list[int], payouts: list[float]) -> list[float]:
    if not stacks:
        return []
    if len(payouts) > len(stacks):
        raise ValueError("Cannot have more payouts than players")
    if any(stack < 0 for stack in stacks):
        raise ValueError("Stacks cannot be negative")

    memo: dict[tuple[tuple[int, ...], tuple[float, ...]], tuple[float, ...]] = {}

    def recurse(active_stacks: tuple[int, ...], remaining_payouts: tuple[float, ...]) -> tuple[float, ...]:
        key = (active_stacks, remaining_payouts)
        if key in memo:
            return memo[key]
        n = len(active_stacks)
        if n == 0 or not remaining_payouts:
            return tuple(0.0 for _ in range(n))
        total = sum(active_stacks)
        if total <= 0:
            return tuple(remaining_payouts[0] / n for _ in range(n))

        equities = [0.0 for _ in range(n)]
        for winner_idx, stack in enumerate(active_stacks):
            probability = stack / total
            equities[winner_idx] += probability * remaining_payouts[0]
            next_stacks = active_stacks[:winner_idx] + active_stacks[winner_idx + 1 :]
            child = recurse(next_stacks, remaining_payouts[1:])
            child_cursor = 0
            for idx in range(n):
                if idx == winner_idx:
                    continue
                equities[idx] += probability * child[child_cursor]
                child_cursor += 1
        memo[key] = tuple(equities)
        return memo[key]

    return list(recurse(tuple(stacks), tuple(payouts)))


def bubble_factor(current_stack: int, stacks: list[int], payouts: list[float], loss_amount: int, win_amount: int) -> float:
    if current_stack <= 0:
        return float("inf")
    before = icm_equities(stacks, payouts)[0]
    lose_stacks = [max(current_stack - loss_amount, 0), *stacks[1:]]
    win_stacks = [current_stack + win_amount, *stacks[1:]]
    downside = before - icm_equities(lose_stacks, payouts)[0]
    upside = icm_equities(win_stacks, payouts)[0] - before
    return float("inf") if upside <= 0 else downside / upside

