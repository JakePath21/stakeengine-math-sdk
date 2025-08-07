from game_executables import GameExecutables

class GameStateOverride(GameExecutables):
    """
    This class is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def reset_book(self):
        # Reset global values used across multiple projects
        super().reset_book()
        # Clear any leftover global multiplier before a new spin
        self.global_mult = 1

    def assign_special_sym_function(self):
        """
        Stub out per-symbol multiplier assignment:
        we no longer use symbol-level multipliers in this game.
        """
        self.special_symbol_functions = {}

    def check_game_repeat(self):
        """Verify final simulation outcomes satisfied all distribution/criteria conditions."""
        if not self.repeat:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
