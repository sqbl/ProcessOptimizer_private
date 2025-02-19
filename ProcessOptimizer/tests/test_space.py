import pytest
import numbers
import numpy as np
import os
from tempfile import NamedTemporaryFile

from numpy.testing import assert_array_almost_equal
from numpy.testing import assert_array_equal
from numpy.testing import assert_equal
from numpy.testing import assert_raises_regex

from ProcessOptimizer import Optimizer
from ProcessOptimizer.space import Space
from ProcessOptimizer.space import Real
from ProcessOptimizer.space import Integer
from ProcessOptimizer.space import Categorical
from ProcessOptimizer.space import check_dimension as space_check_dimension
from ProcessOptimizer.space import space_factory


def check_dimension(Dimension, vals, random_val):
    x = Dimension(*vals)
    assert_equal(x, Dimension(*vals))
    assert x != Dimension(vals[0], vals[1] + 1)
    assert x != Dimension(vals[0] + 1, vals[1])
    assert_equal(x.rvs(random_state=1), random_val)


def check_categorical(vals, random_val):
    x = Categorical(vals)
    assert_equal(x, Categorical(vals))
    assert x != Categorical(vals[:-1] + ("zzz",))
    assert_equal(x.rvs(random_state=1), random_val)


def check_limits(value, low, high):
    # check if low <= value <= high
    assert low <= value
    assert high >= value

def test_space_factory():
    dimension_definition = [(1,5),(1.0,5.0),("a","b")]
    test_space = space_factory(dimension_definition)
    assert isinstance(test_space, Space)
    unchanging_space = Space(dimension_definition)
    unchanged_space = space_factory(unchanging_space)
    assert unchanging_space == unchanged_space

@pytest.mark.fast_test
def test_dimensions():
    check_dimension(Real, (1.0, 4.0), 2.251066014107722)
    check_dimension(Real, (1, 4), 2.251066014107722)
    check_dimension(Integer, (1, 4), 2)
    check_dimension(Integer, (1.0, 4.0), 2)
    check_categorical(("a", "b", "c", "d"), "b")
    check_categorical((1.0, 2.0, 3.0, 4.0), 2.0)


@pytest.mark.fast_test
def test_real_log_sampling_in_bounds():
    dim = Real(low=1, high=32, prior="log-uniform", transform="normalize")

    # round trip a value that is within the bounds of the space
    #
    # x = dim.inverse_transform(dim.transform(31.999999999999999))
    for n in (32.0, 31.999999999999999):
        round_tripped = dim.inverse_transform(dim.transform([n]))
        assert np.allclose([n], round_tripped)
        assert n in dim
        assert round_tripped in dim


@pytest.mark.fast_test
def test_real():
    a = Real(1, 25)
    for i in range(50):
        r = a.rvs(random_state=i)
        check_limits(r, 1, 25)
        assert r in a

    random_values = a.rvs(random_state=0, n_samples=10)
    assert_array_equal(random_values.shape, (10))
    assert_array_equal(a.transform(random_values), random_values)
    assert_array_equal(a.inverse_transform(random_values), random_values)

    log_uniform = Real(10 ** -5, 10 ** 5, prior="log-uniform")
    assert log_uniform != Real(10 ** -5, 10 ** 5)
    for i in range(50):
        random_val = log_uniform.rvs(random_state=i)
        check_limits(random_val, 10 ** -5, 10 ** 5)
    random_values = log_uniform.rvs(random_state=0, n_samples=10)
    assert_array_equal(random_values.shape, (10))
    transformed_vals = log_uniform.transform(random_values)
    assert_array_equal(transformed_vals, np.log10(random_values))
    assert_array_almost_equal(
        log_uniform.inverse_transform(transformed_vals), random_values
    )


@pytest.mark.fast_test
def test_real_bounds():
    # should give same answer as using check_limits() but this is easier
    # to read
    a = Real(1.0, 2.1)
    assert 0.99 not in a
    assert 1.0 in a
    assert 2.09 in a
    assert 2.1 in a
    assert np.nextafter(2.1, 3.0) not in a


@pytest.mark.fast_test
def test_integer():
    a = Integer(1, 10)
    for i in range(50):
        r = a.rvs(random_state=i)
        assert 1 <= r
        assert 11 >= r
        assert r in a

    random_values = a.rvs(random_state=0, n_samples=10)
    assert_array_equal(random_values.shape, (10))
    assert_array_equal(a.transform(random_values), random_values)
    assert_array_equal(a.inverse_transform(random_values), random_values)


