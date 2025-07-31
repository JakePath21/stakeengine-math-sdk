import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Game specific configuration for Beans Glory."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()

        # ——— IDENTIFIERS & METADATA ——————————————————————————————————————————
        self.game_id         = "0_0_beansglory"
        self.provider_number = 0
        self.working_name    = "Beans Glory"
        self.wincap          = 10000
        self.win_type        = "beansglory"
        self.rtp             = 0.97
        self.construct_paths()

        # ——— GRID DIMENSIONS ——————————————————————————————————————————————
        self.num_reels = 5
        self.num_rows  = [3] * self.num_reels

        # ——— PAYTABLE ————————————————————————————————————————————————————
        self.paytable = {
            (5, "H1"): 10,   (4, "H1"): 5,   (3, "H1"): 3,
            (5, "H2"): 8,    (4, "H2"): 4,   (3, "H2"): 2,
            (5, "H3"): 5,    (4, "H3"): 2,   (3, "H3"): 1,
            (5, "H4"): 3,    (4, "H4"): 1,   (3, "H4"): 0.5,
            (5, "H5"): 2,    (4, "H5"): 0.8, (3, "H5"): 0.4,
            (5, "L1"): 2,    (4, "L1"): 0.8, (3, "L1"): 0.4,
            (5, "L2"): 1.5,  (4, "L2"): 0.5, (3, "L2"): 0.2,
            (5, "L3"): 1.5,  (4, "L3"): 0.5, (3, "L3"): 0.2,
            (5, "L4"): 1,    (4, "L4"): 0.3, (3, "L4"): 0.1,
        }

        # ——— SYMBOL CATEGORIES ——————————————————————————————————————————
        self.include_padding = True
        self.special_symbols = {
            "wild":            ["W"],
            "scatter":         ["R", "S", "M"],
            "scatter_regular": ["R"],
            "scatter_super":   ["S"],
            "scatter_mega":    ["M"],
        }

        # ensure these keys exist even if our own logic doesn’t use them
        self.freespin_triggers = {
            self.basegame_type: {999: 0},
            self.freegame_type: {999: 0},
        }
        self.anticipation_triggers = {
            self.basegame_type: -1,
            self.freegame_type: -1,
        }

        # ——— REELS ——————————————————————————————————————————————————————
        reels = {
            "BR0":    "BR0.csv",
            "FR0":    "FR0.csv",
            "FRWCAP": "FRWCAP.csv",
        }
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        # ——— BET MODES & DISTRIBUTIONS ——————————————————————————————————————
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
                    # 0.1% max-win cap
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=self.wincap,
                        conditions={
                            "force_wincap": True,
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                    # 2% Mega
                    Distribution(
                        criteria="mega",
                        quota=0.02,
                        conditions={
                            "scatter_triggers": {"R": 1, "M": 1},
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                    # 3% Super
                    Distribution(
                        criteria="super",
                        quota=0.03,
                        conditions={
                            "scatter_triggers": {"R": 2, "S": 1},
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                    # 5% Regular
                    Distribution(
                        criteria="regular",
                        quota=0.05,
                        conditions={
                            "scatter_triggers": {"R": 3},
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                    # 40% Zero‐win losers
                    Distribution(
                        criteria="0",
                        quota=0.40,
                        win_criteria=0.0,
                        conditions={
                            "force_wincap":   False,
                            "force_freegame": False,
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                    # 54.9% Other base‐game wins
                    Distribution(
                        criteria="basegame",
                        quota=0.549,
                        conditions={
                            "force_freegame": False,
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "mult_values": {self.basegame_type: {1: 1}},
                        },
                    ),
                ],
            ),
        ]
