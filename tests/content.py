from typing import Final

from hypothesis import HealthCheck, given, settings, strategies

blacklist_categories: Final = ("Cc", "Cs", "Zs")
alphabet = strategies.characters(blacklist_categories=blacklist_categories)
dictionary_strategy = strategies.dictionaries(
    keys=strategies.text(),
    values=strategies.text(),
)


class Strategies:
    text = strategies.text(alphabet=alphabet)
    lines = strategies.lists(text)
    floats = strategies.lists(strategies.floats())
    dictionaries = strategies.dictionaries(
        keys=strategies.text(),
        values=dictionary_strategy,
    )


class Given:
    bytes = given(content=strategies.binary())
    text = given(content=Strategies.text)
    lines = given(content=Strategies.lines)
    floats = given(content=Strategies.floats)
    dictionaries = given(content=Strategies.dictionaries)


suppressed_health_checks = (HealthCheck.function_scoped_fixture,)
slower_test_settings = settings(
    max_examples=10,
    suppress_health_check=suppressed_health_checks,
    deadline=1000,
)
