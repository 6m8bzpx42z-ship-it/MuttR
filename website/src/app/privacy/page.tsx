import Link from "next/link";

export const metadata = {
  title: "Privacy Policy - MuttR",
  description: "MuttR Privacy Policy: on-device processing, encrypted storage, and your data rights.",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-off-white">
      <div className="max-w-3xl mx-auto px-6 py-24">
        <Link href="/" className="text-muttr-orange hover:underline text-sm font-medium">
          &larr; Back to MuttR
        </Link>

        <h1 className="mt-8 text-4xl font-bold text-near-black">Privacy Policy</h1>
        <p className="mt-2 text-medium-gray text-sm">Last updated: February 2026</p>

        <div className="mt-12 space-y-8 text-dark-gray leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Overview</h2>
            <p>
              MuttR is a macOS dictation application that processes your voice entirely on your device.
              We are committed to protecting your privacy. This policy explains what data we collect,
              how we use it, and your rights.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Audio Data</h2>
            <p>
              Your audio is <strong>never</strong> sent to any server. All speech-to-text processing
              happens locally on your Mac using the Whisper model. Audio is held in memory only
              during transcription and is immediately discarded afterward. We cannot hear you,
              and we never will.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Transcription History</h2>
            <p>
              Your transcription history is stored in an encrypted SQLite database on your Mac at
              <code className="bg-light-gray px-1.5 py-0.5 rounded text-sm mx-1">~/Library/Application Support/MuttR/</code>.
              The encryption key is stored in your macOS Keychain and is unique to your machine.
              Only the MuttR application can access your transcription data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Account &amp; Payment Data</h2>
            <p>
              If you purchase a paid plan, payment processing is handled by Stripe. We do not store
              your credit card number, billing address, or other payment details. Stripe&apos;s privacy
              policy governs how they handle your payment data. We receive only your email address
              and subscription status from Stripe.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">License Keys</h2>
            <p>
              Your license key is stored securely in your macOS Keychain. License validation
              happens locally by verifying the key&apos;s cryptographic signature. No network requests
              are made to validate your license during normal use.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Analytics &amp; Telemetry</h2>
            <p>
              MuttR does not collect analytics, telemetry, crash reports, or usage statistics.
              We have no tracking pixels, no cookies, and no third-party analytics SDKs.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Data You Can Delete</h2>
            <p>
              You can delete all your transcription history at any time from the Settings window.
              You can also delete MuttR&apos;s data directory entirely by removing
              <code className="bg-light-gray px-1.5 py-0.5 rounded text-sm mx-1">~/Library/Application Support/MuttR/</code>.
              Uninstalling MuttR removes the application but does not automatically delete your data directory.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-near-black mb-3">Contact</h2>
            <p>
              If you have questions about this privacy policy, contact us at{" "}
              <a href="mailto:privacy@drewhowlett.com" className="text-muttr-orange hover:underline">
                privacy@drewhowlett.com
              </a>.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
