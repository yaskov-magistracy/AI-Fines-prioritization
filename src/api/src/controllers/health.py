from fastapi import APIRouter, Response, status


router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health() -> Response:
    return Response(status_code=status.HTTP_200_OK)

