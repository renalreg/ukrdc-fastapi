from ukrdc_stats.calculators.demographics import DemographicsStats
from ukrdc_stats.calculators.dialysis import DialysisStats

from ukrdc_fastapi.config import configuration


async def test_facility_stats_demographics(client_superuser):
    # Repeat to ensure cached response matches
    for _ in range(2):
        response = await client_superuser.get(
            f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1/stats/demographics"
        )
        assert DemographicsStats(**response.json()).metadata.population == 2


async def test_facility_stats_dialysis(client_superuser):
    # Repeat to ensure cached response matches
    for _ in range(2):
        response = await client_superuser.get(
            f"{configuration.base_url}/facilities/TEST_SENDING_FACILITY_1/stats/dialysis"
        )
        assert DialysisStats(**response.json()).metadata.population == 1
