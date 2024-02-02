from ukrdc_fastapi.utils.mirth.messages import (
    build_export_all_message,
    build_export_docs_message,
    build_export_radar_message,
    build_export_tests_message,
    build_merge_message,
    build_unlink_message,
    build_update_workitem_message,
)


def test_build_merge_message():
    assert (
        build_merge_message(1, 2)
        == "<request><superceding>1</superceding><superceeded>2</superceeded></request>"
    )


def test_build_unlink_message():
    assert (
        build_unlink_message(1, 2, "user", "description")
        == "<request><masterRecord>1</masterRecord><personId>2</personId><updateDescription>description</updateDescription><updatedBy>user</updatedBy></request>"
    )


def test_build_update_workitem_message():
    assert (
        build_update_workitem_message(1, 2, "description", "user")
        == "<request><workitem>1</workitem><status>2</status><updateDescription>description</updateDescription><updatedBy>user</updatedBy></request>"
    )


def test_build_export_tests_message():
    assert (
        build_export_tests_message("pid")
        == "<result><pid>pid</pid><tests>FULL</tests></result>"
    )


def test_build_export_docs_message():
    assert (
        build_export_docs_message("pid")
        == "<result><pid>pid</pid><documents>FULL</documents></result>"
    )


def test_build_export_all_message():
    assert (
        build_export_all_message("pid")
        == "<result><pid>pid</pid><tests>FULL</tests><documents>FULL</documents></result>"
    )


def test_build_export_radar_message():
    assert build_export_radar_message("pid") == "<result><pid>pid</pid></result>"
