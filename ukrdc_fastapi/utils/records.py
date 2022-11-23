from ukrdc_sqla.ukrdc import PatientRecord

MIGRATED_EXTRACTS = ("PVMIG", "HSMIG")
MEMBERSHIP_FACILITIES = ("UKRR", "PV", "PKB")
INFORMATIONAL_FACILITIES = ("TRACING", "NHSBT")


def record_is_survey(record: PatientRecord):
    """All SURVEY extracts are survey records"""
    return record.sendingextract == "SURVEY"


def record_is_ukrr(record: PatientRecord):
    """
    All UKRR extracts are UKRR records,
    unless sendingfacility is UKRR (then it's a membership)
    """
    return record.sendingextract == "UKRR" and record.sendingfacility != "UKRR"


def record_is_migrated(record: PatientRecord):
    """All *MIG extracts are migrated records"""
    return record.sendingextract in MIGRATED_EXTRACTS


def record_is_informational(record: PatientRecord):
    """All TRACING facilities are tracing records"""
    return record.sendingfacility in INFORMATIONAL_FACILITIES


def record_is_membership(record: PatientRecord):
    """Check if a record is a membership record"""

    # All RADAR extracts are membership records
    # RADAR membership records have real facility codes as their sendingfacility
    if record.sendingextract == "RADAR":
        return True

    # Records with systems as their sendingfacility are membership records
    if record.sendingfacility in MEMBERSHIP_FACILITIES:
        return True
    return False


def record_is_data(record: PatientRecord):
    """Everything else is a data record"""
    return not (
        record_is_survey(record)
        or record_is_ukrr(record)
        or record_is_migrated(record)
        or record_is_informational(record)
        or record_is_membership(record)
    )