@pytest.mark.fast_test
def test_categorical_transform():
    categories = ["apple", "orange", "banana", None, True, False, 3]
    cat = Categorical(categories)

    apple = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    orange = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    banana = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    none = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    true = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    false = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    three = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]

    assert_equal(cat.transformed_size, 7)
    assert_equal(cat.transformed_size, cat.transform(["apple"]).size)
    assert_array_equal(
        cat.transform(categories),
        [apple, orange, banana, none, true, false, three],
    )
    assert_array_equal(cat.transform(["apple", "orange"]), [apple, orange])
    assert_array_equal(cat.transform(["apple", "banana"]), [apple, banana])
    assert_array_equal(
        cat.inverse_transform([apple, orange]), ["apple", "orange"]
    )
    assert_array_equal(
        cat.inverse_transform([apple, banana]), ["apple", "banana"]
    )
    ent_inverse = cat.inverse_transform(
        [apple, orange, banana, none, true, false, three]
    )
    assert_array_equal(ent_inverse, categories)


@pytest.mark.fast_test
def test_categorical_transform_binary():
    categories = ["apple", "orange"]
    cat = Categorical(categories)

    apple = [0.0]
    orange = [1.0]

    assert_equal(cat.transformed_size, 1)
    assert_equal(cat.transformed_size, cat.transform(["apple"]).size)
    assert_array_equal(cat.transform(categories), [apple, orange])
    assert_array_equal(cat.transform(["apple", "orange"]), [apple, orange])
    assert_array_equal(
        cat.inverse_transform([apple, orange]), ["apple", "orange"]
    )
    ent_inverse = cat.inverse_transform([apple, orange])
    assert_array_equal(ent_inverse, categories)


@pytest.mark.fast_test
def test_categorical_repr():
    small_cat = Categorical([1, 2, 3, 4, 5])
    assert (
        small_cat.__repr__()
        == "Categorical(categories=(1, 2, 3, 4, 5), prior=None)"
    )

    big_cat = Categorical([1, 2, 3, 4, 5, 6, 7, 8])
    assert (
        big_cat.__repr__()
        == "Categorical(categories=(1, 2, 3, ..., 6, 7, 8), prior=None)"
    )


@pytest.mark.fast_test
def test_space_consistency():
    # Reals (uniform)

    s1 = Space([Real(0.0, 1.0)])
    s2 = Space([Real(0.0, 1.0)])
    s3 = Space([Real(0, 1)])
    s4 = Space([(0.0, 1.0)])
    s5 = Space([(0.0, 1.0, "uniform")])
    s6 = Space([(0, 1.0)])
    s7 = Space([(np.float64(0.0), 1.0)])
    s8 = Space([(0, np.float64(1.0))])
    a1 = s1.rvs(n_samples=10, random_state=0)
    a2 = s2.rvs(n_samples=10, random_state=0)
    a3 = s3.rvs(n_samples=10, random_state=0)
    a4 = s4.rvs(n_samples=10, random_state=0)
    a5 = s5.rvs(n_samples=10, random_state=0)
    assert_equal(s1, s2)
    assert_equal(s1, s3)
    assert_equal(s1, s4)
    assert_equal(s1, s5)
    assert_equal(s1, s6)
    assert_equal(s1, s7)
    assert_equal(s1, s8)
    assert_array_equal(a1, a2)
    assert_array_equal(a1, a3)
    assert_array_equal(a1, a4)
    assert_array_equal(a1, a5)

    # Reals (log-uniform)
    s1 = Space([Real(10 ** -3.0, 10 ** 3.0, prior="log-uniform")])
    s2 = Space([Real(10 ** -3.0, 10 ** 3.0, prior="log-uniform")])
    s3 = Space([Real(10 ** -3, 10 ** 3, prior="log-uniform")])
    s4 = Space([(10 ** -3.0, 10 ** 3.0, "log-uniform")])
    s5 = Space([(np.float64(10 ** -3.0), 10 ** 3.0, "log-uniform")])
    a1 = s1.rvs(n_samples=10, random_state=0)
    a2 = s2.rvs(n_samples=10, random_state=0)
    a3 = s3.rvs(n_samples=10, random_state=0)
    a4 = s4.rvs(n_samples=10, random_state=0)
    assert_equal(s1, s2)
    assert_equal(s1, s3)
    assert_equal(s1, s4)
    assert_equal(s1, s5)
    assert_array_equal(a1, a2)
    assert_array_equal(a1, a3)
    assert_array_equal(a1, a4)

    # Integers
    s1 = Space([Integer(1, 5)])
    s2 = Space([Integer(1.0, 5.0)])
    s3 = Space([(1, 5)])
    s4 = Space([(np.int64(1.0), 5)])
    s5 = Space([(1, np.int64(5.0))])
    a1 = s1.rvs(n_samples=10, random_state=0)
    a2 = s2.rvs(n_samples=10, random_state=0)
    a3 = s3.rvs(n_samples=10, random_state=0)
    assert_equal(s1, s2)
    assert_equal(s1, s3)
    assert_equal(s1, s4)
    assert_equal(s1, s5)
    assert_array_equal(a1, a2)
    assert_array_equal(a1, a3)

    # Categoricals
    s1 = Space([Categorical(["a", "b", "c"])])
    s2 = Space([Categorical(["a", "b", "c"])])
    s3 = Space([["a", "b", "c"]])
    a1 = s1.rvs(n_samples=10, random_state=0)
    a2 = s2.rvs(n_samples=10, random_state=0)
    a3 = s3.rvs(n_samples=10, random_state=0)
    assert_equal(s1, s2)
    assert_array_equal(a1, a2)
    assert_equal(s1, s3)
    assert_array_equal(a1, a3)

    s1 = Space([(True, False)])
    s2 = Space([Categorical([True, False])])
    s3 = Space([np.array([True, False])])
    assert s1 == s2 == s3


