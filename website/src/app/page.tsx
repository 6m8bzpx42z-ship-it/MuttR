"use client";

import Image from "next/image";
import { useState } from "react";

/* ------------------------------------------------------------------ */
/* Navbar                                                              */
/* ------------------------------------------------------------------ */

function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <div className="mx-4 mt-4 px-6 py-3 bg-white/80 backdrop-blur-xl border border-black/5 rounded-2xl max-w-5xl lg:mx-auto shadow-sm">
        <nav className="flex items-center justify-between">
          <a href="#" className="flex items-center gap-2.5">
            <Image src="/icon.png" alt="MuttR" width={36} height={36} className="rounded-lg" />
            <span className="font-bold text-lg text-near-black">MuttR</span>
          </a>

          <div className="hidden md:flex items-center gap-1">
            <a href="#features" className="px-4 py-2 text-dark-gray hover:text-near-black transition-colors text-sm font-medium">Features</a>
            <a href="#pricing" className="px-4 py-2 text-dark-gray hover:text-near-black transition-colors text-sm font-medium">Pricing</a>
            <a href="#privacy" className="px-4 py-2 text-dark-gray hover:text-near-black transition-colors text-sm font-medium">Privacy</a>
            <a href="#faq" className="px-4 py-2 text-dark-gray hover:text-near-black transition-colors text-sm font-medium">FAQ</a>
          </div>

          <a
            href="#download"
            className="hidden md:inline-flex px-5 py-2.5 bg-gradient-to-r from-muttr-orange to-muttr-coral text-white text-sm font-semibold rounded-xl hover:shadow-lg hover:shadow-muttr-orange/25 transition-all hover:-translate-y-0.5"
          >
            Download Free
          </a>

          <button onClick={() => setOpen(!open)} className="md:hidden w-10 h-10 flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {open ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </nav>

        {open && (
          <div className="md:hidden pt-4 pb-2 flex flex-col gap-2">
            <a href="#features" onClick={() => setOpen(false)} className="px-4 py-2 text-dark-gray hover:text-near-black text-sm font-medium">Features</a>
            <a href="#pricing" onClick={() => setOpen(false)} className="px-4 py-2 text-dark-gray hover:text-near-black text-sm font-medium">Pricing</a>
            <a href="#privacy" onClick={() => setOpen(false)} className="px-4 py-2 text-dark-gray hover:text-near-black text-sm font-medium">Privacy</a>
            <a href="#faq" onClick={() => setOpen(false)} className="px-4 py-2 text-dark-gray hover:text-near-black text-sm font-medium">FAQ</a>
            <a href="#download" onClick={() => setOpen(false)} className="mt-2 px-5 py-2.5 bg-gradient-to-r from-muttr-orange to-muttr-coral text-white text-sm font-semibold rounded-xl text-center">Download Free</a>
          </div>
        )}
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* Hero                                                                */
/* ------------------------------------------------------------------ */

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-muttr-orange via-muttr-coral to-muttr-red" />
      {/* Decorative orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-white/5 rounded-full blur-3xl animate-float" style={{ animationDelay: "3s" }} />

      <div className="relative z-10 text-center px-6 max-w-3xl">
        <div className="animate-fade-in-up">
          <Image src="/icon.png" alt="MuttR" width={80} height={80} className="mx-auto mb-8 rounded-2xl shadow-2xl" />
        </div>

        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold text-white tracking-tight animate-fade-in-up stagger-1" style={{ opacity: 0 }}>
          Talk, don&apos;t type.
        </h1>

        <p className="mt-6 text-lg sm:text-xl md:text-2xl text-white/80 max-w-xl mx-auto animate-fade-in-up stagger-2" style={{ opacity: 0 }}>
          MuttR turns your voice into text — instantly, privately, right on your Mac. No cloud. No subscription required.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up stagger-3" style={{ opacity: 0 }}>
          <a
            href="#download"
            className="px-8 py-4 bg-white text-near-black font-semibold rounded-2xl text-lg hover:shadow-xl hover:-translate-y-1 transition-all"
          >
            Download Free
          </a>
          <a
            href="#demo"
            className="px-8 py-4 border-2 border-white/40 text-white font-semibold rounded-2xl text-lg hover:bg-white/10 transition-all flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
            Watch Demo
          </a>
        </div>

        <p className="mt-8 text-sm text-white/50 animate-fade-in-up stagger-4" style={{ opacity: 0 }}>
          macOS 13+ required &nbsp;·&nbsp; 100% free to start &nbsp;·&nbsp; No account needed
        </p>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-off-white to-transparent" />
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* How It Works                                                        */
/* ------------------------------------------------------------------ */

const steps = [
  {
    num: "1",
    title: "Hold fn",
    desc: "Hold the fn key and start speaking.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="url(#grad)">
        <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#F2790F" /><stop offset="100%" stopColor="#E53E2E" /></linearGradient></defs>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 5.25a3 3 0 013 3m-3-3h-9a3 3 0 00-3 3v7.5a3 3 0 003 3h9a3 3 0 003-3V11.25M12 12.75v.008" />
      </svg>
    ),
  },
  {
    num: "2",
    title: "Speak",
    desc: "Talk naturally — MuttR listens and transcribes in real-time on your Mac.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="url(#grad2)">
        <defs><linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#F2790F" /><stop offset="100%" stopColor="#E53E2E" /></linearGradient></defs>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
      </svg>
    ),
  },
  {
    num: "3",
    title: "Done",
    desc: "Release the key and your words appear wherever you're typing. That's it.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="url(#grad3)">
        <defs><linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#F2790F" /><stop offset="100%" stopColor="#E53E2E" /></linearGradient></defs>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

function HowItWorks() {
  return (
    <section className="py-24 px-6 bg-off-white">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center text-near-black">
          How it works
        </h2>
        <p className="mt-4 text-center text-dark-gray text-lg max-w-xl mx-auto">
          Three steps. No setup. No learning curve.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s) => (
            <div
              key={s.num}
              className="relative bg-white rounded-2xl p-8 shadow-sm border border-black/5 hover:shadow-lg hover:-translate-y-1 transition-all group"
            >
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-muttr-orange/10 to-muttr-coral/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                {s.icon}
              </div>
              <div className="text-xs font-bold text-muttr-orange uppercase tracking-widest mb-2">
                Step {s.num}
              </div>
              <h3 className="text-xl font-bold text-near-black">{s.title}</h3>
              <p className="mt-2 text-dark-gray leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Features                                                            */
/* ------------------------------------------------------------------ */

const features = [
  {
    title: "On-Device Transcription",
    desc: "Your voice never leaves your Mac. MuttR uses Whisper to transcribe everything locally — no internet needed, no data sent anywhere. Ever.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25" /></svg>
    ),
  },
  {
    title: "Smart Context",
    desc: "MuttR reads the room. It uses what you recently typed and copied to get your words right the first time.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
    ),
  },
  {
    title: "Auto Cleanup",
    desc: "Filler words, false starts, and messy punctuation get cleaned up automatically. Choose how aggressive you want it — from light touch to full polish.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" /></svg>
    ),
  },
  {
    title: "Quiet Voice Mode",
    desc: "Dictate in a whisper. MuttR boosts quiet speech so you can use it in shared spaces, meetings, or late at night without waking anyone up.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" /></svg>
    ),
  },
  {
    title: "Everything Saved Locally",
    desc: "Every transcription is stored in an encrypted database on your Mac. Search your history, copy old transcriptions, or clear it all — your data, your choice.",
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
    ),
  },
];

function Features() {
  return (
    <section id="features" className="py-24 px-6 bg-white">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center text-near-black">
          Your voice, your Mac, your privacy.
        </h2>
        <p className="mt-4 text-center text-dark-gray text-lg max-w-xl mx-auto">
          Everything you need. Nothing you don&apos;t.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div
              key={i}
              className="group relative bg-off-white rounded-2xl p-8 border border-black/5 hover:shadow-xl hover:-translate-y-1 transition-all overflow-hidden"
            >
              {/* Hover gradient accent */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-muttr-orange to-muttr-coral scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />

              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-muttr-orange to-muttr-coral flex items-center justify-center text-white mb-5">
                {f.icon}
              </div>
              <h3 className="text-lg font-bold text-near-black">{f.title}</h3>
              <p className="mt-3 text-dark-gray leading-relaxed text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Pricing                                                             */
/* ------------------------------------------------------------------ */

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "",
    budget: "500 words/day",
    features: ["All features included", "Encrypted local storage", "On-device transcription", "No account needed"],
    cta: "Download Free",
    highlight: false,
  },
  {
    name: "Standard",
    price: "$5",
    period: "/mo",
    budget: "1,000 words/day",
    features: ["All features included", "Encrypted local storage", "On-device transcription", "1-week word rollover"],
    cta: "Get Standard",
    highlight: false,
  },
  {
    name: "Unlimited",
    price: "$15",
    period: "/mo",
    budget: "Unlimited words",
    features: ["All features included", "Encrypted local storage", "On-device transcription", "Priority support"],
    cta: "Get Unlimited",
    highlight: true,
  },
  {
    name: "Lifetime",
    price: "$150",
    period: " one-time",
    budget: "Unlimited forever",
    features: ["All features included", "Encrypted local storage", "On-device transcription", "Priority support", "Never pay again"],
    cta: "Buy Lifetime",
    highlight: false,
  },
];

function Pricing() {
  return (
    <section id="pricing" className="py-24 px-6 bg-off-white">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center text-near-black">
          Pay for what you use.
        </h2>
        <p className="mt-4 text-center text-dark-gray text-lg">
          Not a penny more.
        </p>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={`relative flex flex-col rounded-2xl p-8 border transition-all hover:shadow-xl hover:-translate-y-1 ${
                t.highlight
                  ? "bg-gradient-to-br from-muttr-orange to-muttr-coral text-white border-transparent shadow-lg scale-[1.02]"
                  : "bg-white border-black/5 text-near-black"
              }`}
            >
              {t.highlight && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 bg-white text-muttr-coral text-xs font-bold rounded-full shadow-md uppercase tracking-wide">
                  Most Popular
                </div>
              )}

              <div className="text-sm font-semibold uppercase tracking-wider opacity-70 mb-4">
                {t.name}
              </div>

              <div className="flex items-baseline gap-1 mb-1">
                <span className="text-4xl font-extrabold">{t.price}</span>
                <span className={`text-sm ${t.highlight ? "text-white/70" : "text-medium-gray"}`}>{t.period}</span>
              </div>

              <div className={`text-sm font-medium mb-6 ${t.highlight ? "text-white/80" : "text-muttr-orange"}`}>
                {t.budget}
              </div>

              <ul className="flex-1 space-y-3 mb-8">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <svg className={`w-4 h-4 mt-0.5 flex-shrink-0 ${t.highlight ? "text-white" : "text-success"}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                    </svg>
                    <span className={t.highlight ? "text-white/90" : ""}>{f}</span>
                  </li>
                ))}
              </ul>

              <a
                href="#download"
                className={`block text-center py-3 px-6 rounded-xl font-semibold text-sm transition-all hover:-translate-y-0.5 ${
                  t.highlight
                    ? "bg-white text-muttr-coral hover:shadow-lg"
                    : "bg-gradient-to-r from-muttr-orange to-muttr-coral text-white hover:shadow-lg hover:shadow-muttr-orange/25"
                }`}
              >
                {t.cta}
              </a>
            </div>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-medium-gray">
          Unused words roll over for up to 7 days. No contracts. Cancel anytime.
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Privacy                                                             */
/* ------------------------------------------------------------------ */

const privacyCards = [
  {
    title: "No Cloud",
    desc: "Audio is never uploaded. We literally can't hear you.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
    ),
  },
  {
    title: "Encrypted Storage",
    desc: "Your data is encrypted at rest. Only you can access it through MuttR.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
    ),
  },
  {
    title: "On-Device AI",
    desc: "Whisper runs locally. No internet needed to transcribe.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25" /></svg>
    ),
  },
];

function Privacy() {
  return (
    <section id="privacy" className="py-24 px-6 bg-near-black">
      <div className="max-w-5xl mx-auto text-center">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white">
          Private by design.
        </h2>
        <p className="mt-4 text-xl text-white/60">
          Your voice stays on your Mac. Period.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {privacyCards.map((c) => (
            <div
              key={c.title}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-colors"
            >
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-muttr-orange to-muttr-coral flex items-center justify-center text-white mx-auto mb-6">
                {c.icon}
              </div>
              <h3 className="text-lg font-bold text-white">{c.title}</h3>
              <p className="mt-3 text-white/60 leading-relaxed text-sm">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Comparison                                                          */
/* ------------------------------------------------------------------ */

const compRows = [
  { label: "Price", muttr: "$5/mo", wispr: "$12-15/mo", macos: "Free" },
  { label: "On-Device", muttr: true, wispr: false, macos: "Partial" },
  { label: "Privacy", muttr: "Encrypted", wispr: "Cloud-based", macos: "Apple servers" },
  { label: "Quiet Voice Mode", muttr: true, wispr: true, macos: false },
  { label: "Smart Context", muttr: true, wispr: true, macos: false },
  { label: "Text Cleanup", muttr: "3 levels", wispr: "AI-based", macos: "Basic" },
  { label: "Flexible Word Budget", muttr: true, wispr: false, macos: true },
  { label: "Lifetime Option", muttr: "$150", wispr: false, macos: "N/A" },
];

function Check() {
  return <svg className="w-5 h-5 text-success mx-auto" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" /></svg>;
}

function Cross() {
  return <svg className="w-5 h-5 text-red-400 mx-auto" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.28 3.22a.75.75 0 00-1.06 1.06L8.94 10l-5.72 5.72a.75.75 0 101.06 1.06L10 11.06l5.72 5.72a.75.75 0 101.06-1.06L11.06 10l5.72-5.72a.75.75 0 00-1.06-1.06L10 8.94 4.28 3.22z" clipRule="evenodd" /></svg>;
}

function CellValue({ val }: { val: string | boolean }) {
  if (val === true) return <Check />;
  if (val === false) return <Cross />;
  return <span>{val}</span>;
}

function Comparison() {
  return (
    <section className="py-24 px-6 bg-white">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center text-near-black">
          How MuttR stacks up
        </h2>

        <div className="mt-16 overflow-x-auto rounded-2xl border border-black/5 shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-black/5">
                <th className="text-left py-4 px-6 font-medium text-medium-gray w-1/4"></th>
                <th className="py-4 px-6 font-bold text-white bg-gradient-to-r from-muttr-orange to-muttr-coral rounded-tl-none w-1/4">
                  <div className="flex items-center justify-center gap-2">
                    <Image src="/icon.png" alt="" width={20} height={20} className="rounded" />
                    MuttR
                  </div>
                </th>
                <th className="py-4 px-6 font-medium text-dark-gray bg-light-gray w-1/4">Wispr Flow</th>
                <th className="py-4 px-6 font-medium text-dark-gray bg-light-gray w-1/4">macOS Dictation</th>
              </tr>
            </thead>
            <tbody>
              {compRows.map((r, i) => (
                <tr key={r.label} className={`border-b border-black/5 ${i % 2 === 0 ? "bg-off-white" : "bg-white"}`}>
                  <td className="py-4 px-6 font-medium text-near-black">{r.label}</td>
                  <td className="py-4 px-6 text-center font-semibold text-near-black"><CellValue val={r.muttr} /></td>
                  <td className="py-4 px-6 text-center text-dark-gray"><CellValue val={r.wispr} /></td>
                  <td className="py-4 px-6 text-center text-dark-gray"><CellValue val={r.macos} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Demo Video                                                          */
/* ------------------------------------------------------------------ */

function Demo() {
  return (
    <section id="demo" className="py-24 px-6 bg-gradient-to-br from-muttr-orange/5 via-muttr-coral/5 to-off-white">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-near-black">
          See MuttR in action.
        </h2>

        <div className="mt-12 rounded-2xl overflow-hidden shadow-2xl aspect-video bg-near-black flex items-center justify-center border border-black/10">
          {/* Placeholder for YouTube embed — replace src with actual video */}
          <div className="text-white/40 text-center">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
            <p className="text-sm">Demo video coming soon</p>
          </div>
        </div>

        <p className="mt-8 text-dark-gray italic text-lg">
          &ldquo;I dictated this entire page with MuttR.&rdquo;
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* FAQ                                                                 */
/* ------------------------------------------------------------------ */

const faqs = [
  { q: "Is MuttR really free?", a: "Yes. 500 words per day, every day, no credit card required. When you need more, upgrade starting at $5/mo." },
  { q: "Does my voice get sent to the cloud?", a: "Never. MuttR transcribes everything on your Mac using Whisper. Your audio stays on your device." },
  { q: "What happens to unused words?", a: "They roll over for up to 7 days. After that, they expire. This keeps things fair for everyone." },
  { q: "Can I use MuttR in any app?", a: "Yes. MuttR works anywhere you can type — emails, messages, documents, browsers, code editors, everything." },
  { q: "Is there a Windows or iPhone version?", a: "Not yet. MuttR is Mac-only for now. Other platforms are on our roadmap." },
  { q: "What's the difference between Free and Paid?", a: "Nothing except the word limit. Free users get every feature — the same engine, the same privacy, the same quality." },
  { q: "How do I cancel?", a: "Go to your account settings. Cancel anytime — no contracts, no fees, no guilt trips." },
  { q: "What is Quiet Voice Mode?", a: "It lets you dictate in a whisper. MuttR boosts your quiet voice so you can use it in libraries, shared offices, or next to a sleeping partner." },
];

function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <section id="faq" className="py-24 px-6 bg-off-white">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center text-near-black">
          Questions? We&apos;ve got answers.
        </h2>

        <div className="mt-16 space-y-3">
          {faqs.map((faq, i) => (
            <div key={i} className="bg-white rounded-2xl border border-black/5 overflow-hidden">
              <button
                onClick={() => setOpenIdx(openIdx === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-off-white transition-colors"
              >
                <span className="font-semibold text-near-black pr-4">{faq.q}</span>
                <svg
                  className={`w-5 h-5 text-medium-gray flex-shrink-0 transition-transform ${openIdx === i ? "rotate-180" : ""}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {openIdx === i && (
                <div className="px-6 pb-5 text-dark-gray leading-relaxed">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Final CTA                                                           */
/* ------------------------------------------------------------------ */

function FinalCTA() {
  return (
    <section id="download" className="relative py-24 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-muttr-orange via-muttr-coral to-muttr-red" />
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-white/10 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-2xl mx-auto text-center">
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white">
          Ready to stop typing?
        </h2>
        <p className="mt-4 text-xl text-white/80">
          Download MuttR free and start talking.
        </p>

        <a
          href="#"
          className="inline-block mt-10 px-10 py-4 bg-white text-near-black font-bold rounded-2xl text-lg hover:shadow-2xl hover:-translate-y-1 transition-all"
        >
          Download Free
        </a>

        <p className="mt-6 text-sm text-white/50">
          macOS 13+ required &nbsp;·&nbsp; No account needed &nbsp;·&nbsp; Set up in 30 seconds
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Footer                                                              */
/* ------------------------------------------------------------------ */

function Footer() {
  return (
    <footer className="py-12 px-6 bg-near-black border-t border-white/10">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2.5 mb-4">
              <Image src="/icon.png" alt="MuttR" width={32} height={32} className="rounded-lg" />
              <span className="font-bold text-white text-lg">MuttR</span>
            </div>
            <p className="text-white/40 text-sm">Talk, don&apos;t type.</p>
          </div>

          <div>
            <h4 className="font-semibold text-white text-sm mb-4">Product</h4>
            <ul className="space-y-2">
              <li><a href="#features" className="text-white/50 hover:text-white text-sm transition-colors">Features</a></li>
              <li><a href="#pricing" className="text-white/50 hover:text-white text-sm transition-colors">Pricing</a></li>
              <li><a href="#download" className="text-white/50 hover:text-white text-sm transition-colors">Download</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white text-sm mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><a href="/privacy" className="text-white/50 hover:text-white text-sm transition-colors">Privacy Policy</a></li>
              <li><a href="/terms" className="text-white/50 hover:text-white text-sm transition-colors">Terms of Service</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white text-sm mb-4">Connect</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Twitter/X</a></li>
              <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">GitHub</a></li>
              <li><a href="#" className="text-white/50 hover:text-white text-sm transition-colors">Email</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-white/30 text-sm">&copy; 2026 MuttR. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Features />
        <Pricing />
        <Privacy />
        <Comparison />
        <Demo />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
