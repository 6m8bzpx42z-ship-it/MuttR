import Link from "next/link";

export const metadata = {
  title: "Terms of Service - MuttR",
  description: "MuttR Terms of Service: usage terms, licensing, and liability.",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-off-white">
      <div className="max-w-3xl mx-auto px-6 py-24">
        <Link href="/" className="text-muttr-orange hover:underline text-sm font-medium">
          &larr; Back to MuttR
        </Link>

        <h1 className="mt-8 text-4xl font-bold text-near-black">Terms of Service</h1>
        <p className="mt-2 text-medium-gray text-sm">Last updated: February 2026</p>

        <div className="mt-12 space-y-8 text-dark-gray leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Acceptance of Terms</h2>
            <p>
              By downloading, installing, or using MuttR, you agree to these Terms of Service.
              If you do not agree, do not use the software.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">License Grant</h2>
            <p>
              MuttR grants you a non-exclusive, non-transferable license to use the software
              on your personal Mac computer. The free tier includes 500 words per day. Paid tiers
              provide additional word limits as described on the pricing page.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Subscriptions &amp; Payments</h2>
            <p>
              Paid plans are billed through Stripe. Monthly subscriptions renew automatically
              until cancelled. You may cancel at any time through your account settings or
              the Stripe customer portal. Refunds are handled on a case-by-case basis.
            </p>
            <p className="mt-2">
              Lifetime licenses are a one-time purchase granting unlimited usage indefinitely.
              Lifetime licenses are non-refundable after 30 days.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Word Budget</h2>
            <p>
              Free and Standard tiers include a daily word limit. Unused words roll over for up
              to 7 days. Word counts are tracked locally on your device. We do not monitor your
              usage remotely.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Acceptable Use</h2>
            <p>
              You may not reverse-engineer, decompile, or modify the software. You may not
              share, redistribute, or resell license keys. You may not use MuttR to process
              content that violates applicable laws.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Disclaimer of Warranties</h2>
            <p>
              MuttR is provided &ldquo;as is&rdquo; without warranty of any kind. Transcription
              accuracy depends on audio quality, accent, and other factors. We do not guarantee
              perfect transcription results.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, MuttR and its creators shall not be liable
              for any indirect, incidental, or consequential damages arising from your use of the
              software.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Changes to Terms</h2>
            <p>
              We may update these terms from time to time. Continued use of MuttR after changes
              constitutes acceptance of the new terms. Material changes will be communicated
              through the application or website.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Contact</h2>
            <p>
              For questions about these terms, contact us at{" "}
              <a href="mailto:legal@drewhowlett.com" className="text-muttr-orange hover:underline">
                legal@drewhowlett.com
              </a>.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
