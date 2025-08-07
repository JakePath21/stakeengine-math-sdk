import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Game specific configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "0_0_triplebonus"
        self.provider_number = 0
        self.working_name = "sample ways game"
        self.wincap = 10000
        self.win_type = "newWays"
        self.rtp = 0.97
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [3] * self.num_reels

        # Board and Symbol Properties
        self.paytable = {
            (5, "H1"): 10,
            (4, "H1"): 5,
            (3, "H1"): 3,
            (5, "H2"): 8,
            (4, "H2"): 4,
            (3, "H2"): 2,
            (5, "H3"): 5,
            (4, "H3"): 2,
            (3, "H3"): 1,
            (5, "H4"): 3,
            (4, "H4"): 1,
            (3, "H4"): 0.5,
            (5, "H5"): 2,
            (4, "H5"): 0.8,
            (3, "H5"): 0.4,
            (5, "L1"): 2,
            (4, "L1"): 0.8,
            (3, "L1"): 0.4,
            (5, "L2"): 1.5,
            (4, "L2"): 0.5,
            (3, "L2"): 0.2,
            (5, "L3"): 1.5,
            (4, "L3"): 0.5,
            (3, "L3"): 0.2,
            (5, "L4"): 1,
            (4, "L4"): 0.3,
            (3, "L4"): 0.1,
        }

        self.include_padding = True
        self.special_symbols = {
            "wild": ["W"],
            "scatter": ["R", "S", "M"],
        }

        self.freespin_triggers = {
            self.basegame_type: {3: 8, 4: 8, 5: 8},
            self.freegame_type: {2: 8, 3: 8, 4: 8, 5: 8},
        }
        self.anticipation_triggers = {
            self.basegame_type: 2,
            self.freegame_type: 2,
        }

        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "FRWCAP": "FRWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(
                os.path.join(self.reels_path, f)
            )

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=self.wincap,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_wincap": True,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                            # remove all wild multipliers → always 1×
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=0.1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                            "scatter_triggers": {3: 100, 4: 20, 5: 5},
                            # remove all wild multipliers → always 1×
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=0.4,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            # already only 1×
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.5,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "force_wincap": False,
                            "force_freegame": False,
                            # already only 1×
                            "mult_values": {1: 1},
                        },
                    ),
                ],
            ),
            BetMode(
                name="buy_regular_bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame_regular",
                        quota=1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                ],
            ),

            # Buy Super bonus (100% Super freegame)
            BetMode(
                name="buy_super_bonus",
                cost=200.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame_super",
                        quota=1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                ],
            ),

            # Buy Mega bonus (100% Mega freegame)
            BetMode(
                name="buy_mega_bonus",
                cost=500.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame_mega",
                        quota=1,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                ],
            ),

            # Buy Mystery bonus (10% Mega, 20% Super, 70% Regular)
            BetMode(
                name="buy_mystery_bonus",
                cost=200.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="mystery_mega",
                        quota=0.10,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="mystery_super",
                        quota=0.20,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                    Distribution(
                        criteria="mystery_regular",
                        quota=0.70,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FRWCAP": 5},
                            },
                            "force_freegame": True,
                            "force_wincap": False,
                            "scatter_triggers": {3: 100},  # Fallback, shouldn't be used
                            "mult_values": {1: 1},
                        },
                    ),
                ],
            ),
        ]