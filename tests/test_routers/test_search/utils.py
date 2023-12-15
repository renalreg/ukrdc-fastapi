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
        record_group_no = index % 2

        create_basic_patient(
            index + BUMPER,
            number,
            str(100000000 + index),
            number,
            f"TSF0{record_group_no + 1}",
            "UKRDC" if record_group_no else "PV",
            str(number),
            f"SURNAME{index}",
            f"NAME{index}",
            datetime(1950, 1, (index + 11) % 28),
            ukrdc3,
            jtrace,
        )
