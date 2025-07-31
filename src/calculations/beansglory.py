"""Ways wins executables/calculations."""

from collections import defaultdict
from src.calculations.symbol import Symbol
from src.config.config import Config
from src.wins.multiplier_strategy import apply_mult
from src.events.events import (
    win_info_event,
    set_win_event,
    set_total_event,
)


class Ways:
    """Collection of Ways-wins functions"""

    @staticmethod
    def get_ways_data(
        config: Config,
        board: list[list[Symbol]],
        *,
        wild_key: str = "wild",
        multiplier_key: str = "multiplier",
        multiplier_strategy: str = "symbol",
        global_multiplier: float = 1.0,
    ):
        """
        Ways calculation with possibility for symbol‐ or global‐multiplier application.

        Args:
          config: your GameConfig (unchanged)
          board:  current 2D Symbol grid
          wild_key: name of your wild category (defaults to "wild")
          multiplier_key: the attribute key you use for multipliers on Symbols
          multiplier_strategy: "symbol" or "global"
          global_multiplier: your GameState.global_multiplier
        """
        assert multiplier_strategy in ("symbol", "global")

        return_data = {"totalWin": 0, "wins": []}
        potential_wins = {}
        wilds = [[] for _ in range(len(board))]

        # 1) collect positions of each base symbol + all wilds
        for reel_idx, reel in enumerate(board):
            for row_idx, sym in enumerate(reel):
                # track candidate symbol‐runs
                if reel_idx == 0 and sym.name not in potential_wins:
                    potential_wins[sym.name] = [[] for _ in range(len(board))]
                    potential_wins[sym.name][0].append({"reel": reel_idx, "row": row_idx})
                elif sym.name in potential_wins:
                    potential_wins[sym.name][reel_idx].append({"reel": reel_idx, "row": row_idx})

                # track wilds (may carry per-symbol multipliers)
                if sym.name in config.special_symbols[wild_key]:
                    info = {"reel": reel_idx, "row": row_idx}
                    if sym.check_attribute(multiplier_key):
                        info[multiplier_key] = sym.get_attribute(multiplier_key)
                    wilds[reel_idx].append(info)

        # 2) for each symbol, walk reels 0→n and count ways
        for symbol, per_reel in potential_wins.items():
            kind = 0
            ways = 1
            symbol_mult_sum = 0  # sum of any symbol‐level multipliers
            for reel_idx, hits in enumerate(per_reel):
                if hits or wilds[reel_idx]:
                    kind += 1
                    # count this reel’s contributions
                    count_on_reel = 0

                    # first, symbol hits
                    has_symbol_mult = any(
                        board[p["reel"]][p["row"]].check_attribute(multiplier_key)
                        for p in hits
                    )

                    if not has_symbol_mult:
                        count_on_reel += len(hits)
                    else:
                        # symbol‐multipliers on this reel
                        for p in hits:
                            s = board[p["reel"]][p["row"]]
                            if s.check_attribute(multiplier_key) and multiplier_strategy == "symbol":
                                val = s.get_attribute(multiplier_key)
                                count_on_reel += val
                                symbol_mult_sum += max(val - 1, 0)
                            else:
                                count_on_reel += 1

                    # then wilds
                    for w in wilds[reel_idx]:
                        wsym = board[w["reel"]][w["row"]]
                        if wsym.check_attribute(multiplier_key):
                            val = wsym.get_attribute(multiplier_key)
                            if multiplier_strategy == "symbol":
                                count_on_reel += val
                                symbol_mult_sum += max(val - 1, 0)
                            else:
                                count_on_reel += 1
                        else:
                            count_on_reel += 1

                    ways *= count_on_reel
                else:
                    break

            # only pay if we have a valid paytable entry
            if (kind, symbol) in config.paytable:
                # collect all positions
                positions = []
                for r in range(kind):
                    positions += potential_wins[symbol][r]
                    positions += wilds[r]

                base_win = round(config.paytable[kind, symbol] * ways, 2)
                # now apply either symbol OR global strategy
                win_amt, used_mult = apply_mult(
                    board=board,
                    strategy=multiplier_strategy,
                    win_amount=base_win,
                    global_multiplier=global_multiplier,
                )
                return_data["wins"].append({
                    "symbol": symbol,
                    "kind": kind,
                    "win": win_amt,
                    "positions": positions,
                    "meta": {
                        "ways": ways,
                        "globalMult": used_mult,
                        "winWithoutMult": base_win,
                        "symbolMult": symbol_mult_sum,
                    }
                })
                return_data["totalWin"] += win_amt

        return return_data

    @staticmethod
    def emit_wayswin_events(gamestate) -> None:
        """Transmit win events associated with ways wins."""
        if gamestate.win_manager.spin_win > 0:
            win_info_event(gamestate)
            gamestate.evaluate_wincap()
            set_win_event(gamestate)
        set_total_event(gamestate)

    @staticmethod
    def record_ways_wins(gamestate) -> None:
        """Record Ways type wins."""
        for win in gamestate.win_data["wins"]:
            gamestate.record({
                "kind": len(win["positions"]),
                "symbol": win["symbol"],
                "ways": win["meta"]["ways"],
                "gametype": gamestate.gametype,
            })
