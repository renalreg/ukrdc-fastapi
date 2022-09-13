from ukrdc_fastapi.config import configuration


async def test_codes_list(client):
    response = await client.get(f"{configuration.base_url}/codes/list")
    ids = {item.get("code") for item in response.json().get("items")}
    assert ids == {
        "TEST_SENDING_FACILITY_1",
        "TEST_SENDING_FACILITY_2",
        "CODE_1",
        "CODE_2",
        "CODE_3",
        "G",
    }


async def test_codes_list_filter_standard(client):
    response = await client.get(
        f"{configuration.base_url}/codes/list?coding_standard=CODING_STANDARD_1"
    )
    ids = {item.get("code") for item in response.json().get("items")}
    assert ids == {"CODE_1"}


async def test_codes_list_search(client):
    response = await client.get(f"{configuration.base_url}/codes/list?search=CODE_")
    ids = {item.get("code") for item in response.json().get("items")}
    assert ids == {
        "CODE_1",
        "CODE_2",
        "CODE_3",
    }


async def test_code_list_export(client):
    response = await client.get(f"{configuration.base_url}/codes/export/list")
    assert (
        response.content
        == b'"RR1+","TEST_SENDING_FACILITY_1","TEST_SENDING_FACILITY_1_DESCRIPTION"\r\n"RR1+","TEST_SENDING_FACILITY_2","TEST_SENDING_FACILITY_2_DESCRIPTION"\r\n"CODING_STANDARD_1","CODE_1","DESCRIPTION_1"\r\n"CODING_STANDARD_2","CODE_2","DESCRIPTION_2"\r\n"CODING_STANDARD_2","CODE_3","DESCRIPTION_3"\r\n"NHS_DATA_DICTIONARY","G","ETHNICITY_GROUP_CODE_DESCRIPTION"\r\n'
    )


async def test_code_list_export_filter_standard(client):
    response = await client.get(
        f"{configuration.base_url}/codes/export/list?coding_standard=CODING_STANDARD_1"
    )
    assert response.content == b'"CODING_STANDARD_1","CODE_1","DESCRIPTION_1"\r\n'


async def test_code_maps_export(client):
    response = await client.get(f"{configuration.base_url}/codes/export/maps")
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","CODING_STANDARD_2","CODE_2"\r\n"CODING_STANDARD_2","CODE_2","CODING_STANDARD_1","CODE_1"\r\n'
    )


async def test_code_maps_export_filter_standard(client):
    response = await client.get(
        f"{configuration.base_url}/codes/export/maps?source_coding_standard=CODING_STANDARD_1"
    )
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","CODING_STANDARD_2","CODE_2"\r\n'
    )


async def test_code_exclusions_export(client):
    response = await client.get(f"{configuration.base_url}/codes/export/exclusions")
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","SYSTEM_1"\r\n"CODING_STANDARD_2","CODE_2","SYSTEM_1"\r\n"CODING_STANDARD_2","CODE_2","SYSTEM_2"\r\n'
    )


async def test_code_exclusions_export_filter_standard(client):
    response = await client.get(
        f"{configuration.base_url}/codes/export/exclusions?coding_standard=CODING_STANDARD_1"
    )
    assert response.content == b'"CODING_STANDARD_1","CODE_1","SYSTEM_1"\r\n'
