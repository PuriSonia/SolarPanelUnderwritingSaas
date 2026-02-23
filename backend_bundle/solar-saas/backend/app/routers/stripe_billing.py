import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Organization
from ..deps import require_role
from ..audit import log_event

router = APIRouter(prefix="/billing", tags=["Billing (Stripe)"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

@router.post("/create-checkout-session")
def create_checkout_session(db: Session = Depends(get_db), user=Depends(require_role("admin"))):
    price_id = os.getenv("STRIPE_PRICE_ID", "")
    if not stripe.api_key or not price_id:
        raise HTTPException(status_code=400, detail="Stripe not configured (set STRIPE_SECRET_KEY and STRIPE_PRICE_ID)")

    org = db.query(Organization).filter(Organization.id == user.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")

    if not org.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=org.name, metadata={"org_id": str(org.id)})
        org.stripe_customer_id = customer["id"]
        db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=org.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="http://localhost:3000/billing/success",
        cancel_url="http://localhost:3000/billing/cancel",
        metadata={"org_id": str(org.id)},
    )

    log_event(db, user=user, org_id=user.org_id, action="billing.checkout.created", entity="Organization", entity_id=str(org.id))
    return {"url": session.url}

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=400, detail="Stripe webhook not configured (STRIPE_WEBHOOK_SECRET)")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    if event["type"] in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if org:
            org.stripe_subscription_id = sub.get("id")
            org.billing_status = sub.get("status", org.billing_status)
            db.commit()

    return {"received": True}
