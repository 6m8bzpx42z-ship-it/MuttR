# MuttR Competitive Research

Research into open-source and commercial macOS dictation / speech-to-text products, focusing on push-to-talk workflows, local Whisper transcription, and desktop voice-typing UX.

---

## Comparable Products

### 1. Handy (cjpais/Handy)
- **Stars:** ~14,800 | **Language:** TypeScript/Rust (Tauri) | **Platform:** macOS, Windows, Linux
- **URL:** https://github.com/cjpais/Handy
- **Description:** Cross-platform, open-source speech-to-text app built with Tauri. Press a shortcut, speak, text appears in any field. Entirely offline and privacy-focused.
- **Key Features:**
  - Push-to-talk AND toggle modes via configurable shortcuts
  - Voice Activity Detection (Silero VAD) to filter silence before transcription
  - Multiple model backends: Whisper (Small/Medium/Turbo/Large) + Nvidia Parakeet V3
  - Parakeet V3 is CPU-only with automatic language detection
  - GPU acceleration for Whisper models
  - Globe key support on macOS (in roadmap)
  - Debug mode (Cmd+Shift+D)
  - Cross-platform text insertion with platform-specific solutions (xdotool, wtype, dotool)

### 2. VoiceInk (Beingpax/VoiceInk)
- **Stars:** ~3,700 | **Language:** Swift (native macOS) | **Platform:** macOS 14.4+
- **URL:** https://github.com/Beingpax/VoiceInk
- **Description:** Native macOS voice-to-text app. Open-sourced after 5 months of development. Freemium model (open-source + paid license for updates/support).
- **Key Features:**
  - **Power Mode:** Intelligent app detection that auto-applies pre-configured settings per app or URL
  - **Context Awareness:** AI understands screen content and adapts transcription
  - **Personal Dictionary:** Custom words, industry terms, smart text replacements
  - **Smart Modes:** Switch between AI-powered modes for different writing styles
  - **AI Assistant mode:** Built-in conversational assistant via voice
  - Global configurable keyboard shortcuts with push-to-talk
  - Uses whisper.cpp + FluidAudio (for Parakeet)
  - Homebrew installable

### 3. OpenWhispr (OpenWhispr/openwhispr)
- **Stars:** ~1,200 | **Language:** TypeScript (Electron) | **Platform:** macOS, Windows, Linux
- **URL:** https://github.com/OpenWhispr/openwhispr
- **Description:** Cross-platform dictation app with both local and cloud transcription. Full account system with free/pro tiers.
- **Key Features:**
  - **Account system:** Google OAuth, email/password sign-in, subscription management
  - **Subscription tiers:** Free (2,000 words/week), Pro (unlimited), 7-day trial
  - **Multi-provider AI processing:** OpenAI, Anthropic, Google Gemini, Groq, local models
  - **Transcription history:** SQLite-backed local storage
  - **Custom dictionary** for improved accuracy
  - **Globe key toggle** on macOS via Swift helper
  - **Compound hotkeys** (Cmd+Shift+K style)
  - **Push-to-talk** on Windows via native low-level keyboard hook
  - Nvidia Parakeet via sherpa-onnx
  - Model management UI with one-click cleanup
  - Draggable interface panel
  - Agent naming for personalized AI interactions

### 4. OpenSuperWhisper (Starmel/OpenSuperWhisper)
- **Stars:** ~620 | **Language:** Swift (native macOS) | **Platform:** macOS (Apple Silicon)
- **URL:** https://github.com/Starmel/OpenSuperWhisper
- **Description:** Free, open-source alternative to paid apps like superwhisper and MacWhisper. Real-time audio transcription with whisper.cpp.
- **Key Features:**
  - Real-time audio recording and transcription
  - Global keyboard shortcuts (Cmd+backtick default)
  - Multi-language support with auto-detection
  - Optional translation to English
  - Local storage of recordings with transcriptions
  - Asian language support with auto-correct
  - Long-press single key recording support
  - Homebrew installable
  - Background app mode (no Dock icon)

