# MuttR Website — Content & Layout Map

## Overview
Single-page marketing site with anchor sections. Clean, fast, mobile-responsive. Built to convert visitors into downloads.

**URL:** muttr.app (or similar)
**Stack suggestion:** Static site (Next.js, Astro, or plain HTML/CSS) — no backend needed for the marketing site.

---

## Navigation Bar (Sticky)

```
[MuttR Icon]    Features    Pricing    Privacy    [Download Free ↓]
```

- Sticky top nav with backdrop blur on scroll
- Logo (app icon, small) + "MuttR" wordmark on the left
- Clean links in the center
- Primary gradient CTA button on the right: "Download Free"
- Collapses to hamburger on mobile

---

## Section 1: Hero

**Layout:** Full-width, gradient background (brand orange → coral), centered content

```
Talk, don't type.

MuttR turns your voice into text — instantly, privately,
right on your Mac. No cloud. No subscription required.

[Download Free]    [Watch Demo ▶]

macOS 13+ required  ·  100% free to start  ·  No account needed
```

**Visual:** Hero screenshot showing MuttR's recording overlay on a Mac desktop with the menu bar icon visible. Clean, real macOS screenshot — not a mockup.

**Design notes:**
- H1: "Talk, don't type." in white, 56px bold
- Subtitle: white, 20px, max-width 600px
- Two buttons side by side: "Download Free" (white bg, dark text) + "Watch Demo" (outline, white)
- Trust badges below in small white text

---

## Section 2: How It Works

**Layout:** 3-column grid on desktop, stacked on mobile

```
How it works

1. Hold fn                    2. Speak                     3. Done
[icon: keyboard]             [icon: waveform]             [icon: checkmark]
Hold the fn key and          Talk naturally — MuttR        Release the key and your
start speaking.              listens and transcribes       words appear wherever
                             in real-time on your Mac.     you're typing. That's it.
```

**Design notes:**
- Section title: H2, centered, Near Black
- Three cards with SF Symbol-style icons, step number, title, description
- White background, generous spacing
- Icons use brand gradient fill

---

## Section 3: Features

**Layout:** Alternating left-right feature blocks (image + text)

```
Your voice, your Mac, your privacy.

Feature blocks:

1. [Screenshot: settings panel]
   On-Device Transcription
   Your voice never leaves your Mac. MuttR uses Whisper
   to transcribe everything locally — no internet needed,
   no data sent anywhere. Ever.

2. [Screenshot: recording overlay]
   Smart Context
   MuttR reads the room. It uses what you recently typed
   and copied to get your words right the first time.

3. [Screenshot: cleanup settings]
   Auto Cleanup
   Filler words, false starts, and messy punctuation
   get cleaned up automatically. Choose how aggressive
   you want it — from light touch to full polish.

4. [Illustration: person whispering]
   Quiet Voice Mode
   Dictate in a whisper. MuttR boosts quiet speech
   so you can use it in shared spaces, meetings, or
   late at night without waking anyone up.

5. [Screenshot: history panel]
   Everything Saved Locally
   Every transcription is stored in an encrypted database
   on your Mac. Search your history, copy old transcriptions,
   or clear it all — your data, your choice.
```

**Design notes:**
- Alternating layout: text-left/image-right, then text-right/image-left
- Each feature block has a small gradient accent line above the title
- Images are real screenshots with subtle shadow and rounded corners
- White background with light gray cards

---

## Section 4: Pricing

**Layout:** 3 pricing cards side by side (4 on wide screens with lifetime)

```
Pay for what you use. Not a penny more.

[Free]                    [Standard]                [Unlimited]              [Lifetime]
$0                        $5/mo                     $15/mo                   $150
                                                                             one-time

500 words/day             1,000 words/day           Unlimited                Unlimited forever
All features              All features              All features             All features
Encrypted storage         Encrypted storage         Encrypted storage        Encrypted storage
                          1-week word rollover       Priority support         Priority support
                                                                             Never pay again

[Download Free]           [Get Standard]            [Get Unlimited]          [Buy Lifetime]
                                                    MOST POPULAR
```

**Design notes:**
- "Unlimited" card is highlighted (slightly larger, gradient border or gradient "MOST POPULAR" badge)
- All cards white with subtle shadow
- Prices in large bold text
- Feature list with checkmarks
- Bottom CTA button: Free = gradient, others = outline
- Below the cards: "Unused words roll over for up to 7 days. No contracts. Cancel anytime."

