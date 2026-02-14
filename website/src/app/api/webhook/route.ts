import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import crypto from "crypto";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-01-28.clover",
});

const WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET!;
const HMAC_SECRET = process.env.MUTTR_HMAC_SECRET || "muttr-launch-2026-hmac-secret-key";

type Tier = "standard" | "unlimited" | "lifetime";

function generateLicenseKey(tier: Tier): string {
  // Monthly subscriptions get 35-day expiry for grace period
  // Lifetime gets 0 (never expires)
  const expiry =
    tier === "lifetime"
      ? "0"
      : String(Math.floor(Date.now() / 1000) + 35 * 24 * 60 * 60);

  const message = `MUTTR-${tier}-${expiry}`;
  const signature = crypto
    .createHmac("sha256", HMAC_SECRET)
    .update(message)
    .digest("hex")
    .slice(0, 16);

  return `${message}-${signature}`;
}

function tierFromPrice(priceId: string): Tier | null {
  const map: Record<string, Tier> = {
    [process.env.STRIPE_PRICE_STANDARD || ""]: "standard",
    [process.env.STRIPE_PRICE_UNLIMITED || ""]: "unlimited",
    [process.env.STRIPE_PRICE_LIFETIME || ""]: "lifetime",
  };
  return map[priceId] || null;
}

export async function POST(req: NextRequest) {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature");

  if (!sig) {
    return NextResponse.json({ error: "Missing signature" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, WEBHOOK_SECRET);
  } catch (err) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const lineItems = await stripe.checkout.sessions.listLineItems(session.id);
    const priceId = lineItems.data[0]?.price?.id;

    if (priceId) {
      const tier = tierFromPrice(priceId);
      if (tier) {
        const licenseKey = generateLicenseKey(tier);
        // In production: store in database and email to customer
        console.log(
          `License generated for ${session.customer_email}: ${licenseKey}`
        );
      }
    }
  }

  return NextResponse.json({ received: true });
}
