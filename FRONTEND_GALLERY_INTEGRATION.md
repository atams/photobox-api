# Frontend Gallery Integration Guide

## Overview

Panduan untuk frontend developer dalam mengimplementasikan halaman gallery untuk menampilkan foto-foto hasil photobox.

---

## 1. URL Structure

Gallery page di frontend harus accessible via URL:

```
{FRONTEND_BASE_URL}/gallery/{external_id}
```

**Contoh:**

```
https://photobox-frontend.com/gallery/TRX-3-20251215162111-4450A9BD
```

User akan menerima link ini via email setelah upload foto selesai.

---

## 2. Backend API Endpoint

### Get Photos by Transaction ID

**Endpoint:**

```
GET /api/v1/transactions/{external_id}/photos
```

**Description:** Mengambil list semua foto yang di-upload untuk transaksi tertentu.

**Request:**

```bash
curl -X GET http://localhost:8080/api/v1/transactions/TRX-3-20251215162111-4450A9BD/photos \
  -H "Content-Type: application/json"
```

**Response (200 OK):**

```json
{
    "external_id": "TRX-3-20251215162111-4450A9BD",
    "photo_count": 3,
    "email_sent_at": "2025-12-15T16:39:00+07:00",
    "expiry_date": "2025-12-29T00:00:00+07:00",
    "photos": [
        {
            "url": "https://res.cloudinary.com/dgjxawigd/image/upload/photobox/TRX-3-20251215162111-4450A9BD/photo_1.jpg"
        },
        {
            "url": "https://res.cloudinary.com/dgjxawigd/image/upload/photobox/TRX-3-20251215162111-4450A9BD/photo_2.jpg"
        },
        {
            "url": "https://res.cloudinary.com/dgjxawigd/image/upload/photobox/TRX-3-20251215162111-4450A9BD/photo_3.jpg"
        }
    ]
}
```

**Response Fields:**

-   `external_id` (string): Transaction external ID
-   `photo_count` (integer): Jumlah foto
-   `email_sent_at` (string, ISO 8601): Timestamp kapan email dikirim
-   `expiry_date` (string, ISO 8601): Tanggal kadaluarsa (14 hari dari email_sent_at, jam 00:00 WIB)
-   `photos` (array): List foto
    -   `url` (string): URL full resolution foto

**Error Responses:**

**404 Not Found** - Transaction tidak ditemukan:

```json
{
    "error": "Transaction not found",
    "details": {
        "external_id": "TRX-INVALID-ID"
    }
}
```

**404 Not Found** - Foto belum di-upload:

```json
{
    "error": "No photos found for transaction",
    "details": {
        "external_id": "TRX-3-20251215162111-4450A9BD"
    }
}
```

---

## 3. Frontend Implementation

### 3.1 React Example

```jsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function PhotoGallery() {
    const { externalId } = useParams(); // Get external_id from URL
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPhotos = async () => {
            try {
                const response = await fetch(
                    `${process.env.REACT_APP_API_URL}/api/v1/transactions/${externalId}/photos`
                );

                if (!response.ok) {
                    throw new Error('Failed to fetch photos');
                }

                const result = await response.json();
                setData(result);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchPhotos();
    }, [externalId]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!data) return <div>No photos found</div>;

    return (
        <div className="gallery">
            <h1>📸 Photobox Gallery</h1>

            <div className="info">
                <p>Transaction ID: {data.external_id}</p>
                <p>Total Photos: {data.photo_count}</p>
                <p>
                    Expires:{' '}
                    {new Date(data.expiry_date).toLocaleDateString('id-ID')}
                </p>
            </div>

            <div className="photo-grid">
                {data.photos.map((photo, index) => (
                    <div key={index} className="photo-card">
                        <img
                            src={photo.url}
                            alt={`Photo ${index + 1}`}
                        />
                        <div className="actions">
                            <a
                                href={photo.url}
                                target="_blank"
                                rel="noopener noreferrer">
                                View Full Size
                            </a>
                            <a
                                href={photo.url}
                                download={`photo_${index + 1}.jpg`}>
                                Download
                            </a>
                        </div>
                    </div>
                ))}
            </div>

            <button onClick={() => downloadAll(data.photos)}>
                Download All (ZIP)
            </button>
        </div>
    );
}

// Helper function to download all photos
function downloadAll(photos) {
    photos.forEach((photo, index) => {
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = photo.url;
            link.download = `photo_${index + 1}.jpg`;
            link.click();
        }, index * 500); // Delay 500ms between downloads
    });
}

export default PhotoGallery;
```

