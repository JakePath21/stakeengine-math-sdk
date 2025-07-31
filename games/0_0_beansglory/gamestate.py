import typing
from game_override import GameStateOverride


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


    def check_bonus_entry(self) -> typing.Optional[str]:
        """
        Determine which bonus (if any) this base-game spin qualifies for:
          • 'mega'  if ≥1 'R' + 'M' on reel 3
          • 'super' if ≥2 'R' + 'S' on reel 3
          • 'regular' if ≥3 'R' anywhere
          • None otherwise
        """
        regs  = self.get_positions("R")
        mids  = [p for p in self.get_positions("M") if p["reel"] == 2]
        sups  = [p for p in self.get_positions("S") if p["reel"] == 2]

        if len(regs) >= 3 and mids:
            # Mega has both R count and M on reel 3
            return "mega"
        if len(regs) >= 2 and sups:
            # Super has 2+ R + S on reel 3
            return "super"
        if len(regs) >= 3:
            # Regular needs 3+ R anywhere
            return "regular"
        return None


    def run_regular_bonus(self) -> None:
        """8 spins at 2× global multiplier, plus R-scatter retriggers."""
        self.tot_fs           = 8
        self.global_multiplier= 2
        # no expanding or sticky wilds here
        self.enable_expanding_wilds = False
        self._run_freegame_loop()


    def run_super_bonus(self) -> None:
        """8 spins at 2×, with per-spin expanding wilds and retriggers."""
        self.tot_fs           = 8
        self.global_multiplier= 2
        self.enable_expanding_wilds = True
        self.sticky_wilds     = False  # resets each spin
        self._run_freegame_loop()


    def run_mega_bonus(self) -> None:
        """8 spins at 2×, with sticky-expanding wilds and retriggers."""
        self.tot_fs           = 8
        self.global_multiplier= 2
        self.enable_expanding_wilds = True
        self.sticky_wilds     = True   # carry expansions across spins
        self._run_freegame_loop()


    def _run_freegame_loop(self) -> None:
        """
        Core free-spin loop:
          • Emits update_freespin & update_global_mult each spin
          • Draws board, expands wilds as needed, evaluates wins
          • Handles R-scatter retriggers: 
              3 R -> +3 spins & +2×, 
              4 R -> +4 spins & +5×, 
              5+ R -> +10 spins & +10×
        """
        self.reset_fs_spin()
        # persistent sticky map if needed
        if getattr(self, "sticky_wilds", False):
            self.sticky_positions = {}

        while self.fs < self.tot_fs:
            # start-of-spin events
            self.update_freespin()       # free-spin counter event
            self.emit_global_mult_event()# reflect current global_multiplier
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

        # finish free spins
        self.end_freespin()


    def _expand_wilds(self, sticky: bool) -> None:
        """
        Expand every 'W' on the board to fill its reel.
        If sticky=True, record these reel positions so they persist next spins.
        """
        for reel_idx, reel in enumerate(self.board):
            has_wild = any(sym.name == "W" for sym in reel)
            if has_wild:
                # explode reel
                for row_idx in range(len(reel)):
                    reel[row_idx].assign_attribute({"wild_expanded": True})
                # if sticky, remember for future spins
                if sticky:
                    self.sticky_positions.setdefault(reel_idx, set()).add(row_idx)
