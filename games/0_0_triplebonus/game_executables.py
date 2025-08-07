from game_calculations import GameCalculations
from src.calculations.newWays import Ways
from src.events.events import fs_trigger_event, update_global_mult_event

class GameExecutables(GameCalculations):
    """Custom 'ways' logic with triple-tier bonus rounds."""

    def evaluate_ways_board(self):
        """Populate win-data, record wins, transmit events."""
        # Use the global multiplier if it exists, otherwise default to 1.0
        global_mult = getattr(self, 'global_multiplier', 1.0)
        self.win_data = Ways.get_ways_data(
            self.config, 
            self.board, 
            multiplier_strategy="global",
            global_multiplier=global_mult
        )
        if self.win_data["totalWin"] > 0:
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
        Ways.emit_wayswin_events(self)

    def run_freespin_from_base(self) -> None:
        """
        Trigger one of three bonus rounds based on scatter configuration:
          - Mega:   ≥2 R + ≥1 M on reel 3 → 8 spins @ 50×
          - Super:  ≥2 R + ≥1 S on reel 3 → 8 spins @ 10×
          - Regular:≥3 R                 → 8 spins @ 2×
        Then actually enter the free-spin loop.
        """
        # Count total R scatters on board
        regular_count = sum(
            1
            for reel in self.board
            for sym in reel
            if sym.name == "R"
        )

        # Check for S or M on the middle (3rd) reel
        reel_3 = self.board[2]
        has_super = any(sym.name == "S" for sym in reel_3)
        has_mega  = any(sym.name == "M" for sym in reel_3)

        # Decide bonus type and starting multiplier
        if regular_count >= 2 and has_mega:
            spins, mult = 8, 50
        elif regular_count >= 2 and has_super:
            spins, mult = 8, 10
        elif regular_count >= 3:
            spins, mult = 8, 2
        else:
            return  # no bonus triggered

        # Record scatter symbols for optimization program (CRITICAL for force data)
        self.record({
            "kind": regular_count,
            "symbol": "scatter",
            "gametype": self.gametype,
        })

        # Initialize free spins
        self.tot_fs       = spins
        self.remaining_fs = spins

        # Emit the free-spin trigger event
        fs_trigger_event(
            self,
            include_padding_index=True,
            basegame_trigger=True,
            freegame_trigger=False
        )

        # Set and emit the global multiplier
        self.global_mult = mult
        self.global_multiplier = mult  # Ensure compatibility with ways calculation
        update_global_mult_event(self)

        # Now actually run the free-spin loop
        self.run_freespin()
