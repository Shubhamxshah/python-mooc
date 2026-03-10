to run:
```
uv run uvicorn main:app --reload &
   sleep 3                                                      
   curl -s "http://localhost:8000/weather?city=London" | python3 -m json.tool
```