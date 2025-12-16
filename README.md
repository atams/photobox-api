# Photobox API

A FastAPI-based QRIS payment system for photobox kiosks, built with the ATAMS toolkit. Integrates with Xendit for QRIS payment processing with a polling-based payment status architecture.

## Table of Contents

-   [Key Features](#key-features)
-   [Technology Stack](#technology-stack)
-   [Prerequisites](#prerequisites)
-   [Installation](#installation)
-   [Configuration](#configuration)
-   [Running the Application](#running-the-application)
-   [API Endpoints](#api-endpoints)
-   [Architecture](#architecture)
-   [Payment Flow](#payment-flow)
-   [Security](#security)
-   [Testing](#testing)
-   [Deployment](#deployment)
-   [Project Structure](#project-structure)

## Key Features

-   **QRIS Payment Integration**: Seamless integration with Xendit for QRIS payment generation and processing
-   **Polling-Based Status Updates**: Real-time payment status tracking via 3-second polling mechanism
-   **Location Management**: Master data management for photobox machine locations
-   **Webhook Processing**: Secure webhook endpoint for payment status notifications from Xendit
-   **Atlas SSO Integration**: Enterprise-grade authentication via ATAMS toolkit
-   **Auto-Generated Transaction IDs**: Unique external ID generation with location and timestamp
-   **15-Minute QRIS Expiration**: Automatic expiration handling for payment codes

## Technology Stack

-   **Framework**: FastAPI
-   **Database**: PostgreSQL (Aiven)
-   **ORM**: SQLAlchemy
-   **Authentication**: Atlas SSO (ATAMS)
-   **Payment Gateway**: Xendit (QRIS)
-   **Validation**: Pydantic
-   **Server**: Uvicorn
-   **Toolkit**: ATAMS (Atlas Toolkit for API Management System)

## Prerequisites

-   Python 3.10+
-   PostgreSQL database
-   Xendit account with API access
-   Atlas SSO credentials (for authentication)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/[username]/photobox-api.git
    cd photobox-api
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment:**

    - Linux/Mac:
        ```bash
        source venv/bin/activate
        ```
    - Windows:
        ```bash
        venv\Scripts\activate
        ```

4. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the project root directory with the following variables:

```env
# Application Settings
APP_NAME=Photobox API
APP_VERSION=1.0.0
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/photobox

# Database Connection Pool
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30
DB_POOL_PRE_PING=true

# Atlas SSO Configuration
ATLAS_SSO_URL=https://atlas.yourdomain.com/api/v1
ATLAS_APP_CODE=PHOTOBOX
ATLAS_ENCRYPTION_KEY=[32-char-key]
ATLAS_ENCRYPTION_IV=[16-char-iv]

# Xendit Configuration
XENDIT_API_KEY=xnd_development_...
XENDIT_WEBHOOK_URL=https://your-domain.com/api/v1/webhooks/xendit
XENDIT_CALLBACK_TOKEN=your_callback_token_here

# Response Encryption (Optional)
ENCRYPTION_ENABLED=false
ENCRYPTION_KEY=[32-char-hex]  # Generate: openssl rand -hex 16
ENCRYPTION_IV=[16-char-hex]   # Generate: openssl rand -hex 8

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# Logging
LOGGING_ENABLED=true
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_FILE_PATH=logs/app.log
```

**Important Notes:**

-   `XENDIT_WEBHOOK_URL` must be publicly accessible and configured in both `.env` AND Xendit dashboard
-   For Aiven free tier (20 connection limit), keep default pool settings
-   Total connections = `(DB_POOL_SIZE + DB_MAX_OVERFLOW) × app_instances`

## Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Access Points:**

-   API Documentation (Swagger): http://localhost:8000/docs
-   API Documentation (ReDoc): http://localhost:8000/redoc
-   Health Check: http://localhost:8000/health

## API Endpoints

Base URL: `/api/v1`

### Transactions

**Base Path:** `/api/v1/transactions`

#### POST /api/v1/transactions

Create a new transaction and generate QRIS payment code.

**Authorization:** Required (Atlas SSO)

**Request Body:**

```json
{
    "location_id": 2
}
```

**Response:**

```json
{
    "success": true,
    "message": "Transaction created successfully",
    "data": {
        "tr_id": 1,
        "tr_external_id": "TRX-2-20251215092229-57283A15",
        "tr_location_id": 2,
        "tr_amount": 40000,
        "tr_status": "PENDING",
        "tr_qris_string": "00020101021226...",
        "tr_qris_url": "https://d.xnd.io/...",
        "tr_expired_at": "2025-12-15T09:37:29",
        "tr_created_at": "2025-12-15T09:22:29"
    }
}
```

**Business Logic:**

-   Amount is fixed at Rp 40,000 (`PHOTOBOX_AMOUNT` constant)
-   External ID format: `TRX-{location_id}-{timestamp}-{random}`
-   QRIS expires in exactly 15 minutes
-   Initial status is `PENDING`

#### GET /api/v1/transactions/external/{external_id}

Get transaction status by external ID (for polling).

**Authorization:** Not required (public endpoint for frontend polling)

**Response (Normal):**

```json
{
    "success": true,
    "message": "Transaction retrieved successfully",
    "data": {
        "tr_id": 1,
        "tr_external_id": "TRX-2-20251215092229-57283A15",
        "tr_status": "COMPLETED",
        "tr_paid_at": "2025-12-15T09:25:30",
        "tr_amount": 40000
    }
}
```

**Response (Encrypted, when `ENCRYPTION_ENABLED=true`):**

```json
{
    "data": "base64_encoded_encrypted_payload"
}
```

**Status Values:**

-   `PENDING`: Payment not yet completed
-   `COMPLETED`: Payment successful
-   `FAILED`: Payment failed
-   `EXPIRED`: QRIS code expired (15 minutes)

#### GET /api/v1/transactions/{external_id}/photos

Get all photos for a transaction (for frontend gallery).

**Authorization:** Not required (public endpoint for gallery display)

**Response (Normal):**

```json
{
    "external_id": "TRX-2-20251215092229-57283A15",
    "photo_count": 12,
    "email_sent_at": "2025-12-15T10:00:00",
    "expiry_date": "2025-12-29T00:00:00",
    "photos": [
        {
            "url": "https://res.cloudinary.com/..."
        }
    ]
}
```

**Response (Encrypted, when `ENCRYPTION_ENABLED=true`):**

```json
{
    "data": "base64_encoded_encrypted_payload"
}
```

**Notes:**

-   Photos expire 14 days after email sent
-   Returns 404 if transaction not found or no photos uploaded

#### GET /api/v1/transactions/count

Get total count of transactions by status.

**Authorization:** Required (Atlas SSO)

**Query Parameters:**

-   `status`: Filter by status (optional, comma-separated: "COMPLETED,PENDING")

**Response:**

```json
{
    "success": true,
    "message": "Transaction count retrieved successfully",
    "data": {
        "count": 42
    }
}
```

#### GET /api/v1/transactions (List)

List all transactions with pagination and filtering.

**Authorization:** Required (Atlas SSO)

**Query Parameters:**

-   `search`: Filter by external ID or location name (optional)
-   `skip`: Offset pagination (default: 0)
-   `limit`: Records per page (1-1000, default: 100)

**Response:**

```json
{
    "success": true,
    "message": "Transactions retrieved successfully",
    "data": [
        {
            "tr_id": 1,
            "tr_external_id": "TRX-2-20251215092229-57283A15",
            "tr_status": "COMPLETED",
            "tr_amount": 40000,
            "location": {
                "ml_id": 2,
                "ml_name": "Mall Kelapa Gading"
            }
        }
    ],
    "total": 100,
    "page": 1,
    "size": 100,
    "pages": 1
}
```

---

### Locations

**Base Path:** `/api/v1/locations`

#### GET /api/v1/locations

List all photobox locations with pagination.

**Authorization:** Required (Atlas SSO)

**Query Parameters:**

-   `search`: Filter by location name (optional)
-   `skip`: Offset pagination (default: 0)
-   `limit`: Records per page (1-1000, default: 100)

**Response:**

```json
{
    "success": true,
    "message": "Locations retrieved successfully",
    "data": [
        {
            "ml_id": 1,
            "ml_name": "Mall Taman Anggrek",
            "ml_address": "Jl. Taman Anggrek No. 1",
            "ml_created_at": "2025-12-15T09:00:00"
        }
    ],
    "total": 10,
    "page": 1,
    "size": 100,
    "pages": 1
}
```

#### GET /api/v1/locations/{id}

Get single location by ID.

**Authorization:** Required (Atlas SSO)

**Response:** Single location object

#### POST /api/v1/locations

Create new location.

**Authorization:** Required (Atlas SSO, Admin level)

**Request Body:**

```json
{
    "ml_name": "Mall Senayan City",
    "ml_address": "Jl. Asia Afrika No. 8"
}
```

#### PUT /api/v1/locations/{id}

Update existing location.

**Authorization:** Required (Atlas SSO, Admin level)

#### DELETE /api/v1/locations/{id}

Delete location.

**Authorization:** Required (Atlas SSO, Admin level)

---

### Webhooks

#### POST /api/v1/webhooks/xendit

Xendit webhook endpoint for payment status updates.

**Authorization:** Xendit callback token (header: `x-callback-token`)

**Request Body (from Xendit):**

```json
{
    "external_id": "TRX-2-20251215092229-57283A15",
    "status": "COMPLETED",
    "xendit_id": "qr_5d408580-80cf-471a-a69f-976daadf1b84"
}
```

**Security:**

-   Validates `x-callback-token` header
-   Returns 401 if token missing
-   Returns 403 if token invalid
-   `paid_at` timestamp set automatically on COMPLETED status

---

### Prices

**Base Path:** `/api/v1/prices`

#### GET /api/v1/prices

List all price configurations.

**Authorization:** Required (Atlas SSO)

#### GET /api/v1/prices/{id}

Get single price by ID.

**Authorization:** Required (Atlas SSO)

#### POST /api/v1/prices

Create new price configuration.

**Authorization:** Required (Atlas SSO, Admin level)

#### PUT /api/v1/prices/{id}

Update existing price.

**Authorization:** Required (Atlas SSO, Admin level)

#### DELETE /api/v1/prices/{id}

Delete price.

**Authorization:** Required (Atlas SSO, Admin level)

## Architecture

### Database Schema

**Schema:** `photobox`

**Tables:**

1. **master_locations** - Photobox machine locations

    - `ml_id` (PK): Location ID
    - `ml_name`: Location name
    - `ml_address`: Physical address
    - `ml_created_at`: Creation timestamp
    - **Constraints**: Unique location names

2. **transactions** - Payment transactions

    - `tr_id` (PK): Transaction ID
    - `tr_external_id` (Unique): External transaction identifier
    - `tr_location_id` (FK): References master_locations
    - `tr_amount`: Payment amount (Rp 40,000 fixed)
    - `tr_status`: Status (PENDING/COMPLETED/FAILED/EXPIRED)
    - `tr_qris_string`: Full QRIS payload for QR generation
    - `tr_qris_url`: Xendit QRIS URL
    - `tr_xendit_id`: Xendit payment identifier
    - `tr_expired_at`: QRIS expiration timestamp (15 minutes)
    - `tr_paid_at`: Payment completion timestamp
    - `tr_created_at`: Creation timestamp
    - **Indexes**: `tr_external_id`, `tr_status`, `tr_created_at`

3. **master_prices** - Price configurations
    - `mp_id` (PK): Price ID
    - `mp_name`: Price name/description
    - `mp_amount`: Price amount
    - `mp_created_at`: Creation timestamp

### Layered Architecture (ATAMS Pattern)

```
API Layer (endpoints/)       → Service Layer (services/)       → Repository Layer (repositories/)       → Database
     ↓                                  ↓                                  ↓
  FastAPI                       Business Logic                      SQLAlchemy ORM
  Authorization                 Validation                          Transactions
  Response Format              Xendit Integration                   joinedload
```

**Key Principle:** Business logic lives in the Service layer. Repositories handle only database operations.

### Payment Flow Architecture

This system uses a **polling-based architecture** for real-time payment status updates:

```
1. Frontend → Backend: POST /transactions
2. Backend → Xendit: Create QRIS (15-min expiration)
3. Backend → Frontend: Return transaction + qr_string
4. Frontend: Display QR code + Start polling (3s interval)
5. Frontend → Backend: GET /transactions/external/{id} (every 3s)
6. User: Scans QR + Pays via banking app
7. Xendit → Backend: POST /webhooks/xendit (status update)
8. Frontend: Polling detects COMPLETED status → Stop polling
```

**Critical:** Frontend NEVER calls Xendit directly. All payment operations flow through the backend API.

### Data Flow

```
Request → ATAMS Middleware → Endpoint → Service → Repository → Database
                                          ↓
                                    Xendit API (async)
```

## Payment Flow

### Transaction Creation Process

1. **Frontend submits** `location_id` to `/api/v1/transactions`
2. **TransactionService generates**:
    - External ID: `TRX-{location_id}-{timestamp}-{random}`
    - Amount: Rp 40,000 (fixed constant)
    - Expiration: Current time + 15 minutes
3. **XenditService creates QRIS**:
    - Basic Auth with Base64-encoded API key
    - Returns `qr_string` (for QR code display) and `qr_url`
4. **Backend saves transaction** with status `PENDING`
5. **Frontend receives** transaction data including `qr_string`

### Frontend Polling Strategy

**Requirements:**

-   Poll `/api/v1/transactions/external/{external_id}` every **3 seconds**
-   Start immediately after transaction creation
-   Stop when status reaches terminal state: `COMPLETED`, `FAILED`, or `EXPIRED`
-   Maximum polling duration: **15 minutes** (matches QRIS expiration)

**QR Code Display:**

-   Use `tr_qris_string` field to generate QR code image
-   Frontend library: `qrcode.js` or similar

### Transaction Status Flow

```
PENDING → COMPLETED (payment success via webhook)
PENDING → FAILED (payment error)
PENDING → EXPIRED (15-minute timeout)
```

Status transitions are one-way only. Terminal states are final.

### Webhook Processing

1. **Xendit sends webhook** to `/api/v1/webhooks/xendit`
2. **Backend validates** `x-callback-token` header
3. **TransactionService updates** status and sets `paid_at` timestamp
4. **Frontend polling** detects status change on next poll

## Security

### Authentication & Authorization

**Atlas SSO Integration:**

-   Enterprise SSO authentication via ATAMS toolkit
-   Token validation through `ATLAS_SSO_URL`
-   Application identifier: `ATLAS_APP_CODE`
-   Token decryption: `ATLAS_ENCRYPTION_KEY` + `ATLAS_ENCRYPTION_IV`

**Authorization Levels:**

-   **Level 1** (>= 1): Regular users (read access)
-   **Level 50** (>= 50): Administrators (full CRUD)

**Usage in Endpoints:**

```python
from app.api.deps import require_auth, require_min_role_level

# Basic auth
@router.get("/endpoint", dependencies=[Depends(require_auth)])

# Admin-only
@router.post("/locations", dependencies=[Depends(require_min_role_level(50))])
```

**Public Endpoints:**

-   `GET /api/v1/transactions/external/{external_id}` - No auth required (for polling)
-   `POST /api/v1/webhooks/xendit` - Webhook token validation only

### Webhook Security

Xendit webhook endpoint validates:

1. Presence of `x-callback-token` header
2. Token matches `XENDIT_CALLBACK_TOKEN` from environment
3. Returns 401 if missing, 403 if invalid

### Response Encryption

The API supports AES-256-CBC encryption for sensitive endpoints. When enabled, responses are encrypted before being sent to the client.

**Configuration:**

-   `ENCRYPTION_ENABLED`: Enable/disable response encryption (default: false)
-   `ENCRYPTION_KEY`: 32-character AES encryption key
-   `ENCRYPTION_IV`: 16-character initialization vector

**Encrypted Endpoints:**

-   `GET /api/v1/transactions/external/{external_id}` - Transaction polling endpoint
-   `GET /api/v1/transactions/{external_id}/photos` - Photos list endpoint

**Encryption Details:**

-   Algorithm: AES-256-CBC
-   Padding: PKCS7
-   Output: Base64-encoded encrypted JSON
-   Frontend must decrypt using the same key and IV

**Response Format (when encrypted):**

```json
{
    "data": "base64_encoded_encrypted_payload"
}
```

**Implementation Files:**

-   Encryption service: [app/core/encryption.py](app/core/encryption.py)
-   Response wrapper: [app/utils/response_encryption.py](app/utils/response_encryption.py)

### Environment Variables

**Critical secrets that must not be committed:**

-   `DATABASE_URL`: PostgreSQL connection string
-   `XENDIT_API_KEY`: Xendit secret key
-   `XENDIT_CALLBACK_TOKEN`: Webhook verification token
-   `ATLAS_ENCRYPTION_KEY`, `ATLAS_ENCRYPTION_IV`: SSO encryption keys
-   `ENCRYPTION_KEY`, `ENCRYPTION_IV`: Response encryption keys

## Testing

### Manual Testing with cURL

**Create Transaction:**

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SSO_TOKEN" \
  -d '{"location_id": 2}'
```

**Check Status (Polling):**

```bash
curl http://localhost:8000/api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

**Simulate Webhook (Development Only):**

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/xendit \
  -H "Content-Type: application/json" \
  -H "x-callback-token: your_callback_token_here" \
  -d '{
    "external_id": "TRX-2-20251215092229-57283A15",
    "status": "COMPLETED",
    "xendit_id": "qr_5d408580-80cf-471a-a69f-976daadf1b84"
  }'
```

**Note:** `paid_at` is automatically set to current time when status is `COMPLETED`.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_transaction_service.py
```

## Deployment

### Environment-Specific Configuration

**Development:**

-   `DEBUG=true`
-   Detailed logging
-   CORS allows all origins
-   Local database

**Production:**

-   `DEBUG=false`
-   Error logging only
-   CORS restricted to specific domains
-   Connection pooling optimized for cloud database
-   `XENDIT_WEBHOOK_URL` must be publicly accessible HTTPS endpoint

### Database Connection Pooling

Critical for production deployment:

-   `DB_POOL_SIZE=3`: Base pool size
-   `DB_MAX_OVERFLOW=5`: Additional connections
-   Total connections = `(3 + 5) × app_instances`

**For Aiven Free Tier (20 connection limit):**

-   Max 2 app instances with default settings
-   Monitor connection usage carefully

### Xendit Configuration Checklist

1. ✅ Get API key from Xendit dashboard
2. ✅ Set `XENDIT_API_KEY` in `.env`
3. ✅ Deploy backend with public HTTPS URL
4. ✅ Set `XENDIT_WEBHOOK_URL` in `.env`
5. ✅ Configure webhook URL in Xendit dashboard
6. ✅ Copy callback token from Xendit to `XENDIT_CALLBACK_TOKEN`

## Project Structure

```
photobox-api/
├── app/
│   ├── core/
│   │   ├── config.py              # Application configuration
│   │   └── encryption.py          # AES encryption service
│   ├── db/
│   │   └── session.py             # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── master_location.py     # Location model
│   │   ├── transaction.py         # Transaction model
│   │   └── master_price.py        # Price model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py              # Common response schemas
│   │   ├── master_location.py     # Location schemas
│   │   ├── transaction.py         # Transaction schemas
│   │   └── master_price.py        # Price schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── master_location_repository.py
│   │   ├── transaction_repository.py
│   │   └── master_price_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── master_location_service.py
│   │   ├── transaction_service.py  # Core payment logic + Xendit
│   │   ├── xendit_service.py      # Xendit API integration
│   │   └── master_price_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── response_encryption.py # Response encryption wrapper
│   ├── api/
│   │   ├── deps.py                # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── api.py             # Router aggregation
│   │       └── endpoints/
│   │           ├── master_locations.py
│   │           ├── transactions.py
│   │           ├── webhooks.py     # Xendit webhook handler
│   │           └── master_prices.py
│   └── main.py                    # FastAPI application entry point
├── docs/
│   └── endpoint.md                # API endpoint specifications
├── .env.example                   # Environment variables template
├── .gitignore
├── requirements.txt               # Python dependencies
├── CLAUDE.md                      # Claude Code instructions
├── PAYMENT_FLOW_DOCUMENTATION.md  # Detailed payment flow
└── README.md                      # This file
```

## Code Generation (ATAMS)

Generate CRUD scaffolding with ATAMS toolkit:

```bash
# Generate complete CRUD resource
atams generate [resource_name]

# Example: Generate department resource
atams generate department
```

This creates:

-   Model in `app/models/`
-   Schema in `app/schemas/`
-   Repository in `app/repositories/`
-   Service in `app/services/`
-   Router in `app/api/v1/endpoints/`

## Important Implementation Notes

### When Adding New Features

1. Check if ATAMS toolkit provides the functionality first
2. Follow layer separation: API → Service → Repository → Model
3. Use ATAMS exception classes: `NotFoundException`, `BadRequestException`, etc.
4. All async operations (Xendit calls) use `httpx.AsyncClient`

### Database Operations

-   Always use repository methods for database access
-   Commit/rollback happens at service layer, not repository layer
-   Use `joinedload` for relationship loading (avoid N+1 queries)
-   Index critical query columns: `external_id`, `status`, `created_at`

### Logging

```python
from atams.logging import get_logger
logger = get_logger(__name__)

logger.info("Transaction created", extra={"external_id": external_id})
```

### Error Handling

ATAMS provides automatic exception handling:

-   `NotFoundException` → 404
-   `BadRequestException` → 400
-   `UnprocessableEntityException` → 422
-   `InternalServerException` → 500

## Documentation References

-   Payment flow details: [PAYMENT_FLOW_DOCUMENTATION.md](PAYMENT_FLOW_DOCUMENTATION.md)
-   API specifications: [docs/endpoint.md](docs/endpoint.md)
-   Project instructions: [CLAUDE.md](CLAUDE.md)
-   ATAMS toolkit: See official ATAMS documentation

## Support

For questions or issues:

-   Project repository: [GitHub Issues](https://github.com/[username]/photobox-api/issues)
-   ATAMS toolkit: See ATAMS documentation
-   Xendit integration: [Xendit API Docs](https://developers.xendit.co/)
