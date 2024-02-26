from typing import Any

from hypothesis import HealthCheck, given, settings, strategies
from hypothesis.strategies import SearchStrategy


def text_dictionary_strategy() -> SearchStrategy[dict[str, str]]:
    return strategies.dictionaries(keys=strategies.text(), values=strategies.text())


def dictionary_strategy() -> SearchStrategy[dict[str, dict[str, str]]]:
    return strategies.dictionaries(
        keys=strategies.text(),
        values=text_dictionary_strategy(),
    )


def text_strategy(
    blacklist_characters: str | None = None, **kwargs: Any
) -> SearchStrategy[str]:
    alphabet = strategies.characters(
        blacklist_categories=["Cc", "Cs", "Zs"],
        blacklist_characters=blacklist_characters,
    )
    return strategies.text(alphabet=alphabet, **kwargs)


dictionary_content = given(content=dictionary_strategy())
byte_content = given(content=strategies.binary())
text_content = given(content=text_strategy())
text_lines_content = given(content=strategies.lists(text_strategy()))
floats_content = given(content=strategies.lists(strategies.floats()))

suppressed_health_checks = (HealthCheck.function_scoped_fixture,)
slower_test_settings = settings(
    max_examples=10, suppress_health_check=suppressed_health_checks, deadline=1000
)
