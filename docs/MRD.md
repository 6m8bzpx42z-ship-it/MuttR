# MuttR — Market Requirements Document

## 1. Product Overview

**MuttR** is a macOS dictation app that lets you talk instead of type — anywhere on your Mac. Speech is transcribed on-device using Whisper, so your voice never leaves your computer. MuttR is built for general consumers who hate typing and want a fast, private, affordable alternative to existing voice-to-text tools.

**One-line positioning:** MuttR gives you flexible, private, on-device dictation with unique features at half the price of the competition.

**Competitive framework — FUPP:**
- **F**lexibility — Pay for what you use with a word-based budget, not a flat monthly fee
- **U**nique features — Murmur Mode (quiet dictation), Smart Context, Live Preview, and more
- **P**rice — Starts at $5/mo, undercutting Wispr Flow ($12-15/mo) and Superwhisper ($8.50/mo)
- **P**rivacy — 100% on-device transcription, encrypted local database, nothing leaves your Mac

---

## 2. Target User

**General consumers who hate typing.** Not developers, not meeting transcribers — everyday people who want to speak instead of type in any app: emails, messages, documents, search bars, social media, notes.

**User persona:**
- Uses a Mac daily for personal or work communication
- Types a lot and finds it slow, tedious, or physically uncomfortable
- Values privacy — uncomfortable with voice data going to the cloud
- Price-sensitive — won't pay $15/mo for basic dictation
- Non-technical — needs things to "just work" with no setup

---

## 3. Pricing Model

Word-based pricing — users pay based on how much they dictate, not a flat recurring fee.

| Tier | Price | Word Budget | Details |
|------|-------|-------------|---------|
| **Free** | $0 | 500 words/day | No credit card required. Full feature access. |
| **Standard** | $5/month | 1,000 words/day | All features included. |
| **Unlimited** | $15/month | Unlimited words/day | Power users, heavy dictation. |
| **Lifetime** | $150 one-time | Unlimited forever | One-time purchase, no recurring fees. |

**Rollover policy:** Unused daily words roll over for up to **one week** (7 days). After that, they expire. This prevents word hoarding while giving users flexibility for light and heavy days.

**Account:** One account across all future platforms. Word budget is shared across devices. Mac only at launch.

---

## 4. Competitive Landscape

| Tool | Free Tier | Paid Price | On-Device | Unique to MuttR |
|------|-----------|------------|-----------|-----------------|
| **Wispr Flow** | 2,000 words/wk | $12-15/mo | No (cloud) | MuttR is cheaper, fully private, word-based pricing |
| **Superwhisper** | Small models | ~$8.50/mo | Hybrid | MuttR is simpler, cheaper, Murmur Mode |
| **Voibe** | 300 words/day | ~$3.70/mo | Yes | MuttR has more features (Smart Context, Live Preview) |
| **Sotto** | None | $49 one-time | Yes | MuttR has a free tier and more features |
| **macOS Dictation** | Free/unlimited | $0 | Partial | MuttR has text cleanup, context awareness, customization |

**Key advantages over Wispr Flow (primary competitor):**
1. On-device processing — voice never leaves your Mac
2. Word-based pricing — pay for what you use, not a flat rate
3. Cheaper at every tier ($5 vs $12-15)
4. Murmur Mode — dictate quietly in shared spaces
5. Encrypted local storage — Wispr Flow processes in the cloud

---

## 5. Feature Set

### Core Features (Working)
These are fully implemented and functional at launch:

| Feature | Description |
|---------|-------------|
| **Hold-to-record dictation** | Hold fn key to record, release to transcribe and paste |
| **On-device Whisper** | Local transcription using faster-whisper, no cloud |
| **Text Cleanup** | Automatic filler word removal, punctuation, formatting (3 levels) |
| **Smart Context** | Uses clipboard + recent history to improve transcription accuracy |
| **Auto-Stop Recording** | Learns your speaking cadence to automatically stop recording |
| **Model Selection** | Choose between base.en (faster) or small.en (more accurate) |
| **Transcription History** | Searchable local history of all transcriptions |
| **Menu Bar App** | Lives in the menu bar, always accessible, never in the way |
| **Settings Panel** | Modern macOS System Settings-style UI with sidebar navigation |

### Features Requiring Completion Before Launch

The following features have settings UI and backend code but are **not wired into the app pipeline**. Each must be fully connected or removed before launch. No "coming soon" at launch.

