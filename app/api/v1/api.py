from fastapi import APIRouter
from app.api.v1.endpoints import locations, transactions, webhooks, prices, photos, maintenance, gallery

api_router = APIRouter()

# Register routes
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(prices.router, prefix="/prices", tags=["Prices"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(photos.router, prefix="/transactions", tags=["Photos"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(gallery.router, prefix="/gallery", tags=["Gallery"])
