import numpy as np
from sklearn.model_selection import ParameterGrid


def grid_color_search(evaluation_function, num_iter):
    """
    Performs a grid search over the given parameters and evaluates each
    combination using the provided function.

    Parameters
    ----------
    evaluation_function : function
        A function that takes a dictionary of parameters and returns a score.
        The function should accept a dictionary where keys are parameter names
        and values are the values for those parameters.
    num_iter : int
        The approximate total number of parameter combinations to evaluate. The
        actual number of combinations may be less than this number due to the
        discrete nature of the grid.

    Returns
    -------
    list, list
        The first list contains dictionaries of the parameter combinations. Each
        dictionary has keys corresponding to parameter names and values
        corresponding to the values for those parameters. The second list
        contains the scores for each parameter combination, in the same order as
        the first list.

    Examples
    --------
    >>> def evaluate(params):
    ...     return params['R'] + params['G'] + params['B']
    ...
    >>> parameters = {'R': [0, 255], 'G': [0, 255], 'B': [0, 255]}
    >>> grid_search(parameters, evaluate, 27)
    """
    param_grid = {}
    color_bounds = {"R": [0, 255], "G": [0, 255], "B": [0, 255]}
    num_pts_per_dim = int(np.floor(num_iter ** (1 / len(color_bounds))))
    for name, bnd in color_bounds.items():
        param_grid[name] = np.linspace(bnd[0], bnd[1], num=num_pts_per_dim)
        if isinstance(bnd[0], int):
            param_grid[name] = np.round(param_grid[name]).astype(int)

    grid = list(ParameterGrid(param_grid))

    grid_data = [
        evaluation_function(dict(R=pt["R"], G=pt["G"], B=pt["B"])) for pt in grid
    ]

    return grid, grid_data


def get_random_color(rng=np.random.default_rng(42), max_power=1.0):
    """
    Generates a random RGB color.

    Parameters
    ----------
    rng : numpy.random.Generator, optional
        A random number generator instance from numpy. If not provided, a
        default random number generator is used with a seed of 42.
    max_power : float, optional
        A scaling factor for the brightness of the color. It should be between
        0.0 and 1.0 (inclusive). The default is 1.0, which means full
        brightness. Note that (255, 255, 255) i.e., full power is very bright
        for a neopixel.

    Returns
    -------
    dict
        A dictionary with keys 'R', 'G', 'B' and their corresponding values as
        the generated random color's RGB components.

    Examples
    --------
    >>> get_random_color(rng=np.random.default_rng(42), max_power=1.0)
    {'R': 102, 'G': 220, 'B': 225}
    """
    RGB = 255 * rng.random(3) * max_power
    R, G, B = np.round(RGB).astype(int)
    return dict(R=int(R), G=int(G), B=int(B))


def random_color_search(evaluation_function, num_iter):
    """
    Performs a random search by generating random RGB colors and evaluating them
    using the provided function.

    Parameters
    ----------
    evaluation_function : function
        A function that takes a dictionary of RGB color components and returns a
        score. The function should accept a dictionary where keys are 'R', 'G',
        'B' and values are the values for those components.
    num_iter : int
        The number of random RGB colors to generate and evaluate.

    Returns
    -------
    list, list
        The first list contains dictionaries of the generated random RGB colors.
        Each dictionary has keys 'R', 'G', 'B' and values as the color
        components. The second list contains the scores for each generated
        color, in the same order as the first list.

    Examples
    --------
    >>> def evaluate(params):
    ...     return params['R'] + params['G'] + params['B']
    ...
    >>> random_search(evaluate, 5)
    """
    random_inputs = [get_random_color() for _ in range(num_iter)]
    random_data = [evaluation_function(random_inputs[i]) for i in range(num_iter)]

    return random_inputs, random_data
