# API

## Запуск

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python main.py
```

Swagger:
http://localhost/docs

Запуск тестов:

```powershell
pytest
```
