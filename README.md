# AI Fines Prioritization

Приоритизация должников по ликвидности их автомобиля.

PDF с постановлением (данные должника, сумма долга, фото машины) → извлечение полей →
оценка рыночной стоимости ТС → поиск по базе с фильтрами и сортировкой.

[![CI](https://github.com/yaskov-magistracy/AI-Fines-prioritization/actions/workflows/ci.yml/badge.svg)](https://github.com/yaskov-magistracy/AI-Fines-prioritization/actions/workflows/ci.yml)
[![Docker](https://github.com/yaskov-magistracy/AI-Fines-prioritization/actions/workflows/docker.yml/badge.svg)](https://github.com/yaskov-magistracy/AI-Fines-prioritization/actions/workflows/docker.yml)

## Конвейер

```
PDF → pdf.read_pdf → Extractor → PriceProvider → Postgres → REST /cases
      текст+фото     поля ТС     рыночная цена   DebtCase   фильтры и сортировка
```

Ключевая метрика приоритизации — `debt_to_value_ratio` = долг / стоимость машины.
Чем меньше, тем выгоднее взыскание.

## Быстрый старт

```bash
cp .env.example .env
make install
make up          # postgres + api в docker, миграции накатятся сами
open http://localhost:8000/docs
```

Без docker:

```bash
make install
make migrate
make run
```

Пакетная загрузка папки с PDF:

```bash
poetry run fines ingest ./data/pdfs
```

## API

| Метод | Путь | Что делает |
|---|---|---|
| `POST` | `/documents` | Загрузить PDF, сразу распарсить и оценить |
| `GET` | `/documents/{id}` | Карточка документа с извлечёнными полями |
| `GET` | `/documents/{id}/file` | Скачать исходный PDF |
| `GET` | `/cases` | Поиск с фильтрами и сортировкой |
| `GET` | `/health` | Проверка живости и коннекта к БД |

Фильтры `/cases`: `q`, `make`, `model`, `vin`, `year_min/max`, `debt_min/max`,
`value_min/max`, `ratio_max`, `status`.
Сортировка: `sort_by` ∈ {`debt_amount`, `market_value`, `debt_to_value_ratio`, `year`,
`created_at`}, `order` ∈ {`asc`, `desc`}. Пагинация: `limit`, `offset`.

```bash
curl -F file=@case.pdf http://localhost:8000/documents
curl "http://localhost:8000/cases?make=Toyota&ratio_max=0.5&sort_by=market_value&order=desc"
```

## Точки расширения

Обе подменяемые части описаны протоколами — новая реализация не трогает конвейер.

**Извлечение полей** — `fines.extraction.base.Extractor`:
- `rule_based` (по умолчанию): pdfplumber + регулярки, детерминирован, не ходит в сеть;
- `llm`: заглушка под OpenAI-совместимый эндпоинт, включается `EXTRACTOR_BACKEND=llm`.

Справочник марок — `KNOWN_MAKES` в `src/fines/extraction/patterns.py`, пополняется
по мере встреч в реальных PDF.

**Оценка стоимости** — `fines.pricing.base.PriceProvider`:
- `stub` (по умолчанию): детерминированная формула от марки, возраста и пробега;
- `http`: заглушка под внешний прайс-API, включается `PRICE_PROVIDER=http`.

## Структура

```
src/fines/
├── api/routes/     эндпоинты FastAPI
├── extraction/     чтение PDF и извлечение полей
├── pricing/        провайдеры рыночной цены
├── models.py       ORM: Document, DebtCase, Photo
├── repository.py   поиск с фильтрами
├── pipeline.py     весь конвейер ingest
└── cli.py          пакетная загрузка
alembic/            миграции
tests/              unit + API-тесты на in-memory sqlite
```

## Разработка

```bash
make check      # ruff + mypy + pytest — то же, что гоняет CI
make fmt        # автоформат
make revision m="описание"   # новая миграция
```

Тесты идут на in-memory sqlite и не требуют ни Postgres, ни сети.
Миграции отдельной джобой проверяются на настоящем Postgres (`alembic check`
ловит расхождение моделей и миграций).

## CI/CD

| Workflow | Триггер | Что делает |
|---|---|---|
| `ci.yml` | push в main, PR | ruff, mypy, pytest на 3.11/3.12/3.13, миграции на Postgres |
| `docker.yml` | push в main, теги, PR | сборка образа, дымовой тест на PR, публикация в GHCR |
| `release.yml` | тег `v*.*.*` | GitHub Release с автогенерируемым changelog |

Образ: `ghcr.io/yaskov-magistracy/ai-fines-prioritization`, рассчитан на Postgres —
передайте `DATABASE_URL` и примонтируйте том под `/data/storage`. Секреты не нужны —
хватает встроенного `GITHUB_TOKEN`.

Релиз:

```bash
# version в pyproject.toml должна совпасть с тегом, иначе workflow упадёт
git tag v0.1.0 && git push origin v0.1.0
```

## Конфигурация

Все настройки — через переменные окружения, см. `.env.example`.
`.env` в git не попадает; ключи читаются только через окружение.

## Что дальше

- [ ] Фоновая обработка загрузок (сейчас парсинг синхронный внутри запроса)
- [ ] Реальный провайдер цен вместо заглушки
- [ ] Распознавание марки/модели по фото машины
- [ ] OCR для сканов без текстового слоя
- [ ] Веб-интерфейс поверх `/cases`

## Лицензия

MIT — см. [LICENSE](LICENSE).
