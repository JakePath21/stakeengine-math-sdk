# math-sdk/games/beans_glory/game_optimization.py

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    verify_optimization_input,
)


class OptimizationSetup:
    """Game specific optimization setup for Beans Glory."""

    def __init__(self, game_config):
        self.game_config = game_config

        # --- OPTIMIZATION PARAMETERS ------------------------------------------------
        # We must supply one entry per Distribution(criteria) used in GameConfig.
        # Quotas themselves live in GameConfig; here we describe the desired
        # RTP contribution, hit‐rate, and search targets for each criterion.
        self.game_config.opt_params = {
            "base": {
                # Each key here must match a Distribution(criteria) in your base BetMode:
                "conditions": {
                    # 0.1% max‐win‐cap spins
                    "wincap": ConstructConditions(
                        rtp=0.001,              # ~0.1% of total RTP
                        av_win=self.game_config.wincap,
                        search_conditions=self.game_config.wincap
                    ).return_dict(),

                    # 2% Mega bonus
                    "mega": ConstructConditions(
                        rtp=0.019,             # ~1.9% of RTP
                        hr=0.02,               # ~2% hit‐rate
                        search_conditions={"symbol": "M"}
                    ).return_dict(),

                    # 3% Super bonus
                    "super": ConstructConditions(
                        rtp=0.036,             # ~3.6% of RTP
                        hr=0.03,
                        search_conditions={"symbol": "S"}
                    ).return_dict(),

                    # 5% Regular bonus
                    "regular": ConstructConditions(
                        rtp=0.095,             # ~9.5% of RTP
                        hr=0.05,
                        search_conditions={"symbol": "R"}
                    ).return_dict(),

                    # 40% pure losers
                    "0": ConstructConditions(
                        rtp=0.0,
                        av_win=0,
                        search_conditions=0
                    ).return_dict(),

                    # Remaining ~89.9% other base‐game wins
                    "basegame": ConstructConditions(
                        rtp=0.85,              # adjust so all conditions sum to ~0.97
                        hr=0.60                # ~60% of spins have some base‐game win
                    ).return_dict(),
                },

                # You can tweak these scaling rules to emphasize
                # particular win‐ranges in base vs. freegame.
                "scaling": ConstructScaling(
                    [
                        {
                            "criteria": "basegame",
                            "scale_factor": 1.2,
                            "win_range": (1, 2),
                            "probability": 1.0,
                        },
                        {
                            "criteria": "basegame",
                            "scale_factor": 1.5,
                            "win_range": (10, 20),
                            "probability": 1.0,
                        },
                        # (You can remove the freegame entries here if you prefer
                        # to only scale in your bonus section below.)
                    ]
                ).return_dict(),

                # Simulation parameters for the optimizer.
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },

            "bonus": {
                # This maps to your `buybonus` BetMode:
                "conditions": {
                    "regular": ConstructConditions(
                        rtp=0.50,     # target ~50% RTP inside regular bonus
                        hr=0.30,      # ~30% of bonus spins retrigger or win big
                        search_conditions={"symbol": "R"}
                    ).return_dict(),
                    "super": ConstructConditions(
                        rtp=0.70,
                        hr=0.20,
                        search_conditions={"symbol": "S"}
                    ).return_dict(),
                    "mega": ConstructConditions(
                        rtp=0.90,
                        hr=0.10,
                        search_conditions={"symbol": "M"}
                    ).return_dict(),
                },
                "scaling": ConstructScaling(
                    [
                        {
                            "criteria": "freegame",
                            "scale_factor": 0.8,
                            "win_range": (500, 1000),
                            "probability": 1.0,
                        },
                        {
                            "criteria": "freegame",
                            "scale_factor": 1.2,
                            "win_range": (2000, 4000),
                            "probability": 1.0,
                        },
                    ]
                ).return_dict(),
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    min_m2m=4,
                    max_m2m=8,
                    pmb_rtp=1.0,
                    sim_trials=5000,
                    test_spins=[10, 20, 50],
                    test_weights=[0.6, 0.2, 0.2],
                    score_type="rtp",
                ).return_dict(),
            },
        }

        # Validate that our conditions cover every Distribution(criteria) we configured
        verify_optimization_input(self.game_config, self.game_config.opt_params)
