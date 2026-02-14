import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MuttR — Talk, don't type. Private Mac dictation.",
  description:
    "MuttR turns your voice into text on your Mac. 100% on-device, encrypted, and affordable. Free to start.",
  keywords:
    "mac dictation app, voice to text mac, private dictation, wispr flow alternative, speech to text mac",
  openGraph: {
    title: "MuttR — Talk, don't type.",
    description:
      "MuttR turns your voice into text on your Mac. 100% on-device, encrypted, and affordable.",
    type: "website",
    images: ["/icon.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "MuttR — Talk, don't type.",
    description:
      "Private Mac dictation. On-device. Encrypted. Free to start.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/icon.png" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-off-white text-near-black font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
