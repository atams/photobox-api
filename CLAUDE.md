# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Photobox API - A FastAPI-based QRIS payment system for photobox kiosks, built with the ATAMS toolkit. Integrates with Xendit for QRIS payment processing with a polling-based payment status architecture.

## Development Commands

### Setup and Running

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python migrations/migrate.py up

# Run development server
uvicorn app.main:app --reload

# Access API
# - Swagger Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### ATAMS Code Generation

```bash
# Generate CRUD for a new resource
atams generate <resource_name>

# Example: Generate department resource with model, schema, repository, service, and endpoints
atams generate department
```

## Architecture

### Payment Flow Architecture

This system uses a **polling-based architecture** for real-time payment status updates:

1. **Frontend → Backend**: Create transaction + generate QRIS
2. **Backend → Xendit**: Request QRIS generation with 15-minute expiration
3. **Xendit → Backend**: Webhook notification when payment completes
4. **Frontend → Backend**: Poll every 3 seconds to detect status changes

**Critical**: Frontend NEVER calls Xendit directly. All payment operations flow through the backend API.

### Layer Architecture (ATAMS Pattern)

```
API Layer (endpoints/)
    ↓
Service Layer (services/)
    ↓
Repository Layer (repositories/)
    ↓
Model Layer (models/)
```

**Key Principle**: Business logic lives in the Service layer. Repositories handle only database operations.

### Database Schema

-   **Schema**: `photobox`
-   **Tables**:
    -   `master_locations`: Photobox machine locations
    -   `transactions`: Payment transactions with QRIS data

**Naming Convention**: All table columns use prefixes (`tr_`, `ml_`) matching table abbreviations.

### Service Layer Patterns

**TransactionService**:

-   Orchestrates transaction creation with Xendit QRIS generation
-   Fixed amount: Rp 40,000 (hardcoded constant `PHOTOBOX_AMOUNT`)
-   Auto-generates external IDs: `TRX-{location_id}-{timestamp}-{random}`
-   Handles webhook processing from Xendit

**XenditService**:

-   Uses Basic Auth with Base64-encoded API key
-   Sets QRIS expiration to exactly 15 minutes from creation
-   Returns `qr_string` for frontend QR code display

### Repository Layer Patterns

All repositories extend `BaseRepository[T]` from ATAMS toolkit:

-   Standard CRUD operations inherited from base
-   Custom queries use SQLAlchemy ORM with `joinedload` for relationships
-   Transaction isolation handled at service layer with `db.commit()`

### Authentication & Authorization

Uses **Atlas SSO** integration from ATAMS toolkit for admin endpoints.

#### SSO Configuration

Four required environment variables:

-   `ATLAS_SSO_URL`: SSO service endpoint (e.g., `https://api.atlas-microapi.atamsindonesia.com/api/v1`)
-   `ATLAS_APP_CODE`: Application identifier (must match `app_code` in Atlas SSO response: `PHOTOBOX_API`)
-   `ATLAS_ENCRYPTION_KEY`: 32-character key for SSO token decryption
-   `ATLAS_ENCRYPTION_IV`: 16-character IV for SSO token decryption

#### Role-Based Access Control (RBAC)

**Admin Role** (`role_level <= 10`):

-   Full access to master data management
-   Can create, read, and update locations
-   Can create, read, and update prices
-   Can view all transactions and transaction details (reporting)

**Protected Endpoints** (Admin only):

```
Locations:
- POST   /api/v1/locations        # Create location
- GET    /api/v1/locations        # List locations
- GET    /api/v1/locations/{id}   # Get location detail
- PUT    /api/v1/locations/{id}   # Update location

Prices:
- POST   /api/v1/prices                    # Create price
- GET    /api/v1/prices                    # List prices
- PATCH  /api/v1/prices/{id}/activate      # Activate price
- PATCH  /api/v1/prices/{id}/deactivate    # Deactivate price

Transactions (Admin reporting):
- GET    /api/v1/transactions              # List all transactions
- GET    /api/v1/transactions/{id}         # Get transaction detail by ID
```

