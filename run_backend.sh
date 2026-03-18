#!/bin/bash
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
