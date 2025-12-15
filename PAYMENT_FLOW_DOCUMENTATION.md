# Payment Flow Documentation - Photobox QRIS Integration

## Overview

Dokumentasi ini menjelaskan **end-to-end payment flow** menggunakan Xendit QRIS untuk aplikasi Photobox/Kiosk. Flow ini dirancang dengan strategi **polling** untuk memberikan real-time payment status update kepada user.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Complete Payment Flow](#complete-payment-flow)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Frontend Implementation Guide](#frontend-implementation-guide)
5. [Error Handling](#error-handling)
6. [Configuration](#configuration)
7. [Testing](#testing)

---

## Architecture Overview

```
┌─────────────┐
│  FRONTEND   │
│  (Kiosk)    │
└──────┬──────┘
       │
       │ 1. Create Transaction
       │    POST /api/v1/transactions
       ↓
┌─────────────────┐
│   BACKEND       │
│   (FastAPI)     │
└────────┬────────┘
         │
         │ 2. Generate QRIS
         ↓
    ┌────────┐
    │ XENDIT │
    └────┬───┘
         │
         │ 3. Webhook (Payment Completed)
         │    POST /webhooks/xendit
         ↓
┌─────────────────┐
│   BACKEND       │ ← Update Status di Database
└─────────────────┘
         ↑
         │ 4. Polling Status
         │    GET /transactions/external/{id}
         │    (Every 3 seconds)
┌─────────────┐
│  FRONTEND   │
└─────────────┘
```

**Key Points:**
- Frontend **HANYA** berinteraksi dengan Backend (tidak langsung ke Xendit)
- Xendit **otomatis** hit webhook ke Backend saat payment completed
- Frontend **polling** endpoint status untuk mendapatkan update real-time

---

## Complete Payment Flow

### Step 1: Create Transaction & Generate QRIS

**Trigger:** User memulai session photobox

**Frontend Action:**
```javascript
POST /api/v1/transactions
Headers:
  Content-Type: application/json
Body:
{
  "location_id": 2
}
```

**Backend Process:**
1. Validate location (harus exist dan active)
2. Generate unique `external_id` dengan format: `TRX-{location_id}-{timestamp}-{random}`
3. Call Xendit API untuk generate QRIS code
4. Set expiration time: **15 minutes** dari sekarang
5. Save transaction ke database dengan status `PENDING`
6. Return response ke frontend

**Response:**
```json
{
  "transaction_id": 123,
  "external_id": "TRX-2-20251215092229-57283A15",
  "amount": 40000,
  "status": "PENDING",
  "qr_string": "00020101021126580...",
  "created_at": "2025-12-15T09:22:29.123Z"
}
```

**Frontend Next Action:**
- Display QR code dari `qr_string`
- Save `external_id` untuk polling
- Start polling timer

---

### Step 2: Display QR Code

**Frontend Action:**
1. Convert `qr_string` menjadi QR code image menggunakan library (e.g., `qrcode.js`)
2. Display QR code di screen
3. Tampilkan amount: **Rp 40.000**
4. Tampilkan countdown timer: **15 menit**
5. Tampilkan instruksi: "Scan QR code dengan aplikasi e-wallet Anda"

**Example UI:**
```
╔════════════════════════════╗
║   SCAN UNTUK MEMBAYAR      ║
║                            ║
║   ┌──────────────────┐     ║
║   │                  │     ║
║   │   [QR CODE]      │     ║
║   │                  │     ║
║   └──────────────────┘     ║
║                            ║
║   Rp 40.000                ║
║   Expired in: 14:59        ║
╚════════════════════════════╝
```

---

### Step 3: Start Polling

**Frontend Action:**
Start polling **immediately** after receiving transaction response

**Polling Strategy:**
```javascript
const pollInterval = 3000; // 3 seconds
const maxDuration = 15 * 60 * 1000; // 15 minutes
let startTime = Date.now();

const pollingTimer = setInterval(async () => {
  // Check if expired
  if (Date.now() - startTime > maxDuration) {
    clearInterval(pollingTimer);
    showExpiredMessage();
    return;
  }

  // Poll status
  const response = await fetch(
    `/api/v1/transactions/external/${externalId}`
  );
  const data = await response.json();

  // Check status
  if (data.status === 'COMPLETED') {
    clearInterval(pollingTimer);
    showSuccessMessage(data);
    return;
  }

  if (data.status === 'FAILED' || data.status === 'EXPIRED') {
    clearInterval(pollingTimer);
    showFailedMessage(data);
    return;
  }

  // Status still PENDING, continue polling
}, pollInterval);
```

**API Call:**
```javascript
GET /api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

**Response (While Pending):**
```json
{
  "transaction_id": 123,
  "external_id": "TRX-2-20251215092229-57283A15",
  "amount": 40000,
  "status": "PENDING",
  "qr_string": "00020101021126580...",
  "paid_at": null,
  "location": {
    "id": 2,
    "name": "Booth A"
  }
}
```

---

### Step 4: User Scans QR Code

**User Action:**
1. Buka aplikasi e-wallet (GoPay, OVO, Dana, ShopeePay, dll)
2. Pilih "Scan QR"
3. Scan QR code yang ditampilkan di screen
4. Confirm payment di aplikasi

**What Happens:**
- Payment diproses oleh e-wallet provider
- E-wallet provider notify Xendit
- Xendit process payment

---

### Step 5: Xendit Sends Webhook (Backend Only)

**⚠️ IMPORTANT: Frontend TIDAK terlibat di step ini!**

**Xendit Action:**
Xendit automatically sends webhook to backend:

```javascript
POST https://your-domain.com/api/v1/webhooks/xendit
Headers:
  Content-Type: application/json
  x-callback-token: xnd_development_xxxxx  // Auto-sent by Xendit
Body:
{
  "external_id": "TRX-2-20251215092229-57283A15",
  "status": "COMPLETED",
  "xendit_id": "qr_5d408580-80cf-471a-a69f-976daadf1b84",
  "paid_at": "2025-12-15T09:25:10.878Z"
}
```

**Backend Process:**
1. Verify `x-callback-token` header (security check)
2. Find transaction by `external_id`
3. Update status to `COMPLETED`
4. Set `paid_at` timestamp
5. Save to database
6. Return success response to Xendit

**Response to Xendit:**
```json
{
  "message": "Transaction updated"
}
```

**Frontend:** Tidak perlu tahu tentang webhook ini!

---

### Step 6: Polling Detects Status Change

**Frontend Polling (Next Cycle):**

Pada polling cycle berikutnya (max 3 detik setelah payment):

```javascript
GET /api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

**Response (After Payment):**
```json
{
  "transaction_id": 123,
  "external_id": "TRX-2-20251215092229-57283A15",
  "amount": 40000,
  "status": "COMPLETED",  // ✅ Changed!
  "qr_string": "00020101021126580...",
  "paid_at": "2025-12-15T09:25:10.878Z",  // ✅ Now has value
  "location": {
    "id": 2,
    "name": "Booth A"
  }
}
```

**Frontend Detection:**
```javascript
if (data.status === 'COMPLETED') {
  clearInterval(pollingTimer);
  showSuccessMessage();
  proceedToNextStep(); // Start photo session, etc.
}
```

---

### Step 7: Show Success & Proceed

**Frontend Action:**
1. Stop polling
2. Hide QR code
3. Show success animation/message
4. Proceed to next step (photo session)

**Example UI:**
```
╔════════════════════════════╗
║   ✅ PEMBAYARAN BERHASIL   ║
║                            ║
║   Rp 40.000                ║
║   Paid at: 09:25           ║
║                            ║
║   Memulai sesi foto...     ║
╚════════════════════════════╝
```

---

## API Endpoints Reference

### 1. Create Transaction

**Endpoint:** `POST /api/v1/transactions`

**Purpose:** Create new transaction and generate QRIS code

**Request:**
```json
{
  "location_id": 2
}
```

**Response (201 Created):**
```json
{
  "transaction_id": 123,
  "external_id": "TRX-2-20251215092229-57283A15",
  "amount": 40000,
  "status": "PENDING",
  "qr_string": "00020101021126580009ID.CO.QRIS...",
  "created_at": "2025-12-15T09:22:29.123Z"
}
```

**Errors:**
- `404` - Location not found
- `422` - Location is not active
- `500` - Xendit API error

**Frontend Usage:**
- Call **once** saat user mulai session
- Save `external_id` untuk polling
- Display `qr_string` as QR code

---

### 2. Get Transaction Status (Polling Endpoint)

**Endpoint:** `GET /api/v1/transactions/external/{external_id}`

**Purpose:** Get current transaction status (designed for polling)

**Request:**
```
GET /api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

**Response (200 OK):**
```json
{
  "transaction_id": 123,
  "external_id": "TRX-2-20251215092229-57283A15",
  "amount": 40000,
  "status": "PENDING",  // or "COMPLETED", "FAILED", "EXPIRED"
  "qr_string": "00020101021126580...",
  "paid_at": null,  // or "2025-12-15T09:25:10.878Z" if completed
  "location": {
    "id": 2,
    "name": "Booth A"
  }
}
```

**Errors:**
- `404` - Transaction not found

**Frontend Usage:**
- Poll **every 3 seconds** after creating transaction
- Stop polling when status changes to: `COMPLETED`, `FAILED`, or `EXPIRED`
- Stop polling after **15 minutes**
- **Lightweight endpoint** - safe untuk frequent calls

**Performance:**
- Optimized with database indexing
- Minimal query overhead
- Supports concurrent polling dari multiple kiosks

---

### 3. Webhook Endpoint (Backend Only)

**Endpoint:** `POST /api/v1/webhooks/xendit`

**Purpose:** Receive payment notifications from Xendit

**⚠️ Frontend NEVER calls this endpoint!**

**Request (from Xendit):**
```json
{
  "external_id": "TRX-2-20251215092229-57283A15",
  "status": "COMPLETED",
  "xendit_id": "qr_5d408580-80cf-471a-a69f-976daadf1b84",
  "paid_at": "2025-12-15T09:25:10.878Z"
}
```

**Security:**
- Requires `x-callback-token` header
- Token verified against environment variable
- Rejects unauthorized requests

**Frontend:** Tidak perlu tahu tentang endpoint ini

---

## Frontend Implementation Guide

### React Example

```javascript
import { useState, useEffect, useRef } from 'react';
import QRCode from 'qrcode';

function PaymentScreen({ locationId }) {
  const [transaction, setTransaction] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, pending, completed, failed, expired
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [timeLeft, setTimeLeft] = useState(15 * 60); // 15 minutes in seconds
  const pollingInterval = useRef(null);
  const timerInterval = useRef(null);

  // Step 1: Create Transaction
  const createTransaction = async () => {
    try {
      const response = await fetch('/api/v1/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location_id: locationId })
      });

      if (!response.ok) throw new Error('Failed to create transaction');

      const data = await response.json();
      setTransaction(data);
      setStatus('pending');

      // Generate QR Code
      const qrUrl = await QRCode.toDataURL(data.qr_string);
      setQrCodeUrl(qrUrl);

      // Start polling
      startPolling(data.external_id);

      // Start countdown timer
      startTimer();
    } catch (error) {
      console.error('Error creating transaction:', error);
      setStatus('failed');
    }
  };

  // Step 2: Polling
  const startPolling = (externalId) => {
    pollingInterval.current = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/v1/transactions/external/${externalId}`
        );

        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();

        // Update transaction data
        setTransaction(data);

        // Check status
        if (data.status === 'COMPLETED') {
          stopPolling();
          setStatus('completed');
        } else if (data.status === 'FAILED') {
          stopPolling();
          setStatus('failed');
        } else if (data.status === 'EXPIRED') {
          stopPolling();
          setStatus('expired');
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000); // Poll every 3 seconds
  };

  const stopPolling = () => {
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
      pollingInterval.current = null;
    }
    if (timerInterval.current) {
      clearInterval(timerInterval.current);
      timerInterval.current = null;
    }
  };

  // Step 3: Countdown Timer
  const startTimer = () => {
    timerInterval.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          stopPolling();
          setStatus('expired');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopPolling();
  }, []);

  // Format time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="payment-screen">
      {status === 'idle' && (
        <button onClick={createTransaction}>Start Payment</button>
      )}

      {status === 'pending' && transaction && (
        <div className="qr-display">
          <h2>Scan untuk Membayar</h2>
          <img src={qrCodeUrl} alt="QR Code" />
          <p className="amount">Rp {transaction.amount.toLocaleString()}</p>
          <p className="timer">Expired in: {formatTime(timeLeft)}</p>
          <p className="instruction">
            Scan QR code dengan aplikasi e-wallet Anda
          </p>
        </div>
      )}

      {status === 'completed' && (
        <div className="success">
          <h2>✅ Pembayaran Berhasil!</h2>
          <p>Rp {transaction.amount.toLocaleString()}</p>
          <p>Paid at: {new Date(transaction.paid_at).toLocaleTimeString()}</p>
        </div>
      )}

      {status === 'expired' && (
        <div className="expired">
          <h2>⏱️ QR Code Expired</h2>
          <button onClick={createTransaction}>Create New Transaction</button>
        </div>
      )}

      {status === 'failed' && (
        <div className="failed">
          <h2>❌ Payment Failed</h2>
          <button onClick={createTransaction}>Try Again</button>
        </div>
      )}
    </div>
  );
}

export default PaymentScreen;
```

---

## Error Handling

### Common Errors & Solutions

| Error | Status Code | Cause | Solution |
|-------|-------------|-------|----------|
| Location not found | 404 | Invalid `location_id` | Verify location exists |
| Location inactive | 422 | Location is disabled | Enable location or use different one |
| Xendit API error | 500 | Xendit service down | Retry or contact support |
| Transaction not found | 404 | Invalid `external_id` | Check transaction was created |
| QRIS expired | - | 15 minutes passed | Create new transaction |

### Frontend Error Handling

```javascript
try {
  const response = await fetch('/api/v1/transactions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location_id: 2 })
  });

  if (!response.ok) {
    const error = await response.json();

    if (response.status === 404) {
      showError('Location tidak ditemukan');
    } else if (response.status === 422) {
      showError('Location tidak aktif');
    } else {
      showError('Gagal membuat transaksi, silakan coba lagi');
    }
    return;
  }

  const data = await response.json();
  // Process success...
} catch (error) {
  showError('Koneksi error, periksa jaringan Anda');
}
```

---

## Configuration

### Backend Environment Variables

Add these to your `.env` file:

```env
# Xendit Configuration
XENDIT_API_KEY=xnd_development_your_api_key_here
XENDIT_WEBHOOK_URL=https://your-domain.com/api/v1/webhooks/xendit
XENDIT_CALLBACK_TOKEN=xnd_development_your_callback_token_here
```

**How to get these values:**

1. **XENDIT_API_KEY:**
   - Login to https://dashboard.xendit.co
   - Go to Settings → Developers → API Keys
   - Copy "Secret Key"

2. **XENDIT_WEBHOOK_URL:**
   - Your public backend URL + `/api/v1/webhooks/xendit`
   - Example: `https://api.photobox.com/api/v1/webhooks/xendit`
   - Must be **publicly accessible** (not localhost)

3. **XENDIT_CALLBACK_TOKEN:**
   - Login to https://dashboard.xendit.co
   - Go to Settings → Webhooks
   - Copy "Callback Verification Token"

### Xendit Dashboard Setup

1. Login to Xendit Dashboard
2. Go to **Settings → Webhooks**
3. Add webhook URL: `https://your-domain.com/api/v1/webhooks/xendit`
4. Select events: `QR Codes` → `qr.payment`
5. Save configuration

---

## Testing

### Manual Testing with cURL

#### 1. Create Transaction
```bash
curl -X POST http://localhost:8080/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"location_id": 2}'
```

#### 2. Check Status (Polling)
```bash
curl http://localhost:8080/api/v1/transactions/external/TRX-2-20251215092229-57283A15
```

#### 3. Simulate Webhook (Testing Only)
```bash
curl -X POST http://localhost:8080/api/v1/webhooks/xendit \
  -H "Content-Type: application/json" \
  -H "x-callback-token: xnd_development_your_token_here" \
  -d '{
    "external_id": "TRX-2-20251215092229-57283A15",
    "status": "COMPLETED",
    "xendit_id": "qr_5d408580-80cf-471a-a69f-976daadf1b84",
    "paid_at": "2025-12-15T09:25:10.878Z"
  }'
```

### Testing Workflow

1. **Create transaction** → Get `external_id`
2. **Poll status** → Should return `PENDING`
3. **Scan QR code** with real e-wallet app OR **simulate webhook** with cURL
4. **Poll status again** → Should return `COMPLETED`

---

## Status Transitions

```
PENDING
  │
  ├─→ COMPLETED (payment successful)
  │
  ├─→ FAILED (payment failed)
  │
  └─→ EXPIRED (15 minutes timeout)
```

**Important:**
- Status can only move forward, never backward
- `COMPLETED`, `FAILED`, and `EXPIRED` are final states
- Stop polling when reaching any final state

---

## Performance Considerations

### Polling Strategy

- **Interval:** 3 seconds (balance between responsiveness and server load)
- **Duration:** Maximum 15 minutes (matches QRIS expiration)
- **Optimization:** Endpoint uses database indexing for fast queries

### Best Practices

1. **Always stop polling:**
   - When status changes to final state
   - When QR code expires
   - When user cancels

2. **Handle network errors:**
   - Don't stop polling on temporary network errors
   - Retry failed polling requests
   - Show network error indicator

3. **Clean up intervals:**
   - Clear intervals in cleanup/unmount
   - Prevent memory leaks

---

## Security Notes

### For Frontend Developers:

1. **NEVER implement webhook endpoint in frontend**
   - Webhook is backend-only
   - Contains sensitive verification logic

2. **NEVER expose Xendit credentials in frontend**
   - All Xendit API calls go through backend
   - Frontend only calls your own API

3. **Trust backend status**
   - Status updates come from verified webhook
   - Polling endpoint returns authoritative data

---

## Support & Contact

**For Backend Issues:**
- Check backend logs
- Verify `.env` configuration
- Test webhook with cURL

**For Xendit Issues:**
- Xendit Dashboard: https://dashboard.xendit.co
- Xendit Documentation: https://docs.xendit.co
- Xendit Support: support@xendit.co

**For Frontend Issues:**
- Verify API endpoint URLs
- Check network tab in browser DevTools
- Confirm polling is running

---

## Changelog

### Version 1.0.0 (2025-12-15)

**Features Implemented:**
- ✅ QRIS expiration time: 15 minutes
- ✅ Webhook verification with callback token
- ✅ Frontend polling support with `qr_string` in response
- ✅ Real-time payment status updates
- ✅ Production-ready security

**Breaking Changes:**
- None (initial release)

---

## Quick Reference Card

| Action | Endpoint | Method | Frequency |
|--------|----------|--------|-----------|
| Create QRIS | `/api/v1/transactions` | POST | Once per session |
| Check Status | `/api/v1/transactions/external/{id}` | GET | Every 3 seconds |
| Webhook | `/api/v1/webhooks/xendit` | POST | Auto by Xendit |

**Payment Amount:** Fixed at **Rp 40.000**

**QRIS Expiration:** **15 minutes**

**Polling Interval:** **3 seconds**

**Stop Polling When:**
- Status is `COMPLETED` ✅
- Status is `FAILED` ❌
- Status is `EXPIRED` ⏱️
- 15 minutes elapsed ⏰

---

**End of Documentation**

For questions or clarifications, contact the backend team.
