from ukrdc_fastapi.config import configuration
from ukrdc_fastapi.schemas.patientrecord import DocumentSchema, DocumentSummarySchema


async def test_record_documents(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents"
    )
    assert response.status_code == 200
    documents = [DocumentSummarySchema(**item) for item in response.json()["items"]]
    assert {doc.id for doc in documents} == {
        "DOCUMENT_PDF",
        "DOCUMENT_TXT",
    }


async def test_record_document_detail(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF"
    )
    assert response.status_code == 200
    document = DocumentSchema(**response.json())
    assert document
    assert document.id == "DOCUMENT_PDF"


async def test_record_document_download_txt(client_superuser):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_TXT/download"
    )
    assert response.status_code == 200
    assert (
        response.headers.get("content-disposition")
        == "attachment; filename=DOCUMENT_TXT_NAME.txt"
    )
    assert response.content == b"DOCUMENT_TXT_NOTETEXT"


async def test_record_document_download_pdf(client_superuser, minimal_pdf):
    response = await client_superuser.get(
        f"{configuration.base_url}/patientrecords/PYTEST01:PV:00000000A/documents/DOCUMENT_PDF/download"
    )
    assert response.status_code == 200
    assert (
        response.headers.get("content-disposition")
        == "attachment; filename=DOCUMENT_PDF_FILENAME.pdf"
    )
    assert response.content == minimal_pdf