### 5. Buzz (chidiwilliams/Buzz)
- **Stars:** ~17,800 | **Language:** Python | **Platform:** macOS, Windows, Linux
- **URL:** https://github.com/chidiwilliams/buzz
- **Description:** Mature, cross-platform audio transcription and translation app. More of a file transcription tool than a dictation app, but includes live recording.
- **Key Features:**
  - Transcribe audio/video files and YouTube links
  - **Live realtime transcription** from microphone
  - **Presentation window** for live events
  - Speech separation before transcription (noisy audio)
  - Speaker identification / diarization
  - Multiple Whisper backends with CUDA, Apple Silicon, Vulkan acceleration
  - Export to TXT, SRT, VTT
  - Advanced transcript viewer with search and playback controls
  - **Watch folder** for automatic transcription of new files
  - CLI interface for scripting
  - Available via Flatpak, Snap, DMG, PyPI

### 6. foges/whisper-dictation
- **Stars:** ~210 | **Language:** Python | **Platform:** macOS, Linux, Windows
- **URL:** https://github.com/foges/whisper-dictation
- **Description:** Lightweight multilingual dictation app using OpenAI Whisper. Background process triggered by keyboard shortcut. Entirely offline.
- **Key Features:**
  - Configurable key combinations (default: cmd+option on macOS)
  - Double-tap right Command key as macOS dictation replacement
  - Model and language selection via CLI flags
  - Simple single-script architecture
  - Startup item configuration guide

