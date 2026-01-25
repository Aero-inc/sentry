import math
from pathlib import Path

def is_danger_scenario(file_path: str, threshold: float = 0.05) -> bool:
    
    text = Path(file_path).read_text(encoding="utf-8").strip().splitlines()

    humans = []
    guns = []

    for line in text:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 3:
            continue

        cls = int(float(parts[0]))
        x = float(parts[1])
        y = float(parts[2])

        if cls == 0:
            humans.append((x, y))
        elif cls == 1:
            guns.append((x, y))

    if not humans or not guns:
        return False

    # Early exit: the moment we find a dangerous pair
    for hx, hy in humans:
        for gx, gy in guns:
            if math.hypot(hx - gx, hy - gy) < threshold:
                return True

    return False


if __name__ == "__main__":
    print(is_danger_scenario("sample.txt"))