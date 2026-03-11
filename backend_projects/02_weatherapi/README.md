to run:
```
uv run uvicorn main:app --reload &
   sleep 3                                                      
   curl -s "http://localhost:8000/weather?city=London" | python3 -m json.tool
```

explaination:

# why async with?

async with is an asynchronous context manager. 
It ensures that:
1. HTTP client is created. 
2. requests are executed. 
3. the client is cleanly closed afterwards. 

Buy Python HTTP clients manage connections and pools, so they should be closed. 
`async with` does that automatically. 

httpx.Client()                  synchronous
httpx.Asyncclient()             asynchronous

httpx request format:

```
await client.request(
    method,
    url,
    params=...,   # query params
    json=...,     # json body
    data=...,     # form body
    headers=...
)

e.g. 

response = await client.get(
    GEOCODING_URL,
    params={
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }
)

```

