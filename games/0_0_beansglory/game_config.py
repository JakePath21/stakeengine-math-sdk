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
        self.game_id        = "0_0_beansglory"                              
        self.provider_number= 0
        self.working_name   = "Beans Glory"                                # CHANGED: more descriptive title
        self.wincap         = 10000
        self.win_type       = "ways"                                      # pay-by-ways
        self.rtp            = 0.97                                        # target RTP
        self.construct_paths(self.game_id)

        # ——— GRID DIMENSIONS ——————————————————————————————————————————————
        self.num_reels = 5
        self.num_rows = [3] * self.num_reels  # Optionally include variable number of rows per reel

        # ——— PAYTABLE ————————————————————————————————————————————————————
        self.paytable = {
            (5, "H1"): 10, (4, "H1"): 5, (3, "H1"): 3,
            (5, "H2"): 8,  (4, "H2"): 4, (3, "H2"): 2,
            (5, "H3"): 5,  (4, "H3"): 2, (3, "H3"): 1,
            (5, "H4"): 3,  (4, "H4"): 1, (3, "H4"): 0.5,
            (5, "H5"): 2,  (4, "H5"): 0.8,(3, "H5"): 0.4,
            (5, "L1"): 2,  (4, "L1"): 0.8,(3, "L1"): 0.4,
            (5, "L2"): 1.5,(4, "L2"): 0.5,(3, "L2"): 0.2,
            (5, "L3"): 1.5,(4, "L3"): 0.5,(3, "L3"): 0.2,
            (5, "L4"): 1,  (4, "L4"): 0.3,(3, "L4"): 0.1,
        }

        # ——— SYMBOL CATEGORIES ——————————————————————————————————————————
        self.include_padding = True
        self.special_symbols = {
            "wild":            ["W"],    # unchanged: substituting wild
            "scatter_regular": ["R"],    # CHANGED: regular bonus scatter
            "scatter_super":   ["S"],    # CHANGED: super bonus scatter
            "scatter_mega":    ["M"],    # CHANGED: mega bonus scatter
        }

        #self.freespin_triggers = {
        #    self.basegame_type: {3: 10, 4: 15, 5: 20},
        #    self.freegame_type: {2: 4, 3: 6, 4: 8, 5: 10},
        #}
        # self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 1}



        # ——— REELS ——————————————————————————————————————————————————————
        reels = {
            "BR0":    "BR0.csv",
            "FR0":    "FR0.csv",
            "FRWCAP": "FRWCAP.csv",      # can be used for bonus-capitalizing strips
        }
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

            

        # ——— BET MODES & DISTRIBUTIONS ——————————————————————————————————————
        # We handle all bonus‐entry logic in GameState.check_bonus_entry(), so we clear out
        # legacy freespin_triggers/anticipation_triggers.
        # Distributions quotas must sum to 1.0 per mode.

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
                    # 2% of spins → Mega bonus (≥1 R + M on middle reel)
                    Distribution(
                        criteria="wincap",
                        quota=0.001,
                        win_criteria=self.wincap,
                        conditions={
                            # force at least 1 R and 1 M on reel-3:
                            "scatter_triggers": {"R": 1, "M": 1},
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                        },
                    ),
                    Distribution(
                        criteria="mega",
                        quota=0.02,
                        conditions={
                            # force at least 1 R and 1 M on reel-3:
                            "scatter_triggers": {"R": 1, "M": 1},
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                        },
                    ),
                    # 3% of spins → Super bonus (≥2 R + S on middle reel)
                    Distribution(
                        criteria="super",
                        quota=0.03,
                        conditions={
                            "scatter_triggers": {"R": 2, "S": 1},
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                        },
                    ),
                    # 5% of spins → Regular bonus (≥3 R anywhere)
                    Distribution(
                        criteria="regular",
                        quota=0.05,
                        conditions={
                            "scatter_triggers": {"R": 3},
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                        },
                    ),
                    # 49.9% of spins → No bonus
                    Distribution(
                        criteria="basegame",
                        quota=0.499,
                        conditions={
                            "force_wincap": False,
                            "force_freegame": False,
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
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
                        },
                    ),
                ],
            ),
            BetMode(
                name="buybonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(criteria="regular", quota=0.50, conditions={"force_freegame":True}),
                    Distribution(criteria="super",   quota=0.30, conditions={"force_freegame":True}),
                    Distribution(criteria="mega",    quota=0.20, conditions={"force_freegame":True}),
                ],
            ),
        ]
