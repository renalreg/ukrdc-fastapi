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
def test_convert_query_to_pg_like(term, expected):
    assert search._convert_query_to_pg_like(term) == expected


@pytest.mark.parametrize(
    "term,expected",
    [
        ('"term"', "term"),
        ("term", "term%"),
        ('"term', '"term%'),
        ('t"er"m', 't"er"m%'),
    ],
)
def test_convert_query_to_pg_like_double_ended(term, expected):
    assert search._convert_query_to_pg_like(term) == expected


@pytest.mark.parametrize(
    "term,expected",
    [
        ("0543754634", "0543754634"),
        ("543754634", "0543754634"),
        ("6321892009", "6321892009"),
        ("632 189 2009", "6321892009"),
        ("632-189-2009", "6321892009"),
        ("632 - 189 - 2009", "6321892009"),
        ("1234", "1234"),
        ("1234567890", "1234567890"),
    ],
)
def test_nhs_number_normalization(term, expected):
    s = search.SearchSet()
    s.add_mrn_number(term)

    assert len(s.mrn_numbers) == 1
    assert s.mrn_numbers[0] == expected
