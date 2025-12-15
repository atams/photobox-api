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
- **Schema**: `photobox`
- **Tables**:
  - `master_locations`: Photobox machine locations
  - `transactions`: Payment transactions with QRIS data

**Naming Convention**: All table columns use prefixes (`tr_`, `ml_`) matching table abbreviations.

### Service Layer Patterns

**TransactionService**:
- Orchestrates transaction creation with Xendit QRIS generation
- Fixed amount: Rp 40,000 (hardcoded constant `PHOTOBOX_AMOUNT`)
- Auto-generates external IDs: `TRX-{location_id}-{timestamp}-{random}`
- Handles webhook processing from Xendit

**XenditService**:
- Uses Basic Auth with Base64-encoded API key
- Sets QRIS expiration to exactly 15 minutes from creation
- Returns `qr_string` for frontend QR code display

### Repository Layer Patterns
All repositories extend `BaseRepository[T]` from ATAMS toolkit:
- Standard CRUD operations inherited from base
- Custom queries use SQLAlchemy ORM with `joinedload` for relationships
- Transaction isolation handled at service layer with `db.commit()`

### Authentication & Authorization
Uses **Atlas SSO** integration from ATAMS toolkit:
- `ATLAS_SSO_URL`: SSO service endpoint
- `ATLAS_APP_CODE`: Application identifier
- `ATLAS_ENCRYPTION_KEY` + `ATLAS_ENCRYPTION_IV`: For SSO token decryption

Response encryption is available but optional (`ENCRYPTION_ENABLED` flag).

### Webhook Security
Xendit webhook endpoint (`/api/v1/webhooks/xendit`) validates:
1. Presence of `x-callback-token` header
2. Token matches `XENDIT_CALLBACK_TOKEN` from environment
3. Returns 401/403 on validation failure

## Configuration Notes

### Database Connection Pooling
Critical for production deployment. Environment variables:
- `DB_POOL_SIZE`: Base pool size (default: 3)
- `DB_MAX_OVERFLOW`: Additional connections (default: 5)
- Total connections = `(DB_POOL_SIZE + DB_MAX_OVERFLOW) × app_instances`

**Important**: For Aiven free tier (20 connection limit), keep defaults. Adjust for production based on database limits.

### Xendit Configuration
Three required environment variables:
- `XENDIT_API_KEY`: Secret key from Xendit dashboard
- `XENDIT_WEBHOOK_URL`: Public URL for webhook callbacks (must be publicly accessible)
- `XENDIT_CALLBACK_TOKEN`: Webhook verification token from Xendit dashboard

**Note**: `XENDIT_WEBHOOK_URL` must be configured in both `.env` AND Xendit dashboard settings.

## Frontend Integration

### Polling Strategy
Frontend must implement 3-second polling on `/api/v1/transactions/external/{external_id}` endpoint:
- Start immediately after transaction creation
- Stop when status reaches terminal state: `COMPLETED`, `FAILED`, or `EXPIRED`
- Maximum polling duration: 15 minutes (matches QRIS expiration)

### QR Code Display
The `qr_string` field contains the full QRIS payload. Frontend converts this to a QR code image using a library (e.g., `qrcode.js`).

### Transaction Status Flow
```
PENDING → COMPLETED (success)
PENDING → FAILED (payment error)
PENDING → EXPIRED (15 min timeout)
```

Status transitions are one-way only. Terminal states are final.

## Testing

### Manual Testing with cURL

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
- Always use repository methods for database access
- Commit/rollback happens at service layer, not repository layer
- Use `joinedload` for relationship loading to avoid N+1 queries
- Index critical query columns (external_id, status, created_at)

### Logging
Use ATAMS logging: `from atams.logging import get_logger; logger = get_logger(__name__)`

### Error Handling
ATAMS provides automatic exception handling middleware. Raise appropriate ATAMS exceptions:
- `NotFoundException` → 404
- `BadRequestException` → 400
- `UnprocessableEntityException` → 422
- `InternalServerException` → 500

## Documentation References
- Full payment flow documentation: [PAYMENT_FLOW_DOCUMENTATION.md](PAYMENT_FLOW_DOCUMENTATION.md)
- API endpoint specifications: [docs/endpoint.md](docs/endpoint.md)
- ATAMS toolkit documentation: See official ATAMS docs