| # | Feature | Current State | What Needs to Happen |
|---|---------|---------------|----------------------|
| 1 | **Murmur Mode (Quiet Voice)** | `murmur.py` has full `MurmurMode` and `MurmurProcessor` classes. Settings UI exposes Gain, Noise Gate, and Min Utterance sliders. `hotkey.py` supports triple-tap activation. | Wire triple-tap handler in `app.py` → `MurmurMode.toggle()`. Route audio through `MurmurProcessor` when active. |
| 2 | **Ghostwriter (Live Preview)** | `ghostwriter.py` has `is_enabled()`, `select_behind_cursor()`, and mode config. Settings UI exposes enabled toggle + mode selector. `hotkey.py` supports double-tap. | Wire double-tap handler in `app.py` → Ghostwriter activation. Implement the text replacement flow. |
| 3 | **Confidence Review (Highlight Uncertain Words)** | `confidence.py` extracts per-word confidence from Whisper segments. `app.py` builds `TranscriptionResult` with word data. | Build the review overlay UI that displays highlighted uncertain words. Wire it into the post-transcription flow. |
| 4 | **Cadence Coaching (Speaking Tips)** | `cadence.py` has `SpeechMetrics`, `SpeechProfile`, and `get_feedback()`. `CadenceTracker` runs during recording but results are discarded. | Call `SpeechMetrics.analyze()` after transcription, check `cadence_feedback` config, display feedback to user. |
| 5 | **Sound Feedback (Sound Effects)** | Config key `sound_feedback` saved in account.json. No sound system exists. | Implement sound playback (start/stop beeps) gated on this preference. |
| 6 | **Recording Overlay Toggle (Show Overlay)** | Config key `show_overlay` saved in account.json. `app.py` always shows overlay. | Gate `overlay.show_recording()` and `overlay.show_transcribing()` on this preference. |
| 7 | **Auto-Copy Toggle (Copy After Recording)** | Config key `auto_copy` saved in account.json. `inserter.py` always clipboard-pastes. | Gate clipboard copy behavior on this preference. |
| 8 | **Paste Delay Slider (Paste Timing)** | Config key `paste_delay_ms` saved to config.json. `inserter.py` uses hardcoded `time.sleep(0.05)`. | Read `paste_delay_ms` from config in `inserter.py` instead of hardcoded value. |

### Features Not Exposed in UI (Orphaned Config Keys)

These config keys exist in `config.py` but are never read by app logic. Clean up or implement:

| Config Key | Default | Action |
|-----------|---------|--------|
| `transcription_timeout_s` | 20 | Implement timeout or remove |
| `setup_complete` | False | Implement first-run wizard or remove |
| `confidence_threshold` | 0.7 | Wire to `confidence.py` (currently hardcoded) or remove |
| `confidence_review_timeout_s` | 3 | Wire to review overlay auto-dismiss or remove |
| `murmur_active` | False | Restore state on app restart or remove |

---

## 6. Privacy & Data

**On-device processing:** All speech transcription happens locally using Whisper. Audio is never sent to any server.

**Encrypted local database:** As part of the install process, MuttR creates a local encrypted SQLite database that stores:
- Transcription history
- User preferences and settings
- Account information
- Usage/word count data

Data is encrypted at rest and only accessible through the app. If someone accesses the raw database file, they cannot read the contents.

**Server-side (minimal):** A lightweight server is needed only for:
- Account authentication (email/password or OAuth)
- Word budget tracking and subscription management
- License validation for lifetime purchases

No audio, transcription text, or personal data is sent to the server.

**Privacy marketing copy:** "Your voice never leaves your Mac. MuttR transcribes everything on-device with military-grade encryption. We can't read your data — and we don't want to."

---

## 7. Platform Strategy

| Phase | Platform | Timeline |
|-------|----------|----------|
| **Launch** | macOS | Before end of February 2026 |
| **Phase 2** | Windows | TBD |
| **Phase 3** | iOS / iPad | TBD |

One account, one word budget, shared across all platforms when they launch.

---

## 8. Go-to-Market Strategy

### Launch Channels
1. **Product Hunt** — Launch day campaign (Tuesday-Thursday morning). Prep: 60-second demo video, 4-5 screenshots, compelling tagline. Target: top 5 of the day.
2. **Website** — SEO-optimized landing page with feature highlights, pricing, download link, and privacy messaging.
3. **Social media** — Short demo videos on Twitter/X, Reddit (r/macapps, r/productivity), and relevant communities.
4. **Content creators / influencers** — Reach out to Mac productivity YouTubers and bloggers for reviews.
5. **Word of mouth** — Free tier drives organic sharing. "I dictated this with MuttR" signature option.
6. **SEO** — Target keywords: "mac dictation app", "voice to text mac", "wispr flow alternative", "private dictation app", "on device speech to text mac"

### No paid ads at launch.

### Launch Checklist
- [ ] All 8 unwired features completed or removed
- [ ] Encrypted local database implemented
- [ ] Account system with real auth (replace placeholder)
- [ ] Word budget tracking (local + server)
- [ ] Subscription/payment integration (Stripe or similar)
- [ ] Website live with SEO
- [ ] Product Hunt listing prepared
- [ ] Demo video recorded
- [ ] App signed and notarized for distribution
- [ ] Privacy policy and terms of service

---

## 9. Success Metrics (6 Months Post-Launch)

| Metric | Target |
|--------|--------|
| Paying users on Unlimited ($15/mo) | 100+ |
| Monthly recurring revenue | $1,500+ |
| Lifetime purchases | 5 per month average |
| Lifetime revenue (monthly) | $750 |
| Total monthly revenue target | $2,250+ |
| Free tier users | Tracking for conversion funnel |
| Free → Paid conversion rate | Target 5-10% |

---

## 10. Technical Architecture Summary

| Component | Technology |
|-----------|------------|
| Transcription engine | faster-whisper (on-device) |
| Language | Python + PyObjC |
| UI framework | Native AppKit (Cocoa) |
| Data storage | Encrypted SQLite (local) |
| Menu bar | NSStatusItem + NSMenu |
| Settings | NSSplitView sidebar + content pane |
| Hotkey | CGEventTap (fn key) |
| Audio | sounddevice / pyaudio |
| Distribution | .app bundle, notarized |
| Backend (minimal) | TBD — auth, billing, license validation |

---

*Document created: February 2026*
*Product: MuttR — Talk, don't type.*