---

## Section 5: Privacy

**Layout:** Centered text with icon grid

```
Private by design.

Your voice stays on your Mac. Period.

[Shield icon]              [Lock icon]               [Mac icon]
No Cloud                   Encrypted Storage          On-Device AI
Audio is never uploaded.   Your data is encrypted     Whisper runs locally.
We literally can't hear    at rest. Only you can      No internet needed
you.                       access it through MuttR.   to transcribe.
```

**Design notes:**
- Dark background (Near Black) with white text — visual contrast break
- Three icon cards in a row
- Icons in brand gradient
- Short, punchy copy

---

## Section 6: Comparison

**Layout:** Simple comparison table

```
How MuttR stacks up

                    MuttR        Wispr Flow     macOS Dictation
Price               $5/mo        $12-15/mo      Free
On-Device           Yes          No (cloud)     Partial
Privacy             Encrypted    Cloud-based    Apple servers
Quiet Voice Mode    Yes          Yes            No
Smart Context       Yes          Yes            No
Text Cleanup        3 levels     AI-based       Basic
Word Budget         Flexible     Weekly reset   Unlimited
Lifetime Option     $150         None           N/A
```

**Design notes:**
- Clean table, MuttR column highlighted with gradient header
- Checkmarks and X marks where appropriate
- Keep it factual, not aggressive — confidence, not trash-talking

---

## Section 7: Demo Video

**Layout:** Centered video embed with gradient background

```
See MuttR in action.

[Embedded YouTube video — 60-90 second demo]

"I dictated this entire page with MuttR."
```

**Design notes:**
- Brand gradient background (subtle, low opacity)
- Video player centered, max-width 800px
- Custom thumbnail: Mac screen showing MuttR in action
- Quote below the video in italic

---

## Section 8: FAQ

**Layout:** Accordion-style FAQ

```
Questions? We've got answers.

Q: Is MuttR really free?
A: Yes. 500 words per day, every day, no credit card required. When you need more, upgrade starting at $5/mo.

Q: Does my voice get sent to the cloud?
A: Never. MuttR transcribes everything on your Mac using Whisper. Your audio stays on your device.

Q: What happens to unused words?
A: They roll over for up to 7 days. After that, they expire. This keeps things fair for everyone.

Q: Can I use MuttR in any app?
A: Yes. MuttR works anywhere you can type — emails, messages, documents, browsers, code editors, everything.

Q: Is there a Windows or iPhone version?
A: Not yet. MuttR is Mac-only for now. Other platforms are on our roadmap.

Q: What's the difference between Free and Paid?
A: Nothing except the word limit. Free users get every feature — the same engine, the same privacy, the same quality.

Q: How do I cancel?
A: Go to your account settings. Cancel anytime — no contracts, no fees, no guilt trips.

Q: What is Quiet Voice Mode?
A: It lets you dictate in a whisper. MuttR boosts your quiet voice so you can use it in libraries, shared offices, or next to a sleeping partner.
```

**Design notes:**
- Click to expand/collapse each question
- Clean white background
- Questions in semibold, answers in regular weight

---

## Section 9: Final CTA + Footer

**Layout:** Full-width gradient background with centered CTA

```
Ready to stop typing?

Download MuttR free and start talking.

[Download Free]

macOS 13+ required  ·  No account needed  ·  Set up in 30 seconds
```

**Footer:**
```
[MuttR Icon] MuttR

Product          Legal              Connect
Features         Privacy Policy     Twitter/X
Pricing          Terms of Service   GitHub
Download                            Email

© 2026 MuttR. All rights reserved.
Made with 🎤 in [your city].
```

---

## Technical Notes

- **Analytics:** Plausible or Fathom (privacy-respecting, no cookies)
- **Performance:** Target Lighthouse score 95+, < 2s load time
- **SEO meta tags:**
  - Title: "MuttR — Talk, don't type. Private Mac dictation."
  - Description: "MuttR turns your voice into text on your Mac. 100% on-device, encrypted, and affordable. Free to start."
  - Keywords: mac dictation app, voice to text mac, private dictation, wispr flow alternative, speech to text mac
- **Open Graph:** App icon + "Talk, don't type." for social sharing
- **Favicon:** App icon scaled down

---

*MuttR — Talk, don't type.*