@pytest.mark.fast_test
def test_space_api():
    space = Space(
        [
            (0.0, 1.0),
            (-5, 5),
            ("a", "b", "c"),
            (1.0, 5.0, "log-uniform"),
            ("e", "f"),
        ]
    )

    cat_space = Space([(1, "r"), (1.0, "r")])
    assert isinstance(cat_space.dimensions[0], Categorical)
    assert isinstance(cat_space.dimensions[1], Categorical)

    assert_equal(len(space.dimensions), 5)
    assert isinstance(space.dimensions[0], Real)
    assert isinstance(space.dimensions[1], Integer)
    assert isinstance(space.dimensions[2], Categorical)
    assert isinstance(space.dimensions[3], Real)
    assert isinstance(space.dimensions[4], Categorical)

    samples = space.rvs(n_samples=10, random_state=0)
    assert_equal(len(samples), 10)
    assert_equal(len(samples[0]), 5)

    assert isinstance(samples, list)
    for n in range(4):
        assert isinstance(samples[n], list)

    assert isinstance(samples[0][0], numbers.Real)
    assert isinstance(samples[0][1], numbers.Integral)
    assert isinstance(samples[0][2], str)
    assert isinstance(samples[0][3], numbers.Real)
    assert isinstance(samples[0][4], str)

    samples_transformed = space.transform(samples)
    assert_equal(samples_transformed.shape[0], len(samples))
    assert_equal(samples_transformed.shape[1], 1 + 1 + 3 + 1 + 1)

    # our space contains mixed types, this means we can't use
    # `array_allclose` or similar to check points are close after a round-trip
    # of transformations
    for orig, round_trip in zip(
        samples, space.inverse_transform(samples_transformed)
    ):
        assert space.distance(orig, round_trip) < 1.0e-8

    samples = space.inverse_transform(samples_transformed)
    assert isinstance(samples[0][0], numbers.Real)
    assert isinstance(samples[0][1], numbers.Integral)
    assert isinstance(samples[0][2], str)
    assert isinstance(samples[0][3], numbers.Real)
    assert isinstance(samples[0][4], str)

    for b1, b2 in zip(
        space.bounds,
        [
            (0.0, 1.0),
            (-5, 5),
            np.asarray(["a", "b", "c"]),
            (1.0, 5.0),
            np.asarray(["e", "f"]),
        ],
    ):
        assert_array_equal(b1, b2)

    for b1, b2 in zip(
        space.transformed_bounds,
        [
            (0.0, 1.0),
            (-5, 5),
            (0.0, 1.0),
            (0.0, 1.0),
            (0.0, 1.0),
            (np.log10(1.0), np.log10(5.0)),
            (0.0, 1.0),
        ],
    ):
        assert_array_equal(b1, b2)


@pytest.mark.fast_test
def test_space_from_space():
    # can you pass a Space instance to the Space constructor?
    space = Space(
        [
            (0.0, 1.0),
            (-5, 5),
            ("a", "b", "c"),
            (1.0, 5.0, "log-uniform"),
            ("e", "f"),
        ]
    )

    space2 = Space(space)

    assert_equal(space, space2)


