import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from fines.api.deps import SessionDep, SettingsDep
from fines.pipeline import IngestPipeline
from fines.repository import CaseRepository
from fines.schemas import DocumentOut
from fines.storage import LocalStorage

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload(
    session: SessionDep,
    settings: SettingsDep,
    file: Annotated[UploadFile, File()],
) -> DocumentOut:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Принимаются только PDF")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Файл больше 50 МБ")

    pipeline = IngestPipeline(session, settings)
    document = await pipeline.ingest(file.filename or "unnamed.pdf", data)
    await session.flush()
    return DocumentOut.model_validate(document)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: uuid.UUID, session: SessionDep) -> DocumentOut:
    document = await CaseRepository(session).get_document(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Документ не найден")
    return DocumentOut.model_validate(document)


@router.get("/{document_id}/file")
async def download_document(
    document_id: uuid.UUID, session: SessionDep, settings: SettingsDep
) -> FileResponse:
    document = await CaseRepository(session).get_document(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Документ не найден")

    path = LocalStorage(settings.storage_dir).path(document.storage_path)
    if not path.exists():
        raise HTTPException(status.HTTP_410_GONE, "Файл отсутствует в хранилище")
    return FileResponse(path, media_type="application/pdf", filename=document.filename)
