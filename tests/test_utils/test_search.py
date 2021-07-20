import pytest

from ukrdc_fastapi.utils.search import masterrecords as search


@pytest.mark.parametrize(
    "term,expected",
    [
        ('"term"', True),
        ("term", False),
        ('"term', False),
        ('term"', False),
        ('t"er"m', False),
    ],
)
def test_term_is_exact(term, expected):
    assert search._term_is_exact(term) == expected


@pytest.mark.parametrize(
    "term,expected",
    [
        ('"term"', "term"),
        ("term", "term%"),
        ('"term', '"term%'),
        ('t"er"m', 't"er"m%'),
    ],
)
def test_convert_query_to_ilike(term, expected):
    assert search._convert_query_to_ilike(term) == expected


@pytest.mark.parametrize(
    "term,expected",
    [
        ('"term"', "term"),
        ("term", "%term%"),
        ('"term', '%"term%'),
        ('t"er"m', '%t"er"m%'),
    ],
)
def test_convert_query_to_ilike_double_ended(term, expected):
    assert search._convert_query_to_ilike(term, double_ended=True) == expected


@pytest.mark.parametrize(
    "term,expected",
    [
        ("0543754634", "0543754634"),
        ("543754634", "0543754634"),
        ("6321892009", "6321892009"),
        ("632 189 2009", "6321892009"),
        ("632-189-2009", "6321892009"),
        ("632 - 189 - 2009", "6321892009"),
        ("1234", None),
        ("1234567890", None),
    ],
)
def test_implicit_nhs_number(term, expected):
    s = search.SearchSet()
    s.add_nhs_number(term)

    if expected:
        assert len(s.nhs_numbers) == 1
        assert s.nhs_numbers[0] == expected
    else:
        assert len(s.nhs_numbers) == 0
