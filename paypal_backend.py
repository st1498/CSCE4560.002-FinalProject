import os
import base64
from typing import Optional

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# =========================
# CONFIG
# =========================

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "fake1")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "fake2")
PAYPAL_BASE = "https://api-m.sandbox.paypal.com"  # sandbox base URL

#testing to see if the variables exist
if PAYPAL_CLIENT_ID == "YOUR_SANDBOX_CLIENT_ID" or PAYPAL_SECRET == "YOUR_SANDBOX_SECRET":
    print("[WARN] Set PAYPAL_CLIENT_ID and PAYPAL_SECRET as environment variables for real use.")

# =========================
# APP SETUP
# =========================

app = FastAPI(title="PayPal Checkout Backend (Python)")

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PAYPAL HELPERS
# =========================

async def get_access_token() -> str:
    """
    Get OAuth2 access token from PayPal.
    """
    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )

    if resp.status_code != 200:
        print("[ERROR] Failed to get access token:", resp.text)
        raise HTTPException(status_code=500, detail="Failed to get PayPal access token")

    return resp.json()["access_token"]


# =========================
# ROUTES
# =========================

@app.get("/")
async def root():
    return {"status": "ok", "message": "PayPal backend running"}


@app.post("/api/paypal/create-order")
async def create_order(
    amount: str = "10.00",
    currency: str = "USD",
    description: Optional[str] = "Test payment",
):
    """
    Create a PayPal order.
    Frontend calls this first, gets back an order ID.
    """
    token = await get_access_token()

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                },
                "description": description,
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=body,
        )

    if resp.status_code not in (201, 200):
        print("[ERROR] Failed to create order:", resp.text)
        raise HTTPException(status_code=500, detail="Failed to create PayPal order")

    data = resp.json()
    # You could store data["id"] and other info in your DB here
    return data


@app.post("/api/paypal/capture-order")
async def capture_order(orderID: str = Query(..., alias="orderID")):
    """
    Capture a PayPal order after the user approves it.
    Frontend calls this with ?orderID=... from onApprove.
    """
    token = await get_access_token()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{orderID}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    if resp.status_code not in (201, 200):
        print("[ERROR] Failed to capture order:", resp.text)
        raise HTTPException(status_code=500, detail="Failed to capture PayPal order")

    data = resp.json()

    # TODO: persist transaction in your DB
    # e.g. status = data["status"], capture_id = data["purchase_units"][0]["payments"]["captures"][0]["id"]

    return data


# =========================
# OPTIONAL: WEBHOOK ENDPOINT
# =========================

@app.post("/api/paypal/webhook")
async def paypal_webhook(payload: dict):
    """
    Basic webhook receiver (no signature verification here).
    Configure this URL in your PayPal app's webhook settings.
    """
    event_type = payload.get("event_type")
    resource = payload.get("resource", {})

    print(f"[WEBHOOK] Event: {event_type}")
    print("[WEBHOOK] Resource ID:", resource.get("id"))

    # TODO: verify webhook signature (recommended for real use)
    # TODO: handle events like PAYMENT.CAPTURE.COMPLETED, etc.

    return {"status": "received"}


# =========================
# DEV ENTRYPOINT
# =========================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("paypal_backend:app", host="0.0.0.0", port=8000, reload=True)
