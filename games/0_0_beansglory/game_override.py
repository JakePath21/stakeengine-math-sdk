from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome


class GameStateOverride(GameExecutables):
    """
    Override or extend universal state functions with game-specific behavior:
    - reset per-spin values
    - assign random multipliers to wilds
    - enforce Distribution(criteria) by repeating spins until they match
    """

    def reset_book(self):
        # Call base reset (clears book, event lists, etc.)
        super().reset_book()
        # Add any Beans Glory–specific resets here (e.g. clearing sticky maps)
        # e.g. self.sticky_positions = {}

    def assign_special_sym_function(self):
        # Hook the wild ("W") symbol so assign_mult_property runs on each W
        self.special_symbol_functions = {
            "W": [self.assign_mult_property],
        }

    def assign_mult_property(self, symbol):
        """
        Assign a multiplier attribute to a Wild symbol based on the current distribution's
        "mult_values" condition.
        """
        mult_vals = self.get_current_distribution_conditions()["mult_values"]
        multiplier_value = get_random_outcome(mult_vals)
        symbol.assign_attribute({"multiplier": multiplier_value})

    def check_game_repeat(self):
        """
        Enforce that the spin outcome matches the Distribution(criteria):
          - 'wincap': final_win must equal config.wincap
          - 'mega'  : spin must have qualified for mega bonus
          - 'super' : spin must have qualified for super bonus
          - 'regular': spin must have qualified for regular bonus
          - '0'     : must be a pure losing spin (win == 0, no bonus)
          - 'basegame': any non-bonus, non-wincap spin
        Otherwise, set self.repeat = True to retry the spin.
        """
        crit       = self.get_current_distribution().criteria
        bonus_tier = self.check_bonus_entry()
        win_amt    = self.win_manager.running_bet_win

        if crit == "wincap":
            # require maximum win
            if round(self.final_win, 5) != round(self.config.wincap, 5):
                self.repeat = True

        elif crit == "mega":
            # require mega bonus entry
            if bonus_tier != "mega":
                self.repeat = True

        elif crit == "super":
            # require super bonus entry
            if bonus_tier != "super":
                self.repeat = True

        elif crit == "regular":
            # require regular bonus entry
            if bonus_tier != "regular":
                self.repeat = True

        elif crit == "0":
            # require no win and no bonus
            if win_amt > 0 or bonus_tier is not None:
                self.repeat = True

        elif crit == "basegame":
            # require no bonus entry
            if bonus_tier is not None:
                self.repeat = True

        # any other criteria fall through without forcing a repeat
