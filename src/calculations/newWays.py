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
        wild_key: str = "wild",
        multiplier_key="multiplier",
        multiplier_strategy="symbol",
    ):
        """Ways calculation with possibility for global multiplier application."""
        return_data = {
            "totalWin": 0,
            "wins": [],
        }
        assert multiplier_strategy in ["symbol", "global"]
        global_mult_count = 0
        potential_wins = defaultdict()
        wilds = [[] for _ in range(len(board))]

        for reel, _ in enumerate(board):
            for row, _ in enumerate(board[reel]):
                sym = board[reel][row]

                # Build potential win paths
                if reel == 0 and sym.name not in potential_wins:
                    potential_wins[sym.name] = [[] for _ in range(len(board))]
                    potential_wins[sym.name][0] = [{"reel": reel, "row": row}]
                elif sym.name in potential_wins:
                    potential_wins[sym.name][reel].append({"reel": reel, "row": row})

                # Track wilds (and their multipliers)
                if sym.name in config.special_symbols[wild_key]:
                    wilds[reel].append({"reel": reel, "row": row})
                    if sym.check_attribute(multiplier_key):
                        wilds[reel][-1][multiplier_key] = sym.get_attribute(multiplier_key)

        for symbol, paths in potential_wins.items():
            kind = 0
            ways = 1
            cumulative_sym_mult = 0

            for reel_idx, positions in enumerate(paths):
                reel_has_symbol = len(positions) > 0
                reel_has_wild   = len(wilds[reel_idx]) > 0

                if not (reel_has_symbol or reel_has_wild):
                    break

                kind += 1
                # Count symbols/wilds with multipliers
                reel_sym_count = 0
                symbols_have_mult = any(
                    board[p["reel"]][p["row"]].check_attribute(multiplier_key)
                    for p in positions
                )

                if not symbols_have_mult:
                    reel_sym_count += len(positions)
                else:
                    for p in positions:
                        sym_at = board[p["reel"]][p["row"]]
                        if sym_at.check_attribute(multiplier_key) and multiplier_strategy == "symbol":
                            reel_sym_count += sym_at.get_attribute(multiplier_key)
                        else:
                            reel_sym_count += 1
                            if sym_at.check_attribute(multiplier_key) and multiplier_strategy == "global":
                                gm = sym_at.get_attribute(multiplier_key)
                                global_mult_count += (gm - 1)

                # Include wilds
                if reel_has_wild:
                    for w in wilds[reel_idx]:
                        sym_at = board[w["reel"]][w["row"]]
                        if sym_at.check_attribute(multiplier_key):
                            wm = sym_at.get_attribute(multiplier_key)
                            cumulative_sym_mult += (wm - 1)
                            if multiplier_strategy == "global":
                                reel_sym_count += 1
                                global_mult_count += (wm - 1)
                            else:
                                reel_sym_count += wm
                        else:
                            reel_sym_count += 1

                ways *= reel_sym_count

            # Calculate wins if we have a paytable entry
            if (kind, symbol) in config.paytable:
                positions = []
                for r in range(kind):
                    positions += potential_wins[symbol][r]
                    positions += wilds[r]

                base_win = round(config.paytable[kind, symbol] * ways, 2)
                win_amt, multiplier = apply_mult(
                    board=board,
                    strategy="global",
                    win_amount=base_win,
                    global_multiplier=(global_mult_count if multiplier_strategy == "global" else 1),
                )

                return_data["wins"].append({
                    "symbol": symbol,
                    "kind": kind,
                    "win": win_amt,
                    "positions": positions,
                    "meta": {
                        "ways": ways,
                        "globalMult": multiplier,
                        "winWithoutMult": base_win,
                        "symbolMult": cumulative_sym_mult,
                    },
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
                "kind":   len(win["positions"]),
                "symbol": win["symbol"],
                "ways":   win["meta"]["ways"],
                "gametype": gamestate.gametype,
            })
