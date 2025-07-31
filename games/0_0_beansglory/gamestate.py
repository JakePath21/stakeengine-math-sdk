import typing
from game_override import GameStateOverride
from src.events.events import update_global_mult_event

class GameState(GameStateOverride):
    """Handle basegame and three-tiered bonus logic for Beans Glory."""

    def run_spin(self, sim: int) -> None:
        """Entry point for a single spin in basegame."""
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            # 1) Evaluate base-game wins (ways-to-win)
            self.evaluate_ways_board()
            self.win_manager.update_gametype_wins(self.gametype)

            # 2) Check for bonus entry and delegate
            tier = self.check_bonus_entry()
            if tier == "regular":
                return self.run_regular_bonus()
            elif tier == "super":
                return self.run_super_bonus()
            elif tier == "mega":
                return self.run_mega_bonus()

            # 3) Finalize spin
            self.evaluate_finalwin()
            self.check_game_repeat()

        # 4) Record completed spin outcome
        self.imprint_wins()


    def run_freespin(self) -> None:
        """
        Required override of the abstract free-spin entry point.
        Delegates to our shared free-spin loop.
        """
        self._run_freegame_loop()


    def get_positions(self, symbol_name: str) -> list[dict]:
        """
        Helper to collect all positions of a given symbol on the board.
        Returns a list of dicts: {"reel": reel_idx, "row": row_idx}.
        """
        positions: list[dict] = []
        for reel_idx, reel in enumerate(self.board):
            for row_idx, sym in enumerate(reel):
                if sym.name == symbol_name:
                    positions.append({"reel": reel_idx, "row": row_idx})
        return positions


    def check_bonus_entry(self) -> typing.Optional[str]:
        """
        Determine which bonus (if any) this base-game spin qualifies for:
          • 'mega'   if ≥3 'R' anywhere AND ≥1 'M' on reel 3
          • 'super'  if ≥3 'R' anywhere AND ≥1 'S' on reel 3
          • 'regular' if ≥3 'R' anywhere (and no S/M in reel 3)
          • None     otherwise
        """
        # all 'R' positions anywhere
        regs = self.get_positions("R")
        
        # First check if we have enough scatter symbols
        if len(regs) < 3:
            return None
            
        # only 'M' or 'S' on the 3rd reel (index 2)
        mids = [p for p in self.get_positions("M") if p["reel"] == 2]
        sups = [p for p in self.get_positions("S") if p["reel"] == 2]

        # Now check for mega/super conditions
        # Both require ≥3 'R' AND their specific trigger on reel 3
        if mids and len(regs) >= 3:
            return "mega"
        if sups and len(regs) >= 3:
            return "super"
        
        # If we have ≥3 'R' but no M/S on reel 3, it's regular bonus
        return "regular"



    def run_regular_bonus(self) -> None:
        """8 spins at 2× global multiplier, plus R-scatter retriggers."""
        self.tot_fs                 = 8
        self.global_multiplier      = 2
        self.enable_expanding_wilds = False
        self._run_freegame_loop()


    def run_super_bonus(self) -> None:
        """8 spins at 2×, with per-spin expanding wilds and retriggers."""
        self.tot_fs                 = 8
        self.global_multiplier      = 2
        self.enable_expanding_wilds = True
        self.sticky_wilds           = False
        self._run_freegame_loop()


    def run_mega_bonus(self) -> None:
        """8 spins at 2×, with sticky-expanding wilds and retriggers."""
        self.tot_fs                 = 8
        self.global_multiplier      = 2
        self.enable_expanding_wilds = True
        self.sticky_wilds           = True
        self._run_freegame_loop()


    def _run_freegame_loop(self) -> None:
        """
        Core free-spin loop:
          • Temporarily switches gametype to freegame so FR0 is used
          • Emits update_freespin & update_global_mult each spin
          • Draws board, expands wilds as needed, evaluates wins
          • Handles R-scatter retriggers:
              3 R → +3 spins & +2×
              4 R → +4 spins & +5×
              5+ R → +10 spins & +10×
        """
        # stash and switch into free-spin mode
        prev_type     = self.gametype
        self.gametype = self.config.freegame_type

        # reset free-spin counter
        self.reset_fs_spin()
        if getattr(self, "sticky_wilds", False):
            self.sticky_positions = {}

        while self.fs < self.tot_fs:
            # start-of-spin events
            self.update_freespin()
            update_global_mult_event(self)
            self.draw_board(emit_event=True)

            # expanding / sticky wild logic
            if getattr(self, "enable_expanding_wilds", False):
                self._expand_wilds(sticky=getattr(self, "sticky_wilds", False))

            # win evaluation
            self.evaluate_ways_board()
            self.emit_tumble_win_events()
            self.win_manager.update_gametype_wins(self.gametype)

            # retriggers on R scatters
            scatter_R = self.get_positions("R")
            count_R   = len(scatter_R)
            if count_R >= 3:
                if count_R == 3:
                    self.tot_fs += 3
                    self.global_multiplier += 2
                elif count_R == 4:
                    self.tot_fs += 4
                    self.global_multiplier += 5
                else:  # 5 or more
                    self.tot_fs += 10
                    self.global_multiplier += 10

            # advance spin index
            self.fs += 1

        # wrap up free spins and restore original gametype
        self.end_freespin()
        self.gametype = prev_type


    def _expand_wilds(self, sticky: bool) -> None:
        """
        Expand every 'W' on the board to fill its reel.
        If sticky=True, record these reel positions so they persist next spins.
        """
        for reel_idx, reel in enumerate(self.board):
            has_wild = any(sym.name == "W" for sym in reel)
            if has_wild:
                for row_idx in range(len(reel)):
                    reel[row_idx].assign_attribute({"wild_expanded": True})
                if sticky:
                    for row_idx in range(len(reel)):
                        self.sticky_positions.setdefault(reel_idx, set()).add(row_idx)
