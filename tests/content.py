from hypothesis import given, strategies


def text_dictionary_strategy():
    return strategies.dictionaries(keys=strategies.text(), values=strategies.text())


def dictionary_strategy():
    return strategies.dictionaries(
        keys=strategies.text(),
        values=text_dictionary_strategy(),
    )


def text_strategy(**kwargs):
    alphabet = strategies.characters(blacklist_categories=("Cc", "Cs", "Zs"), **kwargs)
    return strategies.text(alphabet=alphabet)


dictionary_content = given(content=dictionary_strategy())
byte_content = given(content=strategies.binary())
text_content = given(content=text_strategy())
text_lines_content = given(content=strategies.lists(text_strategy()))
floats_content = given(content=strategies.lists(strategies.floats()))
