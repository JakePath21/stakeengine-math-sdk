# math-sdk/games/beans_glory/game_override.py

from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """
    This class is used to override or extend universal state.py functions
    for Beans Glory. Wild symbols no longer receive per-symbol multipliers;
    only the global multiplier is in play.
    """

    def reset_book(self):
        """
        Reset global book state at the start of each spin.
        """
        super().reset_book()
        # No additional per-spin fields to reset here

    def assign_special_sym_function(self):
        """
        Required override for abstract base.
        We have no per-symbol special handling, so just clear the dict.
        """
        self.special_symbol_functions = {}
    # wilds ("W") will not get individual multipliers.
    

    def check_game_repeat(self):
        """
        After a spin completes, enforce any explicit win_criteria
        defined in the current distribution. If the spin outcome
        does not meet that criterion, repeat the spin.
        """
        if not self.repeat:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
