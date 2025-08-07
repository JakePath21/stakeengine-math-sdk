"""Game logic and event emission for standard 'ways' game with a fixed board size."""

from game_override import GameStateOverride
from src.events.events import update_global_mult_event, set_total_event

class GameState(GameStateOverride):
    """Handle basegame and freegame logic."""

    def run_spin(self, sim: int) -> None:
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()

            # BASE GAME: no emit_event (so no scatter‐forcing loop)
            self.draw_board(emit_event=True)

            # Evaluate base-game board
            self.evaluate_ways_board()
            self.win_manager.update_gametype_wins(self.gametype)

            # Check Scatter condition and trigger freegame
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def assign_special_sym_function(self):
        """
        Required abstract method stub.
        We no longer use per-symbol multipliers, so leave this empty.
        """
        self.special_symbol_functions = {}
        
    def run_freespin(self) -> None:
        # Reset free-spin counters
        self.reset_fs_spin()
        # Emit the starting global multiplier for the bonus round
        update_global_mult_event(self)

        while self.fs < self.tot_fs:
            self.update_freespin()

            # FREE SPINS: do emit_event so wins & re-triggers work
            self.draw_board(emit_event=True)

            # Evaluate the board for wins
            self.evaluate_ways_board()

            # Handle any retrigger conditions
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            # 1) Compute this spin's raw win
            self.win_manager.update_gametype_wins(self.gametype)
            raw_win = self.win

            # 2) Apply the persistent global multiplier
            bonus_win = raw_win * self.global_mult

            # 3) Store and emit the multiplied win
            self.win = bonus_win
            set_total_event(self)

        # Finish the free-spin sequence
        self.end_freespin()
