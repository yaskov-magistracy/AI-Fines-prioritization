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

## API

| Метод | Путь | Что делает |
|---|---|---|
| `POST` | `/documents` | Загрузить PDF |
| `POST` | `/documents/appraise` | Распарсить + оценить |
| `GET` | `/documents/{id}` | Карточка документа с извлечёнными полями |
| `GET` | `/documents/{id}/file` | Скачать исходный PDF |
| `POST` | `/documents/search` | Поиск с фильтрами и сортировкой |
| `GET` | `/health` | Проверка живости и коннекта к БД |

Фильтры поиска `/documents`: `q`, `make`, `model`, `vin`, `year_min/max`, `debt_min/max`,
`value_min/max`, `debt_to_value_ratio`, `status`.
Сортировка: `sort_by` ∈ {`debt_amount`, `market_value`, `debt_to_value_ratio`, `year`,
`created_at`}, `order` ∈ {`asc`, `desc`}. Пагинация: `limit`, `offset`.

## Точки расширения

Обе подменяемые части описаны протоколами — новая реализация не трогает конвейер.

**Извлечение полей** — `fines.extraction.base.Extractor`:
- `rule_based` (по умолчанию): pdfplumber + регулярки, детерминирован, не ходит в сеть;
- `llm`: GigaChat.

Справочник марок — `KNOWN_MAKES` в `src/fines/extraction/patterns.py`, пополняется
по мере встреч в реальных PDF.

**Оценка стоимости** — `fines.pricing.base.PriceProvider`:
- `avito_provider`
- `auto_ru_provider`
- ...

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
```