### 3.2 Next.js Example (App Router)

```tsx
// app/gallery/[externalId]/page.tsx
import { notFound } from 'next/navigation';

interface Photo {
    url: string;
}

interface GalleryData {
    external_id: string;
    photo_count: number;
    email_sent_at: string;
    expiry_date: string;
    photos: Photo[];
}

async function getPhotos(externalId: string): Promise<GalleryData | null> {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/transactions/${externalId}/photos`,
        { cache: 'no-store' }
    );

    if (!res.ok) return null;
    return res.json();
}

export default async function GalleryPage({
    params,
}: {
    params: { externalId: string };
}) {
    const data = await getPhotos(params.externalId);

    if (!data) notFound();

    return (
        <div className="container mx-auto p-8">
            <h1 className="text-4xl font-bold mb-8">📸 Photobox Gallery</h1>

            <div className="bg-gray-100 p-6 rounded-lg mb-8">
                <p>Transaction ID: {data.external_id}</p>
                <p>Total Photos: {data.photo_count}</p>
                <p>
                    Expires:{' '}
                    {new Date(data.expiry_date).toLocaleDateString('id-ID')}
                </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {data.photos.map((photo, index) => (
                    <div
                        key={index}
                        className="border rounded-lg overflow-hidden">
                        <img
                            src={photo.url}
                            alt={`Photo ${index + 1}`}
                            className="w-full h-64 object-cover"
                        />
                        <div className="p-4 flex gap-2">
                            <a
                                href={photo.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-primary">
                                View
                            </a>
                            <a
                                href={photo.url}
                                download={`photo_${index + 1}.jpg`}
                                className="btn btn-secondary">
                                Download
                            </a>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
```

### 3.3 Vanilla JavaScript Example

```html
<!DOCTYPE html>
<html lang="id">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Photobox Gallery</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .photo-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .photo-card img {
                width: 100%;
                height: 300px;
                object-fit: cover;
                border-radius: 8px;
            }
            .actions {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            .actions a {
                padding: 8px 16px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>📸 Photobox Gallery</h1>
        <div id="info"></div>
        <div id="gallery" class="photo-grid"></div>

        <script>
            // Get external_id from URL
            const urlParams = new URLSearchParams(window.location.search);
            const externalId = window.location.pathname.split('/').pop();

            // Fetch photos from API
            fetch(
                `http://localhost:8080/api/v1/transactions/${externalId}/photos`
            )
                .then((response) => response.json())
                .then((data) => {
                    // Display info
                    document.getElementById('info').innerHTML = `
                    <p>Transaction ID: ${data.external_id}</p>
                    <p>Total Photos: ${data.photo_count}</p>
                    <p>Expires: ${new Date(data.expiry_date).toLocaleDateString(
                        'id-ID'
                    )}</p>
                `;

                    // Display photos
                    const gallery = document.getElementById('gallery');
                    data.photos.forEach((photo, index) => {
                        const card = document.createElement('div');
                        card.className = 'photo-card';
                        card.innerHTML = `
                        <img src="${photo.url}" alt="Photo ${
                            index + 1
                        }">
                        <div class="actions">
                            <a href="${photo.url}" target="_blank">View</a>
                            <a href="${photo.url}" download="photo_${
                            index + 1
                        }.jpg">Download</a>
                        </div>
                    `;
                        gallery.appendChild(card);
                    });
                })
                .catch((error) => {
                    document.getElementById('gallery').innerHTML = `
                    <p>Error loading photos: ${error.message}</p>
                `;
                });
        </script>
    </body>
</html>
```

---

## 4. Email Configuration

Backend akan mengirim email dengan link ke frontend gallery page.

### 4.1 Backend Configuration

Di file `.env` production, set `API_BASE_URL` ke frontend URL:

```env
# API Base URL (for generating gallery links in emails)
API_BASE_URL=https://photobox-frontend.com
```

**JANGAN** set ke backend URL!

### 4.2 Link Format

Email akan berisi link:

```
https://photobox-frontend.com/api/v1/gallery/{external_id}
```

Frontend harus setup routing untuk handle URL pattern ini.

---

## 5. Routing Setup

### React Router

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PhotoGallery from './pages/PhotoGallery';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/gallery/:externalId" element={<PhotoGallery />} />
            </Routes>
        </BrowserRouter>
    );
}
```

### Next.js (App Router)

```
app/
  gallery/
    [externalId]/
      page.tsx
```

### Next.js (Pages Router)

```
pages/
  gallery/
    [externalId].tsx
```

---

## 6. Environment Variables

Buat file `.env` di frontend project:

```env
# React
REACT_APP_API_URL=https://api.photobox.com

# Next.js
NEXT_PUBLIC_API_URL=https://api.photobox.com

# Vite
VITE_API_URL=https://api.photobox.com
```

---

## 7. Features to Implement

### Must Have

-   ✅ Display all photos in grid layout
-   ✅ Show transaction info (ID, photo count, expiry date)
-   ✅ Individual photo view (lightbox/modal)
-   ✅ Individual photo download
-   ✅ Download all photos (sequential download or ZIP)

### Nice to Have

-   Lightbox/image viewer (react-image-lightbox, photoswipe)
-   Lazy loading images
-   Download progress indicator
-   Expired state UI (when past expiry_date)
-   Social share buttons
-   Print functionality

---

## 8. Image Optimization

Cloudinary provides automatic image transformations via URL:

### Custom Sizes

You can modify the URL for different sizes if needed:

```javascript
// Generate different sizes (optional, for smaller versions)
function getImageUrl(url, width, height) {
    return url.replace('/upload/', `/upload/c_fill,h_${height},w_${width}/`);
}

// Usage
const small = getImageUrl(photo.url, 150, 150);
const medium = getImageUrl(photo.url, 600, 600);
const fullSize = photo.url; // Original
```

### Progressive Loading

```jsx
<img src={photo.url} loading="lazy" alt="Photo" />
```

---

## 9. Error Handling

Handle different error scenarios:

```javascript
async function fetchPhotos(externalId) {
    try {
        const response = await fetch(
            `${API_URL}/api/v1/transactions/${externalId}/photos`
        );

        if (response.status === 404) {
            // Transaction not found or no photos
            return {
                error: 'Photos not found. Link may be invalid or expired.',
            };
        }

        if (!response.ok) {
            return { error: 'Failed to load photos. Please try again later.' };
        }

        return await response.json();
    } catch (error) {
        return { error: 'Network error. Please check your connection.' };
    }
}
```

---

## 10. Testing

### Test URLs

Development:

```
http://localhost:3000/gallery/TRX-3-20251215162111-4450A9BD
```

Production:

```
https://photobox-frontend.com/gallery/TRX-3-20251215162111-4450A9BD
```

### Test Cases

1. **Valid transaction with photos** - Should display gallery
2. **Invalid external_id** - Should show "not found" message
3. **Transaction without photos** - Should show "no photos" message
4. **Expired transaction** - Should still work (cleanup happens server-side)
5. **Network error** - Should show error message

---

## 11. Security Considerations

-   ✅ **No authentication required** - Gallery is public via link (like Google Drive/Dropbox shared links)
-   ✅ **External ID is random** - Hard to guess (contains timestamp + random hex)
-   ✅ **Auto-cleanup** - Photos deleted after 14 days
-   ✅ **HTTPS only** in production
-   ✅ **CORS enabled** - Backend allows cross-origin requests

---

## 12. Performance Tips

1. **Create smaller image sizes** using Cloudinary transformations if needed for grid display
2. **Lazy load images** outside viewport
3. **Prefetch full-size** images on hover
4. **Cache API responses** (SWR, React Query)
5. **Use Next.js Image** component for optimization

```jsx
// Next.js Image optimization
import Image from 'next/image';

<Image
    src={photo.url}
    width={300}
    height={300}
    alt="Photo"
    loading="lazy"
/>;
```

---

## 13. Contact

Jika ada pertanyaan atau issue:

-   Backend API Documentation: `/docs` (Swagger)
-   Backend repository: [link]
-   Frontend lead: [nama]

---

**Last Updated:** 2025-12-15
