import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-01-28.clover",
});

export async function GET(req: NextRequest) {
  const customerId = req.nextUrl.searchParams.get("customer_id");

  if (!customerId) {
    return NextResponse.json(
      { error: "Missing customer_id" },
      { status: 400 }
    );
  }

  try {
    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: process.env.NEXT_PUBLIC_SITE_URL || "https://muttr.drewhowlett.com",
    });

    return NextResponse.redirect(session.url);
  } catch (err) {
    return NextResponse.json(
      { error: "Failed to create portal session" },
      { status: 500 }
    );
  }
}
