from datetime import datetime
from ...utils import create_basic_facility, create_basic_patient

TEST_NUMBERS = [
    "9434765870",
    "9434765889",
    "9434765897",
    "9434765900",
    "9434765919",
    "9434765927",
    "9434765935",
    "9434765943",
    "9434765951",
]

BUMPER = 200


def commit_extra_patients(ukrdc3, jtrace):
    for index, number in enumerate(TEST_NUMBERS):
        nhs_number = number
        ukrdcid = 100000000 + index

        dob = datetime(1950, 1, (index + 11) % 28)
        localid = str(number)

        sending_facility = f"TSF{index + BUMPER}"
        sending_facility_desc = f"TSF{index + BUMPER}_DESCRIPTION"
        sending_extract = "UKRDC"

        create_basic_facility(
            sending_facility,
            sending_facility_desc,
            ukrdc3,
        )

        create_basic_patient(
            index + BUMPER,
            number,
            str(ukrdcid),
            nhs_number,
            sending_facility,
            sending_extract,
            localid,
            f"SURNAME{index}",
            f"NAME{index}",
            dob,
            ukrdc3,
            jtrace,
        )
