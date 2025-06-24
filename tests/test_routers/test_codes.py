from ukrdc_fastapi.config import configuration


async def test_codes_list(client_authenticated):
    response = await client_authenticated.get(f"{configuration.base_url}/codes/list")
    assert response.status_code == 200


async def test_code_list_export(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/list"
    )
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","DESCRIPTION_1"\r\n"CODING_STANDARD_2","CODE_2","DESCRIPTION_2"\r\n"CODING_STANDARD_2","CODE_3","DESCRIPTION_3"\r\n"NHS_DATA_DICTIONARY","G","ETHNICITY_GROUP_DESCRIPTION"\r\n"NHS_DATA_DICTIONARY","eth2","DESCRIPTION_3"\r\n"RR1+","TSF01","TSF01_DESCRIPTION"\r\n"RR1+","TSF02","TSF02_DESCRIPTION"\r\n"URTS_ETHNIC_GROUPING","eth1","DESCRIPTION_3"\r\n'
    )


async def test_code_list_export_filter_standard(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/list?coding_standard=CODING_STANDARD_1"
    )
    assert response.content == b'"CODING_STANDARD_1","CODE_1","DESCRIPTION_1"\r\n'


async def test_code_maps_export(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/maps"
    )
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","CODING_STANDARD_2","CODE_2"\r\n"CODING_STANDARD_2","CODE_2","CODING_STANDARD_1","CODE_1"\r\n"NHS_DATA_DICTIONARY","eth2","URTS_ETHNIC_GROUPING","eth1"\r\n'
    )


async def test_code_maps_export_filter_standard(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/maps?source_coding_standard=CODING_STANDARD_1"
    )
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","CODING_STANDARD_2","CODE_2"\r\n'
    )


async def test_code_exclusions_export(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/exclusions"
    )
    assert (
        response.content
        == b'"CODING_STANDARD_1","CODE_1","SYSTEM_1"\r\n"CODING_STANDARD_2","CODE_2","SYSTEM_1"\r\n"CODING_STANDARD_2","CODE_2","SYSTEM_2"\r\n'
    )


async def test_code_exclusions_export_filter_standard(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/codes/export/exclusions?coding_standard=CODING_STANDARD_1"
    )
    assert response.content == b'"CODING_STANDARD_1","CODE_1","SYSTEM_1"\r\n'
