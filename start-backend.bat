@echo off
echo Starting Legal Companion Backend...
echo.
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause