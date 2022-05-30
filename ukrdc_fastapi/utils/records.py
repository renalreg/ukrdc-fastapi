from ukrdc_sqla.ukrdc import PatientRecord

MIGRATED_EXTRACTS = ("PVMIG", "HSMIG")
UKRDC_MEMBERSHIP_FACILITIES = ("PV", "PKB")


def record_is_survey(record: PatientRecord):
    """All SURVEY extracts are survey records"""
    return record.sendingextract == "SURVEY"


def record_is_migrated(record: PatientRecord):
    """All *MIG extracts are migrated records"""
    return record.sendingextract in MIGRATED_EXTRACTS


def record_is_tracing(record: PatientRecord):
    """All TRACING facilities are tracing records"""
    return record.sendingfacility == "TRACING"


def record_is_membership(record: PatientRecord):
    """Check if a record is a membership record"""

    # All RADAR extracts are membership records
    if record.sendingextract == "RADAR":
        return True
    # All UKRR facilities are membership records
    if record.sendingfacility == "UKRR":
        return True
    # UKRDC extracts are only memberships if they are from certain facilities
    if (
        record.sendingextract == "UKRDC"
        and record.sendingfacility in UKRDC_MEMBERSHIP_FACILITIES
    ):
        return True
    return False


def record_is_data(record: PatientRecord):
    """Everything else is a data record"""
    return not (
        record_is_survey(record)
        or record_is_migrated(record)
        or record_is_tracing(record)
        or record_is_membership(record)
    )
