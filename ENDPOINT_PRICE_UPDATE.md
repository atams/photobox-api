# Endpoint Update for Price Feature

## New Endpoints - Master Price

### 1. Create Price

```http
POST /api/v1/prices
Content-Type: application/json

{
  "price": 40000,
  "description": "Event Special Price",
  "quota": 100
}
```

**Response 201 Created:**

```json
{
    "code": 201,
    "message": "Price created successfully",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "price": 40000.0,
        "description": "Event Special Price",
        "quota": 100,
        "is_active": true,
        "created_at": "2025-12-15T10:30:00",
        "updated_at": null
    }
}
```

**Validation Rules:**

-   `price`: Required, integer, > 0
-   `description`: Optional, max 255 characters
-   `quota`: Optional, integer, > 0 or null (unlimited)

---

### 2. Deactivate Price (Soft Delete)

```http
PATCH /api/v1/prices/{price_id}/deactivate
```

**Response 200 OK:**

```json
{
    "code": 200,
    "message": "Price deactivated successfully",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "price": 40000.0,
        "description": "Event Special Price",
        "quota": 100,
        "is_active": false,
        "created_at": "2025-12-15T10:30:00",
        "updated_at": "2025-12-15T11:00:00"
    }
}
```

**Error Cases:**

-   `404`: Price not found
-   `400`: Price already inactive

---

### 3. Activate Price

```http
PATCH /api/v1/prices/{price_id}/activate
```

**Response 200 OK:**

```json
{
    "code": 200,
    "message": "Price activated successfully",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "price": 40000.0,
        "description": "Event Special Price",
        "quota": 100,
        "is_active": true,
        "created_at": "2025-12-15T10:30:00",
        "updated_at": "2025-12-15T11:30:00"
    }
}
```

**Error Cases:**

-   `404`: Price not found
-   `400`: Price already active

---

## Updated Endpoints - Transactions

### 4. Create Transaction (UPDATED)

```http
POST /api/v1/transactions
Content-Type: application/json

{
  "location_id": 2,
  "price_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Changes:**

-   **New Field**: `price_id` (required, UUID)
-   Removed hardcoded `PHOTOBOX_AMOUNT = 40000`
-   Amount now fetched from `master_price` table

**Response 201 Created:**

```json
{
    "code": 201,
    "message": "Transaction created successfully",
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "external_id": "TRX-2-20251215103045-A1B2C3D4",
        "location_id": 2,
        "location": {
            "id": 2,
            "machine_code": "123023582"
        },
        "price_id": "550e8400-e29b-41d4-a716-446655440000",
        "price": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "price": 40000.0
        },
        "status": "PENDING",
        "qr_string": "00020101021226660...",
        "created_at": "2025-12-15T10:30:45"
    }
}
```

**New Validation:**

-   `price_id`: Must exist in `master_price` table
-   `price_id`: Must be active (`mp_is_active = true`)
-   `price_id`: Must have available quota (if quota is set)

**Error Cases:**

-   `404`: Price not found
-   `400`: Price is inactive
-   `422`: Price quota exceeded

---

### 5. Get Transaction by External ID (UPDATED)

```http
GET /api/v1/transactions/external/{external_id}
```

**Response 200 OK:**

```json
{
    "code": 200,
    "message": "Transaction retrieved successfully",
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "external_id": "TRX-2-20251215103045-A1B2C3D4",
        "location_id": 2,
        "location": {
            "id": 2,
            "machine_code": "123023582"
        },
        "price_id": "550e8400-e29b-41d4-a716-446655440000",
        "price": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "price": 40000.0
        },
        "status": "COMPLETED",
        "qr_string": "00020101021226660...",
        "paid_at": "2025-12-15T10:35:10",
        "created_at": "2025-12-15T10:30:45"
    }
}
```

**Changes:**

-   **New Field**: `price_id` in response
-   **New Nested Object**: `price` (joinedload from master_price)
-   **Removed Field**: `amount` (use `price.price` instead)

---

### 6. Get Transaction by ID (UPDATED)

```http
GET /api/v1/transactions/{transaction_id}
```

**Response:** Same structure as Get by External ID

**Changes:**

-   Same price relationship as external ID endpoint

---

## Business Logic Changes

### Transaction Creation Flow (Updated)

1. **Validate price_id**:

    - Check if price exists
    - Check if price is active
    - Check if quota available (if quota is set)

2. **Decrement quota**:

    - If `mp_quota` is not NULL:
        - Count existing transactions with this `price_id`
        - If count >= quota, return error 422
    - This check happens BEFORE creating transaction

3. **Create transaction**:

    - Use `price.mp_price` as transaction amount
    - Store `price_id` in `tr_price_id`

4. **Generate QRIS**:
    - Pass dynamic amount to Xendit (from price table)

### Quota Management Logic

```python
# Pseudo-code for quota check
if price.quota is not None:
    used_quota = count_transactions_by_price(price_id)
    if used_quota >= price.quota:
        raise QuotaExceededException()
```

**Note**: Quota is checked but NOT decremented. We simply count existing transactions.

---

## Database Relationship Diagram

```
master_locations          master_price
+------------------+      +------------------+
| ml_id (PK)       |      | mp_id (PK)       |
| ml_name          |      | mp_price         |
| ml_address       |      | mp_description   |
| ml_is_active     |      | mp_quota         |
+------------------+      | mp_is_active     |
        |                 | created_at       |
        |                 | updated_at       |
        |                 +------------------+
        |                         |
        |                         |
        +----------+   +----------+
                   |   |
              transactions
        +-------------------------+
        | tr_id (PK)              |
        | tr_external_id          |
        | tr_location_id (FK) ----+
        | tr_price_id (FK) -------+
        | tr_status               |
        | tr_qr_string            |
        | tr_qris_id              |
        | tr_paid_at              |
        | created_at              |
        | updated_at              |
        +-------------------------+
```

---

## Migration Notes

1. **Existing Transactions**:

    - Run DDL to add `tr_price_id` column (nullable initially)
    - Create default price entry
    - Optionally backfill existing transactions with default price_id

2. **Breaking Changes**:

    - Frontend MUST send `price_id` in transaction creation
    - Old transaction creation without `price_id` will fail validation

3. **Backward Compatibility**:
    - None. This is a breaking change requiring frontend update.

---

## Testing Checklist

### Price Endpoints

-   [ ] Create price with all fields
-   [ ] Create price with minimal fields (quota=null)
-   [ ] Create price with invalid amount (negative, zero)
-   [ ] Deactivate active price
-   [ ] Deactivate already inactive price (should fail)
-   [ ] Deactivate non-existent price (404)
-   [ ] Activate inactive price
-   [ ] Activate already active price (should fail)
-   [ ] Activate non-existent price (404)

### Transaction Endpoints

-   [ ] Create transaction with valid price_id
-   [ ] Create transaction with inactive price (should fail)
-   [ ] Create transaction with non-existent price (404)
-   [ ] Create transaction when quota exceeded (422)
-   [ ] Get transaction includes price relationship
-   [ ] Transaction amount matches price.mp_price

### Integration Flow

-   [ ] Create price → Create transaction → Verify amount matches
-   [ ] Create price with quota=5 → Create 6 transactions → 6th fails
-   [ ] Deactivate price → Try create transaction → Fails with 400
-   [ ] Deactivate price → Activate price → Create transaction → Success
