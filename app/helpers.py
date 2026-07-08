import math
import random


def _generate_forecast(base_mg: float) -> list[dict]:
    result = []
    for i in range(24):
        base = base_mg + math.sin(i / 3) * 18 + i * 1.6
        noise = (math.sin(i * 1.7) + math.cos(i * 0.9)) * 5
        result.append({
            "hour": f"{i}:00",
            "actual": round(base + noise) if i < 10 else None,
            "forecast": round(base + noise + ((i - 10) * 2.5 if i >= 10 else 0)),
            "upper": round(base + noise + ((i - 10) * 4 + 12 if i >= 10 else 10)),
            "lower": round(base + noise - (6 if i >= 10 else 8)),
        })
    return result


def _alert_history(seed: int, pattern: str = "default") -> list[dict]:
    rng = random.Random(seed)
    if pattern == "low":
        return [{"day": i + 1, "count": max(0, round(math.sin(i / 4) * 1.5 + (2 if i > 20 else 0.5) + rng.random()))} for i in range(30)]
    if pattern == "minimal":
        return [{"day": i + 1, "count": max(0, round(math.sin(i / 5) * 1 + 0.3 + rng.random() * 0.5))} for i in range(30)]
    return [{"day": i + 1, "count": max(0, round(math.sin(i / 3) * 2 + (3 if i > 22 else 1) + rng.random()))} for i in range(30)]
