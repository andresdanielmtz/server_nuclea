# API Documentation 

URL: `https://localhost:8585/` 
## Endpoints 
### GET /vision 
```
id: str 
image: base64 str 
```

### POST /set_channel 
```
subject: list[str] 
content: str 
```

Example: 
```bash
curl -X POST "http://localhost:8585/set_channel" \
     -H "Content-Type: application/json" \
     -d '{"subject": ["camera", "drone"], "content": "intruder"}'
```

### GET /clean_channel 

Example: 
```bash
curl -X GET "http://localhost:8585/clean_channel"
```

### GET /check_test 

Example: 
```bash
curl -X GET "http://localhost:8585/check_test"
```