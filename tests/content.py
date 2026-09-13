from hypothesis import HealthCheck, given, settings, strategies
from hypothesis.extra import numpy
from hypothesis.strategies import SearchStrategy

Content = dict[str, "Content"] | list["Content"] | str | int | float | bool | None

alphabet = strategies.characters(exclude_categories=("Cc", "Cs", "Zl", "Zp"))

scalars = (
    strategies.none()
    | strategies.booleans()
    | strategies.integers()
    | strategies.floats(allow_nan=False)
    | strategies.text()
)


def nesting_strategy(children: SearchStrategy[Content]) -> SearchStrategy[Content]:
    dictionaries = strategies.dictionaries(strategies.text(), children)
    return strategies.lists(children) | dictionaries


class Strategies:
    text = strategies.text(alphabet=alphabet)
    lines = strategies.lists(text)
    arrays = numpy.arrays(numpy.scalar_dtypes(), numpy.array_shapes(min_dims=0))
    serializable = strategies.recursive(scalars, nesting_strategy)


class Given:
    bytes = given(content=strategies.binary())
    text = given(content=Strategies.text)
    lines = given(content=Strategies.lines)


suppressed_health_checks = (HealthCheck.function_scoped_fixture,)
slower_test_settings = settings(
    max_examples=10,
    suppress_health_check=suppressed_health_checks,
    deadline=1000,
)
