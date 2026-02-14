# MuttR Brand Style Guide

## 1. Brand Identity

**Brand name:** MuttR
**Tagline:** Talk, don't type.
**Brand essence:** Fast, private, effortless dictation that just works.

MuttR is for people who are tired of typing. It's not a productivity tool for power users — it's an everyday utility that makes your Mac feel more natural. You talk, it types. Simple.

---

## 2. Logo & Icon

### App Icon
- Rounded square (standard macOS squircle)
- Warm gradient background: orange (top-left) to coral-red (bottom-right)
- White speech bubble with sound wave bars emerging from it
- The speech bubble represents voice input; the wave bars represent transcription happening in real-time

### Menu Bar Icon
- Simplified version of the app icon
- Same gradient + white speech bubble at small scale
- Must be legible at 18x18pt and 36x36pt (@2x)

### Logo Usage
- The app icon IS the logo — no separate wordmark needed at this stage
- When the name "MuttR" appears alongside the icon, use the brand font (see Typography)
- Always maintain clear space around the icon equal to 25% of its width
- Never stretch, rotate, recolor, or add effects to the icon

---

## 3. Color Palette

### Primary Colors (from app icon gradient)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **MuttR Orange** | `#F2790F` | 242, 121, 15 | Gradient start (top-left), primary accent, CTAs |
| **MuttR Coral** | `#E53E2E` | 229, 62, 46 | Gradient end (bottom-right), hover states |
| **MuttR Red** | `#D42B1E` | 212, 43, 30 | Deep accent, emphasis, alerts |

### Gradient
- **Primary gradient:** 135deg from MuttR Orange to MuttR Coral
- CSS: `linear-gradient(135deg, #F2790F 0%, #E53E2E 100%)`
- Use for: hero backgrounds, buttons, accent strips, icon backgrounds

### Neutral Colors

| Name | Hex | Usage |
|------|-----|-------|
| **White** | `#FFFFFF` | Text on gradient, card backgrounds, icons |
| **Off-White** | `#FAFAFA` | Page backgrounds |
| **Light Gray** | `#F0F0F0` | Card backgrounds, dividers |
| **Medium Gray** | `#9CA3AF` | Secondary text, captions |
| **Dark Gray** | `#374151` | Body text |
| **Near Black** | `#111827` | Headlines, primary text |

### Semantic Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Success Green** | `#10B981` | Confirmation, active states, "recording" indicator |
| **Warning Amber** | `#F59E0B` | Caution states, word budget warnings |
| **Error Red** | `#EF4444` | Errors, destructive actions |

---

## 4. Typography

### Primary Font: SF Pro (System)
MuttR is a native Mac app — use the system font everywhere for a native feel.

| Style | Font | Size | Weight | Usage |
|-------|------|------|--------|-------|
| **H1** | SF Pro Display | 48px | Bold (700) | Hero headline |
| **H2** | SF Pro Display | 32px | Semibold (600) | Section titles |
| **H3** | SF Pro Display | 24px | Semibold (600) | Card titles |
| **Body** | SF Pro Text | 16px | Regular (400) | Paragraphs, descriptions |
| **Body Small** | SF Pro Text | 14px | Regular (400) | Captions, metadata |
| **Button** | SF Pro Text | 16px | Semibold (600) | CTAs, buttons |
| **Code/Tech** | SF Mono | 14px | Regular (400) | Technical details (sparingly) |

### Website Font (Fallback)
If SF Pro is unavailable (non-Apple devices visiting the website):
- Headlines: Inter (Bold/Semibold)
- Body: Inter (Regular)
- Fallback stack: `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

---

## 5. Brand Voice

### Personality
MuttR sounds like a smart friend who keeps it simple. Not corporate. Not overly casual. Just clear, confident, and a little bit fun.

### Voice Attributes

| Attribute | What it means | Example |
|-----------|---------------|---------|
| **Direct** | Say it in as few words as possible | "Talk, don't type." not "MuttR enables you to leverage voice-based input for enhanced productivity." |
| **Confident** | We know our product is good | "Your voice stays on your Mac. Period." not "We try our best to keep your data private." |
| **Warm** | Approachable, not robotic | "Hey, your words are rolling over — use them or lose them this week!" not "Alert: unused word allocation expires in 7 days." |
| **Honest** | No BS, no hype | "It's dictation. It works. It's private." not "Revolutionary AI-powered next-generation speech platform." |

### Tone by Context

| Context | Tone | Example |
|---------|------|---------|
| **Marketing / website** | Confident + warm | "Stop typing. Start talking. MuttR turns your voice into text — right on your Mac, no cloud required." |
| **In-app UI** | Clear + minimal | "Recording..." / "Hold fn to start" / "500 words left today" |
| **Error messages** | Helpful + calm | "Couldn't hear you — try speaking a bit louder" not "Error: audio level below threshold" |
| **Pricing page** | Direct + fair | "Pay for what you use. Not a penny more." |
| **Social media** | Casual + fun | "Typed this tweet with my voice in 3 seconds. Just saying." |

### Words We Use
- Talk, speak, voice, say
- Simple, fast, private, yours
- On your Mac, on-device, local

### Words We Don't Use
- Revolutionary, disruptive, game-changing, leverage
- AI-powered (unless specifically about a feature)
- Cloud-based, SaaS, platform, solution
- Synergy, optimize, streamline

---

## 6. Imagery & Visual Style

### Photography
- Not needed at launch — the product IS the visual
- If used later: real people, natural lighting, candid (not stock photo poses)
- Show people talking to their Mac in real situations: couch, coffee shop, desk

### Screenshots & Product Shots
- Clean macOS desktop with MuttR visible
- Show the overlay recording indicator
- Show the settings panel
- Dark mode AND light mode versions

### Illustrations
- Minimal, line-based if needed
- Use brand gradient for accent elements
- Keep it simple — MuttR is not a playful/whimsical brand, it's a utility

### Iconography
- SF Symbols throughout the app (already implemented)
- On the website, use simple line icons or SF Symbol equivalents
- Always white on gradient backgrounds, dark gray on light backgrounds

---

## 7. UI Components (Website)

### Buttons

**Primary CTA:**
- Background: brand gradient (orange → coral)
- Text: white, 16px semibold
- Border radius: 12px
- Padding: 14px 28px
- Hover: slightly darker gradient, subtle lift shadow
- Example: "Download Free"

**Secondary CTA:**
- Background: transparent
- Border: 1.5px Near Black
- Text: Near Black, 16px semibold
- Border radius: 12px
- Hover: light gray fill
- Example: "View Pricing"

### Cards
- Background: white
- Border radius: 16px
- Shadow: `0 1px 3px rgba(0,0,0,0.08)`
- Padding: 24px-32px
- Used for: feature highlights, pricing tiers, testimonials

### Navigation
- Clean, minimal top nav
- Logo (icon) left, links center, CTA right
- Sticky on scroll with subtle backdrop blur
- Links: Home, Features, Pricing, Download

---

## 8. Application Rules

### Do
- Use the gradient for primary actions and hero sections
- Keep text short and scannable
- Let the product speak for itself — show don't tell
- Maintain generous whitespace
- Use dark mode support everywhere

### Don't
- Use the gradient for body text backgrounds (too busy)
- Mix the brand gradient with other bright colors
- Use all caps for body text (headlines only, sparingly)
- Add decorative elements that don't serve a purpose
- Use the brand colors at low opacity for text (accessibility)

---

*MuttR — Talk, don't type.*
