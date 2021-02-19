"""Test cases for nhs_numbers.py file."""

from ukrdc_fastapi.utils.nhs import (
    OrganizationType,
    get_organization,
    normalise_number,
    valid_number,
)


def test_get_organization_works_with_ints():
    assert OrganizationType.CHI == get_organization(1111111111)
    assert OrganizationType.CHI == get_organization(410690351)
    assert OrganizationType.HSC == get_organization(3235930892)
    assert OrganizationType.NHS == get_organization(6477633973)


def test_get_organization_works_with_strings():
    assert OrganizationType.CHI == get_organization("1111111111")
    assert OrganizationType.CHI == get_organization("410690351")
    assert OrganizationType.HSC == get_organization("3235930892")
    assert OrganizationType.NHS == get_organization("6477633973")


def test_get_organization_returns_unk_on_empty_or_invalid():
    assert OrganizationType.UNK == get_organization("")
    assert OrganizationType.UNK == get_organization("12345")


def test_valid_number_validates_valid_numbers():
    assert valid_number(1111111111, OrganizationType.CHI) == True
    assert valid_number(3235930892, OrganizationType.HSC) == True
    assert valid_number(6477633973, OrganizationType.NHS) == True
    assert valid_number(204222923, OrganizationType.CHI) == True

    assert valid_number("1111111111", OrganizationType.CHI) == True
    assert valid_number("3235930892", OrganizationType.HSC) == True
    assert valid_number("6477633973", OrganizationType.NHS) == True
    assert valid_number("204222923", OrganizationType.CHI) == True


def test_valid_number_returns_false_invalid_numbers():
    assert valid_number(1111111112, OrganizationType.CHI) == False
    assert valid_number(3235930893, OrganizationType.HSC) == False
    assert valid_number(6477633974, OrganizationType.NHS) == False
    assert valid_number(204222922, OrganizationType.CHI) == False
    assert valid_number("1111111112", OrganizationType.CHI) == False
    assert valid_number("3235930893", OrganizationType.HSC) == False
    assert valid_number("6477633974", OrganizationType.NHS) == False
    assert valid_number("204222922", OrganizationType.CHI) == False


def test_valid_number_unknown_organization_numbers_are_valid():
    assert valid_number(1234, None) == True
    assert valid_number(1234, OrganizationType.UNK) == True
    assert valid_number(None, OrganizationType.UNK) == True
    assert valid_number("", OrganizationType.UNK) == True
    assert valid_number("", None) == True


def test_normalise_number_returns_unchanged_if_valid_given():
    assert normalise_number("1111111111") == "1111111111"


def test_normalise_number_strips_spaces_dashes():
    assert normalise_number("111-111-1111") == "1111111111"
    assert normalise_number("111 111 1111") == "1111111111"


def test_normalise_number_pads_zero_on_nine_char():
    assert normalise_number("111111111") == "0111111111"