@pytest.mark.fast_test
def test_normalize():
    a = Real(2.0, 30.0, transform="normalize")
    for i in range(50):
        check_limits(a.rvs(random_state=i), 2, 30)

    rng = np.random.RandomState(0)
    X = rng.randn(100)
    X = 28 * (X - X.min()) / (X.max() - X.min()) + 2

    # Check transformed values are in [0, 1]
    assert np.all(a.transform(X) <= np.ones_like(X))
    assert np.all(np.zeros_like(X) <= a.transform(X))

    # Check inverse transform
    assert_array_almost_equal(a.inverse_transform(a.transform(X)), X)

    # log-uniform prior
    a = Real(10 ** 2.0, 10 ** 4.0, prior="log-uniform", transform="normalize")
    for i in range(50):
        check_limits(a.rvs(random_state=i), 10 ** 2, 10 ** 4)

    rng = np.random.RandomState(0)
    X = np.clip(10 ** 3 * rng.randn(100), 10 ** 2.0, 10 ** 4.0)

    # Check transform
    assert np.all(a.transform(X) <= np.ones_like(X))
    assert np.all(np.zeros_like(X) <= a.transform(X))

    # Check inverse transform
    assert_array_almost_equal(a.inverse_transform(a.transform(X)), X)

    a = Integer(2, 30, transform="normalize")
    for i in range(50):
        check_limits(a.rvs(random_state=i), 2, 30)
    assert_array_equal(a.transformed_bounds, (0, 1))

    X = rng.randint(2, 31, dtype=np.int64)
    # Check transformed values are in [0, 1]
    assert np.all(a.transform(X) <= np.ones_like(X))
    assert np.all(np.zeros_like(X) <= a.transform(X))

    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.int64)
    assert_array_equal(X_orig, X)

    a = Integer(2, 30, transform="normalize")
    X = rng.randint(2, 31)
    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.int64)

    a = Integer(2, 30, transform="normalize")
    X = rng.randint(2, 31)
    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.int64)

    a = Integer(2, 30, transform="normalize")
    for i in range(50):
        check_limits(a.rvs(random_state=i), 2, 30)
    assert_array_equal(a.transformed_bounds, (0, 1))

    X = rng.randint(2, 31, dtype=int)
    # Check transformed values are in [0, 1]
    assert np.all(a.transform(X) <= np.ones_like(X))
    assert np.all(np.zeros_like(X) <= a.transform(X))

    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.int64)
    assert_array_equal(X_orig, X)

    a = Real(0, 1, transform="normalize")
    for i in range(50):
        check_limits(a.rvs(random_state=i), 0, 1)
    assert_array_equal(a.transformed_bounds, (0, 1))

    X = rng.rand()
    # Check transformed values are in [0, 1]
    assert np.all(a.transform(X) <= np.ones_like(X))
    assert np.all(np.zeros_like(X) <= a.transform(X))

    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, float)
    assert_array_equal(X_orig, X)

    a = Real(0, 1, transform="normalize")
    X = np.float64(rng.rand())
    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.float64)

    a = Real(0, 1, transform="normalize")
    X = np.float64(rng.rand())
    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.float64)

    a = Real(0, 1, transform="normalize")
    X = np.float64(rng.rand())
    # Check inverse transform
    X_orig = a.inverse_transform(a.transform(X))
    assert isinstance(X_orig, np.float64)


def check_valid_transformation(klass):
    assert klass(2, 30, transform="normalize")
    assert klass(2, 30, transform="identity")
    assert_raises_regex(
        ValueError,
        "should be 'normalize' or 'identity'",
        klass,
        2,
        30,
        transform="not a valid transform name",
    )


@pytest.mark.fast_test
def test_valid_transformation():
    check_valid_transformation(Integer)
    check_valid_transformation(Real)


@pytest.mark.fast_test
def test_invalid_dimension():
    assert_raises_regex(
        ValueError, "has to be a list or tuple", space_check_dimension, "23"
    )
    # single value fixes dimension of space
    space_check_dimension((23,))


@pytest.mark.fast_test
def test_categorical_identity():
    categories = ["cat", "dog", "rat"]
    cat = Categorical(categories, transform="identity")
    samples = cat.rvs(100)
    assert all([t in categories for t in cat.rvs(100)])
    transformed = cat.transform(samples)
    assert_array_equal(transformed, samples)
    assert_array_equal(samples, cat.inverse_transform(transformed))


@pytest.mark.fast_test
def test_categorical_distance():
    categories = ["car", "dog", "orange"]
    cat = Categorical(categories)
    for cat1 in categories:
        for cat2 in categories:
            delta = cat.distance(cat1, cat2)
            if cat1 == cat2:
                assert delta == 0
            else:
                assert delta == 1


@pytest.mark.fast_test
def test_integer_distance():
    ints = Integer(1, 10)
    for i in range(1, 10 + 1):
        assert_equal(ints.distance(4, i), abs(4 - i))


