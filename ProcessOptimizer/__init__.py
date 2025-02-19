"""
`ProcessOptimizer`, is a simple and efficient library to minimize (very)
expensive and noisy black-box functions. It implements several methods for
sequential model-based optimization. `ProcessOptimizer` is reusable in many
contexts and accessible.

## Install

pip install ProcessOptimizer

## Development

The library is still experimental and under heavy development.

"""

from . import acquisition
from .model_systems import benchmarks
from . import callbacks
from . import learning
from . import optimizer

from . import space
from .optimizer import dummy_minimize
from .optimizer import forest_minimize
from .optimizer import gbrt_minimize
from .optimizer import gp_minimize
from .optimizer import Optimizer
from .searchcv import BayesSearchCV
from .space import Space, space_factory
from .utils import dump
from .utils import expected_minimum
from .utils import expected_minimum_random_sampling
from .utils import load
from .utils import cook_estimator, create_result, y_coverage
from .plots import plot_objective, plot_objectives
from .plots import plot_evaluations, plot_convergence
from .plots import plot_Pareto, plot_expected_minimum_convergence

__version__ = "0.8.1"


__all__ = (
    "acquisition",
    "benchmarks",
    "callbacks",
    "learning",
    "optimizer",
    "plots",
    "space",
    "gp_minimize",
    "dummy_minimize",
    "forest_minimize",
    "gbrt_minimize",
    "Optimizer",
    "dump",
    "load",
    "cook_estimator",
    "create_result",
    "expected_minimum",
    "expected_minimum_random_sampling",
    "BayesSearchCV",
    "Space",
    "space_factory",
    "plot_objective",
    "plot_objectives",
    "plot_evaluations",
    "plot_convergence",
    "plot_Pareto",
    "y_coverage",
    "plot_expected_minimum_convergence"
)