### 7. ashwin-pc/whisper-dictation
- **Stars:** ~24 | **Language:** Python | **Platform:** macOS only
- **URL:** https://github.com/ashwin-pc/whisper-dictation
- **Description:** macOS dictation app using Globe/Function key -- very close to MuttR's concept. Press fn to record, press again to transcribe and paste.
- **Key Features:**
  - **Globe/Function key trigger** (exactly MuttR's approach)
  - System tray (menu bar) app running in background
  - Auto-paste at cursor position
  - **AI text enhancement:** Select text, then dictate an instruction to modify it (via AWS Bedrock/Claude)
  - Visual feedback with menu bar icon status

### 8. doctorguile/faster-whisper-dictation
- **Stars:** ~27 | **Language:** Python | **Platform:** macOS, Linux, Windows
- **URL:** https://github.com/doctorguile/faster-whisper-dictation
- **Description:** Fork/evolution of foges/whisper-dictation using faster-whisper (CTranslate2) for better performance.
- **Key Features:**
  - Uses faster-whisper (same backend as MuttR)
  - Double-tap right-cmd trigger on macOS
  - Configurable max recording time (default 30s)
  - Device and compute type selection (cpu, cuda, float16, int8)
  - Cross-platform key combo support via pynput

### 9. nerd-dictation (ideasman42/nerd-dictation)
- **Stars:** ~1,750 | **Language:** Python | **Platform:** Linux
- **URL:** https://github.com/ideasman42/nerd-dictation
- **Description:** Single-file Python script for offline speech-to-text on Linux using VOSK-API. Designed to be hackable.
- **Key Features:**
  - **User config as Python script** -- manipulate text with full Python
  - Numbers-to-digits conversion ("three million" -> "3,000,000")
  - Timeout-based auto-stop when no speech detected
  - Suspend/resume to keep model in memory
  - Zero overhead -- manual activation only, no background processes
  - Multiple input simulation backends (xdotool, ydotool, dotool, wtype)

### 10. superwhisper (Commercial)
- **URL:** https://superwhisper.com
- **Description:** Commercial macOS menu bar dictation app. The market leader for local Whisper dictation on Mac.
- **Key Features:**
  - Fully offline transcription with whisper.cpp
  - Multiple AI modes (pure transcription, formatted text, custom prompts)
  - Multilingual with on-the-fly translation
  - File transcription (audio/video to text)
  - Context awareness for smarter results
  - Custom vocabulary/dictionary
  - Pricing: free tier (15 min), then $8.49/mo or $85/yr

---

## Key Features MuttR Is Missing

Based on this research, significant features present in competitors but absent from MuttR's v1 plan:

| Feature | Found In | Priority for MuttR |
|---------|----------|-------------------|
| **Voice Activity Detection (VAD)** | Handy, WhisperMac | High -- filters silence, improves UX |
| **Transcription history** | OpenWhispr, OpenSuperWhisper, Buzz | Medium -- users want to review past dictations |
| **Personal dictionary / custom vocabulary** | VoiceInk, OpenWhispr, superwhisper | High -- critical for names, jargon |
| **Multiple transcription backends** (Parakeet, whisper.cpp) | Handy, VoiceInk, OpenWhispr, WhisperMac | Medium -- Parakeet is faster on CPU |
| **AI-powered text enhancement** | ashwin-pc, VoiceInk, OpenWhispr | Low for v1 -- but powerful differentiator |
| **App-aware / context-aware modes** | VoiceInk (Power Mode), superwhisper | Low for v1 -- but high value |
| **Multilingual support** | Most competitors | Low (v1 is English-only by design) |
| **Configurable hotkey** | Every competitor except MuttR | Medium -- fn-only is limiting |
| **Homebrew installation** | OpenSuperWhisper, VoiceInk, Handy | Medium -- expected distribution channel |

---

## UX Patterns Worth Adopting

1. **Toggle vs Hold-to-Talk choice.** Handy and OpenWhispr let users choose between push-to-talk (hold key) and toggle mode (press to start, press to stop). Some users prefer toggle for longer dictations. MuttR should consider adding toggle mode as an option.

2. **Visual recording indicator with waveform.** MuttR already plans this, but competitors like OpenSuperWhisper and VoiceInk show that a compact, non-intrusive overlay is essential. The lower-center position MuttR chose is good -- VoiceInk uses a similar approach.

3. **Immediate model download on first launch.** Handy and OpenSuperWhisper download models during first-run setup. MuttR's wizard should do the same with clear progress indication.

4. **Draggable/repositionable overlay.** OpenWhispr's draggable panel is useful for users with specific screen layouts. Worth considering post-v1.

5. **Menu bar as the primary interaction point.** All successful competitors use a menu bar icon as the hub. MuttR already plans this. VoiceInk's approach of keeping the popover minimal with a slider and quick settings is a good pattern to follow.

6. **Transcription history accessible from menu bar.** OpenWhispr and OpenSuperWhisper store recordings + transcriptions. Even a simple "last 10 transcriptions" list would be valuable for recovering dictated text that was inserted into the wrong field.

7. **Silence detection auto-stop.** nerd-dictation and Handy use silence detection to auto-end recording. This is a better UX than MuttR's hard 30s timeout alone. Combining VAD silence detection with the max timeout would feel more natural.

---

## Technical Approaches Worth Learning From

1. **Silero VAD (Handy).** Handy uses Silero Voice Activity Detection to strip silence before sending audio to Whisper. This reduces transcription time and improves accuracy by eliminating noise segments. MuttR should strongly consider integrating VAD (the silero-vad Python package or webrtcvad are lightweight options).

2. **Parakeet V3 as CPU-optimized alternative (Handy, VoiceInk, OpenWhispr).** Multiple projects now offer Nvidia's Parakeet alongside Whisper. Parakeet runs ~5x realtime on CPU with automatic language detection. For MuttR's Apple Silicon target, MLX-Whisper or Parakeet-MLX could be compelling alternatives to faster-whisper.

3. **whisper.cpp with CoreML (OpenSuperWhisper, VoiceInk).** Native Swift apps use whisper.cpp with Apple's CoreML acceleration for the fastest inference on Apple Silicon. MuttR uses Python + faster-whisper (CTranslate2), which is good but whisper.cpp + CoreML could be faster for the macOS-specific use case.

4. **Text insertion strategies.** The clipboard snapshot/restore approach MuttR plans is the standard. OpenWhispr adds a native C binary on Windows for SendInput, and Handy uses platform-specific tools. MuttR's PyObjC CGEvents approach for macOS is solid. The key insight from competitors: the paste delay matters a lot -- too short and it fails, too long and users notice. MuttR's configurable delay (60ms default, 120ms retry) is well-calibrated.

5. **User configuration as code (nerd-dictation).** nerd-dictation lets users write Python to post-process text. This is an extreme-power-user feature, but the concept of extensible cleanup rules is valuable. MuttR's slider-based profiles are good for v1, but a future plugin/script system could differentiate it.

6. **Tauri for cross-platform (Handy).** If MuttR ever considers going cross-platform, Tauri (Rust + web frontend) is the modern choice over Electron. Handy proves it works well for this use case.

7. **SQLite for transcription history (OpenWhispr).** Simple, reliable, no external dependencies. If MuttR adds history, SQLite is the right choice.

---

## Pitfalls to Avoid

1. **Electron bloat.** OpenWhispr uses Electron and ships at hundreds of MB. MuttR's Python + PyObjC approach is leaner for a macOS-only app. Stay native.

2. **Too many model choices in the UI.** Buzz offers many backends and model sizes, which overwhelms casual users. MuttR's approach of defaulting to base.en with an optional small.en is the right level of simplicity for v1.

3. **Intel compatibility rabbit hole.** OpenSuperWhisper lists Intel support as an open issue. MuttR correctly targets Apple Silicon first with Intel as best-effort. Do not sacrifice Apple Silicon performance for Intel compatibility.

4. **Unsigned app distribution friction.** Every competitor mentions the "right-click to open" dance on macOS. MuttR's first-run wizard should include clear instructions for this, with screenshots if possible.

5. **Accessibility permission UX.** Multiple projects report that users struggle with granting Accessibility permissions. MuttR's setup wizard approach is correct -- walk users through it step-by-step with deep links to System Settings.

6. **Clipboard restoration race conditions.** Several projects mention issues with clipboard restore timing. MuttR's 300ms restore window is reasonable, but should be tested across apps with varying paste responsiveness (Electron apps, VS Code, etc. can be slow).

7. **Scope creep into AI assistant territory.** VoiceInk and OpenWhispr add AI chat, multi-provider LLM integration, and agent modes. This dilutes the core dictation experience. MuttR should resist this for v1 and focus on doing dictation extremely well.

---

## Specific Recommendations for MuttR

### Must-Have for v1
1. **Add VAD-based silence detection.** Use webrtcvad or silero-vad to detect when the user stops speaking. Auto-end recording after 1.5-2s of silence (configurable). This is more natural than requiring a key release and handles the case where users forget to release fn.

2. **Add a simple transcription history.** Store the last N transcriptions (default 20) in a JSON file or SQLite DB. Show them in the menu bar popover. This is a safety net for when text gets inserted into the wrong field.

3. **Ensure the fn key detection is robust.** ashwin-pc/whisper-dictation proves the fn/Globe key approach works on macOS. Study their implementation for edge cases. Be prepared for macOS updates that change fn key behavior.

### Should-Have for v1.1
4. **Add a personal dictionary.** Let users add proper nouns, technical terms, and abbreviations that Whisper consistently gets wrong. Even a simple text file of corrections (regex or exact match) would be valuable.

5. **Add toggle mode as an alternative to hold-to-talk.** Some users (especially those with accessibility needs) find holding a key difficult. Let them press fn once to start, fn again to stop.

6. **Homebrew cask distribution.** Make MuttR installable via `brew install muttr`. This is the expected distribution channel for macOS developer tools.

### Future Differentiators
7. **Investigate Parakeet-MLX or MLX-Whisper.** Apple's MLX framework is designed for Apple Silicon ML inference. An MLX-based backend could outperform faster-whisper on M-series chips.

8. **App-context-aware cleanup profiles.** Detect the frontmost app and adjust cleanup behavior. Slack messages need different formatting than code comments or email drafts. VoiceInk's Power Mode demonstrates user demand for this.

9. **"Edit selected text" voice command.** ashwin-pc/whisper-dictation's feature of selecting text then dictating an instruction to modify it is genuinely innovative. This could be done locally with a small LLM or rule-based approach.

---

## Market Positioning

MuttR occupies a clear niche: **the simplest possible local dictation app for macOS.** The competitive landscape shows two patterns:

- **Overbuilt apps** (OpenWhispr, VoiceInk) with accounts, subscriptions, AI chat, and dozens of settings
- **Script-level tools** (foges/whisper-dictation, nerd-dictation) that require terminal comfort and manual setup

MuttR's sweet spot is between these: a polished .app bundle that does one thing well (hold fn, speak, text appears) with minimal configuration. The cleanup slider is the right amount of user control. Do not add features that compromise this simplicity.

The closest direct competitor is ashwin-pc/whisper-dictation (same fn-key concept, same Python stack) but it has only 24 stars and limited polish. MuttR has an opportunity to be the definitive fn-key dictation app for macOS.
