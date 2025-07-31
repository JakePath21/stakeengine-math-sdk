import csv, os

def fix_reel(path, fallback="L4"):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            # only allow S/M in the middle column (index 2)
            for col in (0, 1, 3, 4):
                if row[col] in ("S", "M"):
                    row[col] = fallback
            rows.append(row)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

if __name__ == "__main__":
    base = os.path.join("games", "0_0_beansglory", "reels")
    for fn in ("BR0.csv", "FR0.csv", "FRWCAP.csv"):
        path = os.path.join(base, fn)
        print(f"> Patching {path}")
        fix_reel(path)
    print("✅ Reels updated!")
