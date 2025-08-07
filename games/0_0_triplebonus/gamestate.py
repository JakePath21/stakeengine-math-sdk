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

            # Check if this is a buy bonus mode
            if hasattr(self, 'betmode') and self.betmode.startswith('buy_'):
                # For buy bonus modes, skip base game and go straight to bonus
                self.handle_buy_bonus()
            else:
                # BASE GAME: normal flow
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

    def handle_buy_bonus(self) -> None:
        """Handle buy bonus modes that skip base game."""
        # Determine which bonus type based on betmode
        if self.betmode == 'buy_regular_bonus':
            spins, mult = 8, 2
        elif self.betmode == 'buy_super_bonus':
            spins, mult = 8, 10
        elif self.betmode == 'buy_mega_bonus':
            spins, mult = 8, 50
        elif self.betmode == 'buy_mystery_bonus':
            # Random bonus type for mystery
            import random
            bonus_types = [(8, 2), (8, 10), (8, 50)]
            spins, mult = random.choice(bonus_types)
        else:
            return  # Unknown buy bonus type
            
        # Set up the bonus round
        self.tot_fs = spins
        self.remaining_fs = spins
        self.global_mult = mult
        self.global_multiplier = mult
        
        # Initialize special_syms_on_board as empty for buy modes
        self.special_syms_on_board = {"scatter": []}
        
        # Emit events for the bonus start
        from src.events.events import fs_trigger_event, update_global_mult_event
        fs_trigger_event(
            self,
            include_padding_index=True,
            basegame_trigger=False,  # Not triggered from base game
            freegame_trigger=True
        )
        update_global_mult_event(self)
        
        # Run the bonus round
        self.run_freespin()

    def assign_special_sym_function(self):
        """
        Required abstract method stub.
        We no longer use per-symbol multipliers, so leave this empty.
        """
        self.special_symbol_functions = {}

    @property
    def win(self):
        """Map self.win to self.win_manager.spin_win for compatibility."""
        return self.win_manager.spin_win

    @win.setter
    def win(self, value):
        """Allow setting win value through win_manager."""
        self.win_manager.set_spin_win(value)
        
    def run_freespin(self) -> None:
        # Reset free-spin counters
        self.reset_fs_spin()
        
        # Use 'global_multiplier' to match the ways calculation expectations
        if not hasattr(self, 'global_multiplier'):
            self.global_multiplier = getattr(self, 'global_mult', 1.0)
            
        # Emit the starting global multiplier for the bonus round
        update_global_mult_event(self)

        while self.fs < self.tot_fs:
            self.update_freespin()

            # FREE SPINS: do emit_event so wins & re-triggers work
            self.draw_board(emit_event=True)

            # Evaluate the board for wins (global multiplier is applied internally)
            self.evaluate_ways_board()

            # Handle any retrigger conditions
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            # Update gametype wins (no manual multiplier application needed)
            self.win_manager.update_gametype_wins(self.gametype)
            
            # Emit total event for this spin
            set_total_event(self)

        # Finish the free-spin sequence
        self.end_freespin()
