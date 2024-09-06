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

### POST /vision
Processes an image for vision analysis.

**Request Body:**
```json
{
    "id": "unique_id",
    "image": "base64_encoded_image"
}
```

**Response:**
```json
{
    "id": "unique_id",
    "result": "detection_result"
}
```

### GET /drone_info
Retrieves information about the drone.

**Response:**
```json
{
    "current_position": "current_position",
    "detection": "detection_result",
    "panoramic": "panoramic_result",
    "time_counter": "time_counter",
    "drone_override": "drone_override_status"
}
```

### GET /guard_info
Retrieves information about the guard.

**Response:**
```json
{
    "drone_override": "drone_override_status",
    "initialize_panoramic_view": "initialize_panoramic_view_status",
    "drone_override_timer": "drone_override_timer"
}
```

### GET /trigger_panoramic
Triggers the panoramic view.

**Response:**
```json
{
    "status": "success"
}
```