@pytest.mark.fast_test
def test_integer_distance_out_of_range():
    ints = Integer(1, 10)
    assert_raises_regex(
        RuntimeError,
        "compute distance for values within",
        ints.distance,
        11,
        10,
    )


@pytest.mark.fast_test
def test_real_distance_out_of_range():
    ints = Real(1, 10)
    assert_raises_regex(
        RuntimeError,
        "compute distance for values within",
        ints.distance,
        11,
        10,
    )


@pytest.mark.fast_test
def test_real_distance():
    reals = Real(1, 10)
    for i in range(1, 10 + 1):
        assert_equal(reals.distance(4.1234, i), abs(4.1234 - i))


@pytest.mark.parametrize(
    "dimension, bounds",
    [(Real, (2, 1)), (Integer, (2, 1)), (Real, (2, 2)), (Integer, (2, 2))],
)
def test_dimension_bounds(dimension, bounds):
    with pytest.raises(ValueError) as exc:
        dim = dimension(*bounds)
        assert "has to be less than the upper bound " in exc.value.args[0]


@pytest.mark.parametrize(
    "dimension, name",
    [
        (Real(1, 2, name="learning rate"), "learning rate"),
        (Integer(1, 100, name="no of trees"), "no of trees"),
        (Categorical(["red, blue"], name="colors"), "colors"),
    ],
)
def test_dimension_name(dimension, name):
    assert dimension.name == name


@pytest.mark.parametrize(
    "dimension", [Real(1, 2), Integer(1, 100), Categorical(["red, blue"])]
)
def test_dimension_name_none(dimension):
    assert dimension.name is None


@pytest.mark.fast_test
def test_space_from_yaml():
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(
            b"""
        Space:
            - Real:
                low: 0.0
                high: 1.0
            - Integer:
                low: -5
                high: 5
            - Categorical:
                categories:
                - a
                - b
                - c
            - Real:
                low: 1.0
                high: 5.0
                prior: log-uniform
            - Categorical:
                categories:
                - e
                - f
        """
        )
        tmp.flush()

        space = Space(
            [
                (0.0, 1.0),
                (-5, 5),
                ("a", "b", "c"),
                (1.0, 5.0, "log-uniform"),
                ("e", "f"),
            ]
        )

        space2 = Space.from_yaml(tmp.name)
        assert_equal(space, space2)
        tmp.close()
        os.unlink(tmp.name)


@pytest.mark.parametrize("name", [1, 1.0, True])
def test_dimension_with_invalid_names(name):
    with pytest.raises(ValueError) as exc:
        Real(1, 2, name=name)
    assert (
        "Dimension's name must be either string or None." == exc.value.args[0]
    )


@pytest.mark.fast_test
def test_purely_categorical_space():
    # Test reproduces the bug in #908, make sure it doesn't come back
    dims = [Categorical(["a", "b", "c"]), Categorical(["A", "B", "C"])]

    with pytest.raises(
        ValueError,
        match="GaussianProcessRegressor on a purely categorical space"
        " is not supported. Please use another base estimator",
    ):
        opt = Optimizer(dims, n_initial_points=2, random_state=3)
        # assert(Optimizer(dims, n_initial_points=2, random_state=3) == "GaussianProcessRegressor on a purely categorical space"
        # " is not supported. Please use another base estimator")


# =============================================================================
#     for _ in range(2):
#         x = optimizer.ask()
#         # before the fix this call raised an exception
#         optimizer.tell(x, np.random.uniform())
# =============================================================================


@pytest.mark.fast_test
def test_lhs_arange():
    # Test that the latin hypercube sampling functions run normally
    dim_cat = Categorical(["a", "b", "c"])
    dim_cat.lhs_arange(10)
    dim_int = Integer(-10, 20)
    lhs_int = dim_int.lhs_arange(10)
    dim_real = Real(-10, 20)
    lhs_real = dim_real.lhs_arange(10)
    # Test that the Integer and Real classes return identical points after
    # rounding, using Numpy's allclose function
    assert np.allclose(lhs_int, lhs_real, atol=0.5)
    # Test that the Integer class returns values that are ints for all intents 
    # and purposes
    assert all([np.mod(x,1) == 0 for x in lhs_int])
    # Test that the Real class returns flots in all locations
    assert all([isinstance(x,np.float64) for x in lhs_real])


@pytest.mark.fast_test
def test_lhs():
    SPACE = Space(
        [Integer(-20, 20), Real(-10.5, 100), Categorical(list("abc"))]
    )
    samples = SPACE.lhs(10)
    assert len(samples) == 10
    assert len(samples[0]) == 3