**Public Endpoints** (No authentication required):

```
Transactions (Customer-facing):
- POST   /api/v1/transactions                          # Create transaction + QRIS
- GET    /api/v1/transactions/external/{external_id}   # Poll transaction status

Photos:
- GET    /api/v1/photos/list                          # Get transaction photos

Webhooks:
- POST   /api/v1/webhooks/xendit                      # Xendit payment callback (protected by x-callback-token)

Templates:
- GET    /gallery/{external_id}                       # Photo gallery page
```

#### SSO Implementation Pattern

**Dependencies** ([app/api/deps.py](app/api/deps.py)):

```python
from atams.sso import create_atlas_client, create_auth_dependencies
from app.core.config import settings

atlas_client = create_atlas_client(settings)
get_current_user, require_auth, require_min_role_level, require_role_level = create_auth_dependencies(atlas_client)
```

**Endpoint Protection**:

```python
from app.api.deps import require_auth, require_min_role_level

@router.post(
    "/locations",
    dependencies=[Depends(require_min_role_level(10))]  # Admin only
)
async def create_location(
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth)  # Extract user info
):
    # current_user contains: u_id, u_username, u_email, u_full_name, roles
    return await location_service.create_location(db, data)
```

**Atlas SSO Response Structure**:

```json
{
    "success": true,
    "message": "User info retrieved successfully",
    "data": {
        "u_id": 2,
        "u_username": "admin",
        "u_email": "admin@example.com",
        "u_full_name": "Administrator",
        "u_status": "active",
        "roles": [
            {
                "role_id": 25,
                "role_code": "ADMIN",
                "role_name": "Administrator",
                "role_level": 10,
                "app_id": 20,
                "app_name": "photobox_api",
                "app_code": "PHOTOBOX_API"
            }
        ]
    }
}
```

**IMPORTANT**:

-   Atlas SSO response is **encrypted** (ATAMS toolkit handles decryption automatically)
-   `app_code` in response must match `ATLAS_APP_CODE` environment variable
-   Admin check uses `role_level <= 10` (NOT `>= 10`)
-   JWT token must be sent in `Authorization: Bearer <token>` header

### Response Encryption

The API supports AES-256-CBC encryption for sensitive endpoints. When enabled, responses are encrypted before being sent to the client.

**Encrypted Endpoints:**

-   `GET /api/v1/transactions/external/{external_id}` - Transaction polling endpoint
-   `GET /api/v1/transactions/{external_id}/photos` - Photos list endpoint

**Configuration:**

-   `ENCRYPTION_ENABLED`: Enable/disable response encryption (default: false)
-   `ENCRYPTION_KEY`: 32-character AES encryption key
-   `ENCRYPTION_IV`: 16-character initialization vector

**Response Format (when encrypted):**

```json
{
    "data": "base64_encoded_encrypted_payload"
}
```

**Encryption Details:**

-   Algorithm: AES-256-CBC
-   Padding: PKCS7
-   Output: Base64-encoded encrypted JSON
-   Frontend must decrypt using the same key and IV

**Implementation Files:**

-   Encryption service: `app/core/encryption.py`
-   Response wrapper: `app/utils/response_encryption.py`

### Webhook Security

Xendit webhook endpoint (`/api/v1/webhooks/xendit`) validates:

1. Presence of `x-callback-token` header
2. Token matches `XENDIT_CALLBACK_TOKEN` from environment
3. Returns 401/403 on validation failure

## Configuration Notes

### Database Connection Pooling

Critical for production deployment. Environment variables:

-   `DB_POOL_SIZE`: Base pool size (default: 3)
-   `DB_MAX_OVERFLOW`: Additional connections (default: 5)
-   Total connections = `(DB_POOL_SIZE + DB_MAX_OVERFLOW) × app_instances`

**Important**: For Aiven free tier (20 connection limit), keep defaults. Adjust for production based on database limits.

### Xendit Configuration

Three required environment variables:

-   `XENDIT_API_KEY`: Secret key from Xendit dashboard
-   `XENDIT_WEBHOOK_URL`: Public URL for webhook callbacks (must be publicly accessible)
-   `XENDIT_CALLBACK_TOKEN`: Webhook verification token from Xendit dashboard

**Note**: `XENDIT_WEBHOOK_URL` must be configured in both `.env` AND Xendit dashboard settings.

### CORS Configuration

CORS (Cross-Origin Resource Sharing) controls which frontend domains can access the API. Configured via environment variables:

**Environment Variables:**

-   `CORS_ORIGINS`: Comma-separated list of allowed origins (no spaces!)
-   `CORS_ALLOW_CREDENTIALS`: Allow credentials (cookies, auth headers) - set to `true` for SSO
-   `CORS_ALLOW_METHODS`: HTTP methods allowed (default: GET,POST,PUT,PATCH,DELETE,OPTIONS)
-   `CORS_ALLOW_HEADERS`: Headers allowed (default: `*` for all headers)

**Configuration Examples:**

```env
# Development + Production (recommended - allows localhost + all atamsindonesia.com subdomains)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://*.atamsindonesia.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Production only (wildcard subdomain for atamsindonesia.com)
CORS_ORIGINS=https://*.atamsindonesia.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Production (specific domains only)
CORS_ORIGINS=https://photobox-frontend.com,https://admin.photobox.com,https://*.atamsindonesia.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Allow all origins (NOT recommended for production!)
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=false
```

**Wildcard Subdomain Support:**

-   `https://*.atamsindonesia.com` will allow:
    -   `https://api.atamsindonesia.com`
    -   `https://admin.atamsindonesia.com`
    -   `https://photobox.atamsindonesia.com`
    -   Any other subdomain of `atamsindonesia.com`

**Important Security Notes:**

-   ✅ **Production**: Use specific domain(s) or wildcard subdomain (e.g., `https://*.atamsindonesia.com`)
-   ✅ **Development**: Use localhost ports (e.g., `http://localhost:3000,http://localhost:5173`)
-   ✅ **Wildcard subdomain**: `https://*.atamsindonesia.com` allows all subdomains (secure for your organization)
-   ❌ **Never use `*` in production** - it allows ANY website to call your API
-   ✅ Set `CORS_ALLOW_CREDENTIALS=true` if using Atlas SSO (required for JWT tokens)

**CORS Middleware Location:**

-   Configured in: [app/main.py](app/main.py:40-47)
-   Settings from: [app/core/config.py](app/core/config.py:13) (inherited from `AtamsBaseSettings`)

## Frontend Integration

### Polling Strategy

Frontend must implement 3-second polling on `/api/v1/transactions/external/{external_id}` endpoint:

-   Start immediately after transaction creation
-   Stop when status reaches terminal state: `COMPLETED`, `FAILED`, or `EXPIRED`
-   Maximum polling duration: 15 minutes (matches QRIS expiration)

### QR Code Display

The `qr_string` field contains the full QRIS payload. Frontend converts this to a QR code image using a library (e.g., `qrcode.js`).

### Transaction Status Flow

```
PENDING → COMPLETED (success)
PENDING → FAILED (payment error)
PENDING → EXPIRED (15 min timeout)
```

Status transitions are one-way only. Terminal states are final.

## Database Migrations

### Running Migrations

The project includes migration scripts for database schema management:

```bash
# Check migration status
python migrations/migrate.py status

# Apply all migrations
python migrations/migrate.py up

# Rollback last migration
python migrations/migrate.py down

# Rollback specific migration
python migrations/migrate.py down 001
```

**Alternative (Bash):**

```bash
./migrations/migrate.sh status
./migrations/migrate.sh up
./migrations/migrate.sh down
```

### Migration Files Structure

```
migrations/
├── 001_initial_schema.sql            # Initial schema creation
├── 001_initial_schema_rollback.sql   # Rollback script
├── migrate.py                         # Python migration tool
├── migrate.sh                         # Bash migration tool
├── requirements.txt                   # Migration dependencies
└── README.md                          # Migration documentation
```

### Creating New Migrations

