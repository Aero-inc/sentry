# Stream Worker Service

CPU-based video stream processing service with ML inference capabilities.

## Structure

```
stream-worker/
├── src/
│   ├── api/                # REST API routes
│   │   ├── __init__.py
│   │   └── routes.py       # Flask endpoints
│   ├── core/               # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration management
│   │   └── errors.py       # Custom exceptions
│   ├── models/             # ML models
│   │   ├── __init__.py
│   │   ├── specialist_interface.py  # Abstract base class
│   │   └── cpu_specialist.py        # CPU inference implementation
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── aws_services.py        # S3 & CloudWatch
│   │   └── stream_processor.py    # Frame processing pipeline
│   └── utils/              # Utilities (future)
│       └── __init__.py
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
└── README.md
```

## Design Principles

- **Separation of Concerns**: API, business logic, models, and services are isolated
- **Dependency Injection**: Services are injected, not imported globally
- **Simple Logging**: Using print statements for now (CloudWatch handles aggregation)
- **Future-Proof**: Modular structure ready for expansion

## Configuration

Environment variables (see [src/core/config.py](src/core/config.py)):
- `ENVIRONMENT`: dev/prod
- `MODEL_PATH`: Path to ONNX model
- `S3_ARTIFACTS_BUCKET`: Model storage bucket
- `S3_CLIPS_BUCKET`: Frame/clip storage bucket

## API Endpoints

- `GET /health` - Health check
- `POST /streams` - Create stream
- `DELETE /streams/<id>` - Stop stream
- `POST /streams/<id>/frames` - Process frame
- `GET /stats` - Service statistics

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python app.py
```

## Docker

```bash
docker build -t stream-worker .
docker run -p 8000:8000 stream-worker
```
