from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord import DocumentSchema, DocumentSummarySchema


async def test_record_documents(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents"
    )
    assert response.status_code == 200


async def test_record_document_detail(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF"
    )
    assert response.status_code == 200


async def test_record_document_download_txt(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_TXT/download"
    )
    assert response.status_code == 200
    assert (
        response.headers.get("content-disposition")
        == "attachment; filename=DOCUMENT_TXT_NAME.txt"
    )
    assert response.content == b"DOCUMENT_TXT_NOTETEXT"


async def test_record_document_download_pdf(client_authenticated, minimal_pdf):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF/download"
    )
    assert response.status_code == 200
    assert (
        response.headers.get("content-disposition")
        == "attachment; filename=DOCUMENT_PDF_FILENAME.pdf"
    )
    assert response.content == minimal_pdf


async def test_record_documents_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/documents"
    )
    assert response.status_code == 403


async def test_record_document_detail_denied(client_authenticated):
    response = await client_authenticated.get(
        f"{configuration.base_url}/patientrecords/PYTEST03:PV:00000000A/documents/DOCUMENT_PDF"
    )
    assert response.status_code == 403