1. Create new migration file: `002_description.sql`
2. Create rollback file: `002_description_rollback.sql`
3. Follow sequential numbering (001, 002, 003, etc.)
4. Test in development before applying to production
5. Always create both forward and rollback scripts

**Migration Template:**

```sql
-- Migration: 002_add_feature
-- Description: Brief description of the migration
-- Author: Your name
-- Date: YYYY-MM-DD

-- Your SQL here
```

### Initial Migration

The `001_initial_schema.sql` includes:

-   Schema creation: `photobox`
-   Tables: `master_locations`, `master_price`, `transactions`
-   Indexes for performance
-   Foreign key constraints
-   Sample seed data (optional)

## Testing

### Manual Testing with cURL

#### Testing SSO Protected Endpoints

**Get Atlas SSO Token** (login first via Atlas SSO UI, then extract JWT token from browser):

```bash
# Set your JWT token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Test protected endpoint - List Locations (Admin only)
curl -X GET http://localhost:8000/api/v1/locations \
  -H "Authorization: Bearer $TOKEN"

# Test protected endpoint - Create Location (Admin only)
curl -X POST http://localhost:8000/api/v1/locations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "machine_code": "PB-001",
    "name": "Photobox Mall Kelapa Gading",
    "address": "Mall Kelapa Gading, Jakarta",
    "is_active": true
  }'

# Test protected endpoint - List Prices (Admin only)
curl -X GET http://localhost:8000/api/v1/prices \
  -H "Authorization: Bearer $TOKEN"

# Test protected endpoint - List Transactions (Admin only)
# With date range filter
curl -X GET "http://localhost:8000/api/v1/transactions?date_from=2025-01-01&date_to=2025-12-31&page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Without date filter (show all transactions)
curl -X GET "http://localhost:8000/api/v1/transactions?page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# With only date_from (date_to auto-set to 1 year ahead)
curl -X GET "http://localhost:8000/api/v1/transactions?date_from=2025-01-01&page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# With only date_to (date_from auto-set to 1 year before)
curl -X GET "http://localhost:8000/api/v1/transactions?date_to=2025-12-31&page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Test protected endpoint - Get Transaction Detail by ID (Admin only)
curl -X GET http://localhost:8000/api/v1/transactions/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Responses**:

-   **Without token** or **invalid token**: `401 Unauthorized`
-   **With valid token but wrong role** (`role_level > 10`): `403 Forbidden`
-   **With valid admin token** (`role_level <= 10`): `200 OK` with data

#### Testing Public Endpoints

**Create Transaction**:

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"location_id": 2}'
```

**Check Status (Polling)**:

```bash
curl http://localhost:8000/api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

**Simulate Webhook (Development Only)**:

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

**Note**: The `paid_at` timestamp is automatically set to the current time when `status` is `COMPLETED`. No need to include it in the webhook payload.

## Important Implementation Notes

### When Adding New Features

1. Check if ATAMS toolkit provides the functionality before implementing
2. Follow the existing layer separation: API → Service → Repository → Model
3. Use ATAMS exception classes: `NotFoundException`, `BadRequestException`, `UnprocessableEntityException`, etc.
4. All async operations (Xendit calls) use `httpx.AsyncClient`

### Database Operations

-   Always use repository methods for database access
-   Commit/rollback happens at service layer, not repository layer
-   Use `joinedload` for relationship loading to avoid N+1 queries
-   Index critical query columns (external_id, status, created_at)

### Logging

Use ATAMS logging: `from atams.logging import get_logger; logger = get_logger(__name__)`

### Error Handling

ATAMS provides automatic exception handling middleware. Raise appropriate ATAMS exceptions:

-   `NotFoundException` → 404
-   `BadRequestException` → 400
-   `UnprocessableEntityException` → 422
-   `InternalServerException` → 500

## Documentation References

-   Full payment flow documentation: [PAYMENT_FLOW_DOCUMENTATION.md](PAYMENT_FLOW_DOCUMENTATION.md)
-   API endpoint specifications: [docs/endpoint.md](docs/endpoint.md)
-   ATAMS toolkit documentation: See official ATAMS docs
