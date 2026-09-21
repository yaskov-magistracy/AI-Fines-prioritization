from httpx import AsyncClient

from tests.factories import make_pdf


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


async def test_upload_and_fetch(client: AsyncClient) -> None:
    files = {"file": ("case.pdf", make_pdf(), "application/pdf")}
    created = await client.post("/documents", files=files)
    assert created.status_code == 201, created.text

    body = created.json()
    assert body["case"]["vin"] == "JTDBE32K123456789"

    fetched = await client.get(f"/documents/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


async def test_upload_rejects_non_pdf(client: AsyncClient) -> None:
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    assert (await client.post("/documents", files=files)).status_code == 415


async def test_search_filters_and_sorts(client: AsyncClient) -> None:
    for year in (2010, 2018):
        pdf = make_pdf(
            [
                "Dolzhnik: Petrov Petr Petrovich",
                "Summa dolga: 300 000 rub.",
                "Marka, model: Kia Rio",
                f"God vypuska: {year}",
            ]
        )
        response = await client.post("/documents", files={"file": (f"{year}.pdf", pdf)})
        assert response.status_code == 201, response.text

    found = await client.get("/cases", params={"make": "Kia", "sort_by": "year", "order": "desc"})
    assert found.status_code == 200
    page = found.json()
    assert page["total"] == 2
    assert [item["year"] for item in page["items"]] == [2018, 2010]

    narrowed = await client.get("/cases", params={"year_min": 2015})
    assert narrowed.json()["total"] == 1

    missing = await client.get("/cases", params={"make": "Ferrari"})
    assert missing.json()["total"] == 0


async def test_document_404(client: AsyncClient) -> None:
    unknown = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/documents/{unknown}")).status_code == 404
