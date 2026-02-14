"""Menu bar status item + settings window with history and account panels."""

import Cocoa
import objc

from muttr import config, history, account


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(text, font_size=13, bold=False, color=None, weight=None):
    """Create an NSTextField used as a static label."""
    tf = Cocoa.NSTextField.alloc().initWithFrame_(Cocoa.NSZeroRect)
    tf.setStringValue_(text)
    tf.setBezeled_(False)
    tf.setDrawsBackground_(False)
    tf.setEditable_(False)
    tf.setSelectable_(False)
    if weight is not None:
        tf.setFont_(Cocoa.NSFont.systemFontOfSize_weight_(font_size, weight))
    elif bold:
        tf.setFont_(Cocoa.NSFont.boldSystemFontOfSize_(font_size))
    else:
        tf.setFont_(Cocoa.NSFont.systemFontOfSize_(font_size))
    if color:
        tf.setTextColor_(color)
    tf.sizeToFit()
    return tf


def _section_label(text):
    """Small uppercase section header above a card."""
    lbl = _label(text.upper(), font_size=11, color=Cocoa.NSColor.secondaryLabelColor())
    lbl.setFont_(Cocoa.NSFont.systemFontOfSize_weight_(11, Cocoa.NSFontWeightSemibold))
    lbl.sizeToFit()
    return lbl


def _ts_to_str(ts):
    """Format a unix timestamp as a readable string."""
    import datetime
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%b %d, %Y  %I:%M %p")


def _ts_relative(ts):
    """Format a unix timestamp as a relative time string."""
    import time, datetime
    now = time.time()
    delta = now - ts
    if delta < 60:
        return "Just now"
    elif delta < 3600:
        m = int(delta / 60)
        return f"{m}m ago"
    elif delta < 86400:
        h = int(delta / 3600)
        return f"{h}h ago"
    else:
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%b %d, %I:%M %p")


def _sf_symbol(name, size=16):
    """Load an SF Symbol image by name."""
    img = Cocoa.NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
    if img is None:
        return None
    cfg = Cocoa.NSImageSymbolConfiguration.configurationWithPointSize_weight_(
        size, Cocoa.NSFontWeightRegular
    )
    return img.imageWithSymbolConfiguration_(cfg)


# ---------------------------------------------------------------------------
# iOS-style toggle switch (custom NSButton subclass drawing a pill shape)
# ---------------------------------------------------------------------------

_SWITCH_W = 42
_SWITCH_H = 24
_SWITCH_KNOB = 20
_SWITCH_PAD = 2


class _ToggleSwitch(Cocoa.NSButton):
    """A pill-shaped on/off switch matching iOS style."""

    def initWithFrame_(self, frame):
        self = objc.super(_ToggleSwitch, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setButtonType_(Cocoa.NSButtonTypeToggle)
        self.setBordered_(False)
        self.setTitle_("")
        self.setAlternateTitle_("")
        return self

    def drawRect_(self, rect):
        on = self.state() == Cocoa.NSControlStateValueOn
        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height
        radius = h / 2

        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, radius, radius
        )
        if on:
            Cocoa.NSColor.controlAccentColor().setFill()
        else:
            Cocoa.NSColor.separatorColor().setFill()
        path.fill()

        knob_size = h - _SWITCH_PAD * 2
        knob_x = (w - knob_size - _SWITCH_PAD) if on else _SWITCH_PAD
        knob_rect = Cocoa.NSMakeRect(knob_x, _SWITCH_PAD, knob_size, knob_size)
        knob = Cocoa.NSBezierPath.bezierPathWithOvalInRect_(knob_rect)
        Cocoa.NSColor.whiteColor().setFill()
        knob.fill()

    def intrinsicContentSize(self):
        return Cocoa.NSMakeSize(_SWITCH_W, _SWITCH_H)


def _make_switch(state, target, action):
    """Create an iOS-style toggle switch."""
    sw = _ToggleSwitch.alloc().initWithFrame_(
        Cocoa.NSMakeRect(0, 0, _SWITCH_W, _SWITCH_H)
    )
    sw.setState_(Cocoa.NSControlStateValueOn if state else Cocoa.NSControlStateValueOff)
    sw.setTarget_(target)
    sw.setAction_(action)
    return sw


# ---------------------------------------------------------------------------
# VStack layout helper
# ---------------------------------------------------------------------------

class _VStack:
    """Tracks a vertical cursor to lay out subviews top-to-bottom."""

    def __init__(self, container, top, left=0, width=None):
        self.container = container
        self.y = top
        self.left = left
        self.width = width or (container.frame().size.width - left * 2)

    def add(self, view, height=None, x_offset=0):
        if height is None:
            height = view.frame().size.height
        view.setFrameOrigin_(Cocoa.NSMakePoint(self.left + x_offset, self.y - height))
        self.container.addSubview_(view)
        self.y -= height
        return view

    def space(self, pts):
        self.y -= pts

    @property
    def cursor(self):
        return self.y


# ---------------------------------------------------------------------------
# Card builder
# ---------------------------------------------------------------------------

def _card(width, content_builder, fill_color=None):
    """Rounded-rect card using NSBox."""
    CARD_PAD_H = 20
    CARD_PAD_V = 14

    card = Cocoa.NSBox.alloc().initWithFrame_(
        Cocoa.NSMakeRect(0, 0, width, 2000)
    )
    card.setBoxType_(Cocoa.NSBoxCustom)
    card.setCornerRadius_(10)
    card.setFillColor_(fill_color or Cocoa.NSColor.controlBackgroundColor())
    card.setBorderWidth_(0)
    card.setContentViewMargins_(Cocoa.NSMakeSize(0, 0))

    content = card.contentView()
    content.setFrame_(Cocoa.NSMakeRect(0, 0, width, 2000))

    inner_width = width - CARD_PAD_H * 2
    vs = _VStack(content, 2000 - CARD_PAD_V, left=CARD_PAD_H, width=inner_width)
    content_builder(vs, inner_width)
    used = 2000 - vs.cursor + CARD_PAD_V
    card.setFrameSize_(Cocoa.NSMakeSize(width, used))
    content.setFrameSize_(Cocoa.NSMakeSize(width, used))

    shift = used - 2000
    for sub in content.subviews():
        origin = sub.frame().origin
        sub.setFrameOrigin_(Cocoa.NSMakePoint(origin.x, origin.y + shift))

    return card


def _scrollable_section(container, vs, initial_height, margin_top=20):
    """Finalize a section container into a scroll view."""
    content_w = container.frame().size.width
    total_h = initial_height - vs.cursor + margin_top
    final_h = max(total_h, WINDOW_HEIGHT)
    container.setFrameSize_(Cocoa.NSMakeSize(content_w, final_h))

    shift = final_h - initial_height
    for sub in container.subviews():
        origin = sub.frame().origin
        sub.setFrameOrigin_(Cocoa.NSMakePoint(origin.x, origin.y + shift))

    scroll = Cocoa.NSScrollView.alloc().initWithFrame_(
        Cocoa.NSMakeRect(0, 0, content_w, WINDOW_HEIGHT)
    )
    scroll.setHasVerticalScroller_(True)
    scroll.setDrawsBackground_(False)
    scroll.setDocumentView_(container)
    scroll.setAutoresizingMask_(
        Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
    )
    container.scrollPoint_(Cocoa.NSMakePoint(0, container.frame().size.height))
    return scroll


# ---------------------------------------------------------------------------
# Toggle row builder (iOS-style)
# ---------------------------------------------------------------------------

def _toggle_row(label_text, state, target, action, width, description=None):
    """Row with label on left, iOS toggle on right, optional description below."""
    ROW_H = 44 if description else 40
    row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, width, ROW_H))

    label_y = (ROW_H / 2) + 2 if description else (ROW_H - 18) / 2
    lbl = _label(label_text, font_size=13)
    lbl.setFrameOrigin_(Cocoa.NSMakePoint(0, label_y))
    row.addSubview_(lbl)

    switch = _make_switch(state, target, action)
    switch.setFrameOrigin_(Cocoa.NSMakePoint(width - _SWITCH_W, (ROW_H - _SWITCH_H) / 2))
    row.addSubview_(switch)

    if description:
        desc = _label(description, font_size=11, color=Cocoa.NSColor.secondaryLabelColor())
        desc.setFrameOrigin_(Cocoa.NSMakePoint(0, label_y - 16))
        row.addSubview_(desc)

    return row, switch


# Thin separator line inside cards
def _card_separator(width):
    sep = Cocoa.NSBox.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, width, 1))
    sep.setBoxType_(Cocoa.NSBoxSeparator)
    return sep


# ---------------------------------------------------------------------------
# Sidebar data
# ---------------------------------------------------------------------------

SIDEBAR_ITEMS = [
    ("gearshape", "General", "general"),
    ("waveform", "Transcription", "transcription"),
    ("clock", "History", "history"),
    ("person.crop.circle", "Account", "account"),
]

# ---------------------------------------------------------------------------
# Window dimensions
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 780
WINDOW_HEIGHT = 560
SIDEBAR_WIDTH = 220
CONTENT_PAD = 24


# ---------------------------------------------------------------------------
# Settings Window Controller
# ---------------------------------------------------------------------------

class SettingsWindowController(Cocoa.NSObject):
    """Manages a native NSWindow with sidebar-driven settings panels."""

    def init(self):
        self = objc.super(SettingsWindowController, self).init()
        if self is None:
            return None
        self._window = None
        self._split_view = None
        self._sidebar_table = None
        self._content_host = None
        self._section_cache = {}

        # History
        self._history_table = None
        self._history_data = []
        self._search_field = None
        self._history_count_label = None
        self._history_scroll = None
        self._history_container = None

        # General controls
        self._auto_copy_switch = None
        self._sound_switch = None
        self._overlay_switch = None
        self._delay_slider = None
        self._delay_label = None

        # Transcription controls
        self._model_popup = None
        self._model_desc_label = None
        self._cleanup_slider = None
        self._cleanup_label = None
        self._context_stitch_switch = None
        self._adaptive_silence_switch = None
        self._confidence_review_switch = None
        self._cadence_feedback_switch = None
        self._ghostwriter_switch = None
        self._ghostwriter_seg = None
        self._murmur_gain_slider = None
        self._murmur_gain_label = None
        self._murmur_gate_slider = None
        self._murmur_gate_label = None
        self._murmur_utterance_slider = None
        self._murmur_utterance_label = None

        # Account
        self._email_field = None
        self._name_field = None
        self._sign_in_button = None
        self._avatar_label = None
        self._profile_name_label = None
        self._profile_email_label = None
        self._credentials_card = None

        return self

    @objc.python_method
    def show(self):
        if self._window is None:
            self._build_window()
        self._refresh_history()
        self._refresh_account_ui()
        self._window.makeKeyAndOrderFront_(None)
        Cocoa.NSApp.activateIgnoringOtherApps_(True)

    # ------------------------------------------------------------------
    # Window + split view
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_window(self):
        style = (
            Cocoa.NSWindowStyleMaskTitled
            | Cocoa.NSWindowStyleMaskClosable
            | Cocoa.NSWindowStyleMaskMiniaturizable
            | Cocoa.NSWindowStyleMaskResizable
            | Cocoa.NSWindowStyleMaskFullSizeContentView
        )
        rect = Cocoa.NSMakeRect(200, 200, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, Cocoa.NSBackingStoreBuffered, False
        )
        self._window.setTitle_("MuttR Settings")
        self._window.setTitlebarAppearsTransparent_(True)
        self._window.setMinSize_(Cocoa.NSMakeSize(640, 420))
        self._window.center()
        self._window.setReleasedWhenClosed_(False)

        self._split_view = Cocoa.NSSplitView.alloc().initWithFrame_(
            self._window.contentView().bounds()
        )
        self._split_view.setVertical_(True)
        self._split_view.setDividerStyle_(Cocoa.NSSplitViewDividerStyleThin)
        self._split_view.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )
        self._split_view.setDelegate_(self)

        sidebar = self._build_sidebar()
        self._split_view.addSubview_(sidebar)

        self._content_host = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WINDOW_WIDTH - SIDEBAR_WIDTH, WINDOW_HEIGHT)
        )
        self._content_host.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )
        self._split_view.addSubview_(self._content_host)
        self._window.contentView().addSubview_(self._split_view)

        self._sidebar_table.selectRowIndexes_byExtendingSelection_(
            Cocoa.NSIndexSet.indexSetWithIndex_(0), False
        )
        self._switch_to_section("general")

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_sidebar(self):
        frame = Cocoa.NSMakeRect(0, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)

        effect = Cocoa.NSVisualEffectView.alloc().initWithFrame_(frame)
        effect.setMaterial_(Cocoa.NSVisualEffectMaterialSidebar)
        effect.setBlendingMode_(Cocoa.NSVisualEffectBlendingModeBehindWindow)
        effect.setAutoresizingMask_(Cocoa.NSViewHeightSizable)

        scroll = Cocoa.NSScrollView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        )
        scroll.setHasVerticalScroller_(True)
        scroll.setDrawsBackground_(False)
        scroll.setAutoresizingMask_(
            Cocoa.NSViewHeightSizable | Cocoa.NSViewWidthSizable
        )

        self._sidebar_table = Cocoa.NSTableView.alloc().initWithFrame_(Cocoa.NSZeroRect)
        self._sidebar_table.setStyle_(Cocoa.NSTableViewStyleSourceList)
        self._sidebar_table.setHeaderView_(None)
        self._sidebar_table.setBackgroundColor_(Cocoa.NSColor.clearColor())
        self._sidebar_table.setRowHeight_(34)
        self._sidebar_table.setSelectionHighlightStyle_(
            Cocoa.NSTableViewSelectionHighlightStyleSourceList
        )
        self._sidebar_table.setIntercellSpacing_(Cocoa.NSMakeSize(0, 2))

        col = Cocoa.NSTableColumn.alloc().initWithIdentifier_("sidebar")
        col.setWidth_(SIDEBAR_WIDTH - 20)
        self._sidebar_table.addTableColumn_(col)
        self._sidebar_table.setDataSource_(self)
        self._sidebar_table.setDelegate_(self)

        scroll.setDocumentView_(self._sidebar_table)
        effect.addSubview_(scroll)
        return effect

    # ------------------------------------------------------------------
    # Section switching
    # ------------------------------------------------------------------

    @objc.python_method
    def _switch_to_section(self, section_id):
        for sub in list(self._content_host.subviews()):
            sub.removeFromSuperview()

        if section_id not in self._section_cache:
            builders = {
                "general": self._build_general_section,
                "transcription": self._build_transcription_section,
                "history": self._build_history_section,
                "account": self._build_account_section,
            }
            builder = builders.get(section_id)
            if builder:
                self._section_cache[section_id] = builder()

        view = self._section_cache.get(section_id)
        if view:
            view.setFrame_(self._content_host.bounds())
            view.setAutoresizingMask_(
                Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
            )
            self._content_host.addSubview_(view)

        if section_id == "history":
            self._refresh_history()
        elif section_id == "account":
            self._refresh_account_ui()

    # ------------------------------------------------------------------
    # Section: General
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_general_section(self):
        cfg = config.load()
        prefs = account.load_account()["preferences"]
        content_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        card_w = content_w - CONTENT_PAD * 2

        container = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, content_w, 1200)
        )
        vs = _VStack(container, 1200 - 20, left=CONTENT_PAD, width=card_w)

        # Card 1 — Preferences
        lbl = _section_label("Preferences")
        vs.add(lbl, height=16)
        vs.space(6)

        def prefs_builder(cvs, w):
            row1, self._auto_copy_switch = _toggle_row(
                "Auto-copy to clipboard",
                prefs.get("auto_copy", True), self, "prefChanged:", w)
            cvs.add(row1, height=40)
            cvs.add(_card_separator(w), height=1)

            row2, self._sound_switch = _toggle_row(
                "Sound feedback",
                prefs.get("sound_feedback", False), self, "prefChanged:", w)
            cvs.add(row2, height=40)
            cvs.add(_card_separator(w), height=1)

            row3, self._overlay_switch = _toggle_row(
                "Recording overlay",
                prefs.get("show_overlay", True), self, "prefChanged:", w)
            cvs.add(row3, height=40)

        card1 = _card(card_w, prefs_builder)
        vs.add(card1, height=card1.frame().size.height)
        vs.space(20)

        # Card 2 — Paste Delay
        lbl2 = _section_label("Paste Delay")
        vs.add(lbl2, height=16)
        vs.space(6)

        def delay_builder(cvs, w):
            self._delay_label = _label(f"{cfg['paste_delay_ms']} ms", font_size=13,
                                       color=Cocoa.NSColor.labelColor(),
                                       weight=Cocoa.NSFontWeightMedium)
            self._delay_label.setAlignment_(Cocoa.NSTextAlignmentRight)
            self._delay_label.setFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            cvs.add(self._delay_label, height=20)
            cvs.space(6)

            self._delay_slider = Cocoa.NSSlider.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 22)
            )
            self._delay_slider.setMinValue_(10)
            self._delay_slider.setMaxValue_(500)
            self._delay_slider.setIntValue_(cfg["paste_delay_ms"])
            self._delay_slider.setTarget_(self)
            self._delay_slider.setAction_("delaySliderChanged:")
            cvs.add(self._delay_slider, height=22)
            cvs.space(4)

            desc = _label("Delay before pasting transcribed text (10\u2013500 ms)",
                          font_size=11, color=Cocoa.NSColor.tertiaryLabelColor())
            cvs.add(desc, height=14)

        card2 = _card(card_w, delay_builder)
        vs.add(card2, height=card2.frame().size.height)

        return _scrollable_section(container, vs, 1200)

    # ------------------------------------------------------------------
    # Section: Transcription
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_transcription_section(self):
        cfg = config.load()
        content_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        card_w = content_w - CONTENT_PAD * 2

        container = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, content_w, 2000)
        )
        vs = _VStack(container, 2000 - 20, left=CONTENT_PAD, width=card_w)

        # Card 1 — Model
        lbl1 = _section_label("Whisper Model")
        vs.add(lbl1, height=16)
        vs.space(6)

        def model_builder(cvs, w):
            row_h = 36
            row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, row_h))
            lbl = _label("Model Size", font_size=13)
            lbl.setFrameOrigin_(Cocoa.NSMakePoint(0, (row_h - lbl.frame().size.height) / 2))
            row.addSubview_(lbl)

            self._model_popup = Cocoa.NSPopUpButton.alloc().initWithFrame_pullsDown_(
                Cocoa.NSMakeRect(w - 180, (row_h - 25) / 2, 180, 25), False
            )
            self._model_popup.addItemsWithTitles_(["base.en", "small.en"])
            model_idx = 0 if cfg["model"] == "base.en" else 1
            self._model_popup.selectItemAtIndex_(model_idx)
            self._model_popup.setTarget_(self)
            self._model_popup.setAction_("modelChanged:")
            row.addSubview_(self._model_popup)
            cvs.add(row, height=row_h)
            cvs.space(4)

            desc = _label("base.en is faster; small.en is more accurate but uses more memory.",
                          font_size=11, color=Cocoa.NSColor.tertiaryLabelColor())
            cvs.add(desc, height=14)

        card1 = _card(card_w, model_builder)
        vs.add(card1, height=card1.frame().size.height)
        vs.space(20)

        # Card 2 — Cleanup
        lbl2 = _section_label("Cleanup")
        vs.add(lbl2, height=16)
        vs.space(6)

        def cleanup_builder(cvs, w):
            level_names = ["Light", "Moderate", "Aggressive"]

            self._cleanup_label = _label(
                level_names[cfg["cleanup_level"]], font_size=13,
                color=Cocoa.NSColor.labelColor(), weight=Cocoa.NSFontWeightMedium
            )
            self._cleanup_label.setAlignment_(Cocoa.NSTextAlignmentRight)
            self._cleanup_label.setFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            cvs.add(self._cleanup_label, height=20)
            cvs.space(4)

            self._cleanup_slider = Cocoa.NSSlider.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 22)
            )
            self._cleanup_slider.setMinValue_(0)
            self._cleanup_slider.setMaxValue_(2)
            self._cleanup_slider.setNumberOfTickMarks_(3)
            self._cleanup_slider.setAllowsTickMarkValuesOnly_(True)
            self._cleanup_slider.setIntValue_(cfg["cleanup_level"])
            self._cleanup_slider.setTarget_(self)
            self._cleanup_slider.setAction_("cleanupSliderChanged:")
            cvs.add(self._cleanup_slider, height=22)
            cvs.space(6)

            tick_row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 14))
            for i, name in enumerate(level_names):
                t = _label(name, font_size=10, color=Cocoa.NSColor.tertiaryLabelColor())
                if i == 0:
                    x = 0
                elif i == 1:
                    x = (w - t.frame().size.width) / 2
                else:
                    x = w - t.frame().size.width
                t.setFrameOrigin_(Cocoa.NSMakePoint(x, 0))
                tick_row.addSubview_(t)
            cvs.add(tick_row, height=14)

        card2 = _card(card_w, cleanup_builder)
        vs.add(card2, height=card2.frame().size.height)
        vs.space(20)

        # Card 3 — Intelligence
        lbl3 = _section_label("Intelligence")
        vs.add(lbl3, height=16)
        vs.space(6)

        def intel_builder(cvs, w):
            r1, self._context_stitch_switch = _toggle_row(
                "Context Stitching", cfg.get("context_stitching", True),
                self, "contextStitchChanged:", w,
                description="Use clipboard + history to improve accuracy")
            cvs.add(r1, height=44)
            cvs.add(_card_separator(w), height=1)

            r2, self._adaptive_silence_switch = _toggle_row(
                "Adaptive Silence", cfg.get("adaptive_silence", True),
                self, "adaptiveSilenceChanged:", w,
                description="Learn your speaking cadence for auto-stop")
            cvs.add(r2, height=44)
            cvs.add(_card_separator(w), height=1)

            r3, self._confidence_review_switch = _toggle_row(
                "Confidence Review", cfg.get("confidence_review", False),
                self, "confidenceReviewChanged:", w,
                description="Show heatmap for low-confidence words")
            cvs.add(r3, height=44)
            cvs.add(_card_separator(w), height=1)

            r4, self._cadence_feedback_switch = _toggle_row(
                "Cadence Coaching", cfg.get("cadence_feedback", True),
                self, "cadenceFeedbackChanged:", w,
                description="Speech quality feedback after transcription")
            cvs.add(r4, height=44)

        card3 = _card(card_w, intel_builder)
        vs.add(card3, height=card3.frame().size.height)
        vs.space(20)

        # Card 4 — Ghostwriter
        lbl4 = _section_label("Ghostwriter")
        vs.add(lbl4, height=16)
        vs.space(6)

        def ghost_builder(cvs, w):
            r1, self._ghostwriter_switch = _toggle_row(
                "Enabled", cfg.get("ghostwriter_enabled", True),
                self, "ghostwriterEnabledChanged:", w)
            cvs.add(r1, height=40)
            cvs.add(_card_separator(w), height=1)
            cvs.space(8)

            lbl = _label("Selection Mode", font_size=12,
                         color=Cocoa.NSColor.secondaryLabelColor())
            cvs.add(lbl, height=16)
            cvs.space(8)

            self._ghostwriter_seg = Cocoa.NSSegmentedControl.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 28)
            )
            self._ghostwriter_seg.setSegmentCount_(3)
            self._ghostwriter_seg.setLabel_forSegment_("Sentence", 0)
            self._ghostwriter_seg.setLabel_forSegment_("Line", 1)
            self._ghostwriter_seg.setLabel_forSegment_("Word", 2)
            self._ghostwriter_seg.setSegmentStyle_(Cocoa.NSSegmentStyleRounded)
            mode_map = {"sentence": 0, "line": 1, "word": 2}
            self._ghostwriter_seg.setSelectedSegment_(
                mode_map.get(cfg.get("ghostwriter_mode", "sentence"), 0)
            )
            self._ghostwriter_seg.setTarget_(self)
            self._ghostwriter_seg.setAction_("ghostwriterModeChanged:")
            cvs.add(self._ghostwriter_seg, height=28)

        card4 = _card(card_w, ghost_builder)
        vs.add(card4, height=card4.frame().size.height)
        vs.space(20)

        # Card 5 — Murmur Mode
        lbl5 = _section_label("Murmur Mode")
        vs.add(lbl5, height=16)
        vs.space(6)

        def murmur_builder(cvs, w):
            # Gain
            gain_row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            gl = _label("Gain", font_size=13)
            gl.setFrameOrigin_(Cocoa.NSMakePoint(0, 0))
            gain_row.addSubview_(gl)
            self._murmur_gain_label = _label(
                f"{cfg.get('murmur_gain', 3.0):.1f}", font_size=13,
                weight=Cocoa.NSFontWeightMedium)
            self._murmur_gain_label.setAlignment_(Cocoa.NSTextAlignmentRight)
            self._murmur_gain_label.setFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            gain_row.addSubview_(self._murmur_gain_label)
            cvs.add(gain_row, height=20)
            cvs.space(4)

            self._murmur_gain_slider = Cocoa.NSSlider.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 22)
            )
            self._murmur_gain_slider.setMinValue_(1.0)
            self._murmur_gain_slider.setMaxValue_(10.0)
            self._murmur_gain_slider.setFloatValue_(cfg.get("murmur_gain", 3.0))
            self._murmur_gain_slider.setTarget_(self)
            self._murmur_gain_slider.setAction_("murmurGainChanged:")
            cvs.add(self._murmur_gain_slider, height=22)
            cvs.space(14)

            # Noise Gate
            gate_row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            nl = _label("Noise Gate", font_size=13)
            nl.setFrameOrigin_(Cocoa.NSMakePoint(0, 0))
            gate_row.addSubview_(nl)
            self._murmur_gate_label = _label(
                f"{cfg.get('murmur_noise_gate_db', -50.0):.0f} dB", font_size=13,
                weight=Cocoa.NSFontWeightMedium)
            self._murmur_gate_label.setAlignment_(Cocoa.NSTextAlignmentRight)
            self._murmur_gate_label.setFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            gate_row.addSubview_(self._murmur_gate_label)
            cvs.add(gate_row, height=20)
            cvs.space(4)

            self._murmur_gate_slider = Cocoa.NSSlider.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 22)
            )
            self._murmur_gate_slider.setMinValue_(-80.0)
            self._murmur_gate_slider.setMaxValue_(-20.0)
            self._murmur_gate_slider.setFloatValue_(cfg.get("murmur_noise_gate_db", -50.0))
            self._murmur_gate_slider.setTarget_(self)
            self._murmur_gate_slider.setAction_("murmurGateChanged:")
            cvs.add(self._murmur_gate_slider, height=22)
            cvs.space(14)

            # Min Utterance
            utt_row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            ul = _label("Min Utterance", font_size=13)
            ul.setFrameOrigin_(Cocoa.NSMakePoint(0, 0))
            utt_row.addSubview_(ul)
            self._murmur_utterance_label = _label(
                f"{int(cfg.get('murmur_min_utterance_ms', 80))} ms", font_size=13,
                weight=Cocoa.NSFontWeightMedium)
            self._murmur_utterance_label.setAlignment_(Cocoa.NSTextAlignmentRight)
            self._murmur_utterance_label.setFrame_(Cocoa.NSMakeRect(0, 0, w, 20))
            utt_row.addSubview_(self._murmur_utterance_label)
            cvs.add(utt_row, height=20)
            cvs.space(4)

            self._murmur_utterance_slider = Cocoa.NSSlider.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 22)
            )
            self._murmur_utterance_slider.setMinValue_(40)
            self._murmur_utterance_slider.setMaxValue_(400)
            self._murmur_utterance_slider.setIntValue_(cfg.get("murmur_min_utterance_ms", 80))
            self._murmur_utterance_slider.setTarget_(self)
            self._murmur_utterance_slider.setAction_("murmurUtteranceChanged:")
            cvs.add(self._murmur_utterance_slider, height=22)

        card5 = _card(card_w, murmur_builder)
        vs.add(card5, height=card5.frame().size.height)

        return _scrollable_section(container, vs, 2000)

    # ------------------------------------------------------------------
    # Section: History (card-based)
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_history_section(self):
        content_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        card_w = content_w - CONTENT_PAD * 2

        outer = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, content_w, WINDOW_HEIGHT)
        )
        outer.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )

        # Top bar: search + clear
        bar_y = WINDOW_HEIGHT - 52
        search_w = card_w - 100
        self._search_field = Cocoa.NSSearchField.alloc().initWithFrame_(
            Cocoa.NSMakeRect(CONTENT_PAD, bar_y, search_w, 28)
        )
        self._search_field.setPlaceholderString_("Search transcriptions\u2026")
        self._search_field.setTarget_(self)
        self._search_field.setAction_("searchChanged:")
        self._search_field.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewMinYMargin
        )
        outer.addSubview_(self._search_field)

        clear_btn = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(content_w - CONTENT_PAD - 90, bar_y, 90, 28)
        )
        clear_btn.setTitle_("Clear All")
        clear_btn.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        clear_btn.setTarget_(self)
        clear_btn.setAction_("clearHistory:")
        clear_btn.setAutoresizingMask_(
            Cocoa.NSViewMinXMargin | Cocoa.NSViewMinYMargin
        )
        outer.addSubview_(clear_btn)

        # Scrollable card list
        scroll_rect = Cocoa.NSMakeRect(0, 30, content_w, WINDOW_HEIGHT - 90)
        self._history_scroll = Cocoa.NSScrollView.alloc().initWithFrame_(scroll_rect)
        self._history_scroll.setHasVerticalScroller_(True)
        self._history_scroll.setDrawsBackground_(False)
        self._history_scroll.setBorderType_(Cocoa.NSNoBorder)
        self._history_scroll.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewHeightSizable
        )

        self._history_container = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, content_w, 10)
        )
        self._history_scroll.setDocumentView_(self._history_container)
        outer.addSubview_(self._history_scroll)

        # Bottom count
        self._history_count_label = _label(
            "", font_size=11, color=Cocoa.NSColor.tertiaryLabelColor()
        )
        self._history_count_label.setFrame_(
            Cocoa.NSMakeRect(CONTENT_PAD, 6, card_w, 18)
        )
        self._history_count_label.setAutoresizingMask_(
            Cocoa.NSViewWidthSizable | Cocoa.NSViewMaxYMargin
        )
        outer.addSubview_(self._history_count_label)

        return outer

    @objc.python_method
    def _rebuild_history_cards(self):
        """Rebuild the card-based history list from self._history_data."""
        if self._history_container is None:
            return

        # Clear old cards
        for sub in list(self._history_container.subviews()):
            sub.removeFromSuperview()

        content_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        card_w = content_w - CONTENT_PAD * 2
        card_gap = 10

        # Subtle shadow for each card (Wispr Flow style)
        shadow = Cocoa.NSShadow.alloc().init()
        shadow.setShadowColor_(
            Cocoa.NSColor.shadowColor().colorWithAlphaComponent_(0.08)
        )
        shadow.setShadowOffset_(Cocoa.NSMakeSize(0, -1))
        shadow.setShadowBlurRadius_(3)

        # Build cards first to get their actual heights
        cards = []
        for i, entry in enumerate(self._history_data):
            def entry_builder(cvs, w, e=entry):
                # Transcription text first (primary content)
                text = e.get("cleaned_text") or e.get("raw_text", "")
                txt = Cocoa.NSTextField.alloc().initWithFrame_(
                    Cocoa.NSMakeRect(0, 0, w, 18)
                )
                txt.setStringValue_(text)
                txt.setFont_(Cocoa.NSFont.systemFontOfSize_(13.5))
                txt.setTextColor_(Cocoa.NSColor.labelColor())
                txt.setEditable_(False)
                txt.setSelectable_(True)
                txt.setDrawsBackground_(False)
                txt.setBezeled_(False)
                txt.cell().setWraps_(True)
                txt.cell().setLineBreakMode_(Cocoa.NSLineBreakByWordWrapping)
                # Calculate wrapped height using the cell
                cell_size = txt.cell().cellSizeForBounds_(
                    Cocoa.NSMakeRect(0, 0, w, 10000)
                )
                text_h = max(cell_size.height, 18)
                txt.setFrame_(Cocoa.NSMakeRect(0, 0, w, text_h))
                cvs.add(txt, height=text_h)

                cvs.space(8)

                # Metadata below (secondary — timestamp)
                time_str = _ts_relative(e["timestamp"])
                meta = _label(time_str, font_size=11,
                              color=Cocoa.NSColor.tertiaryLabelColor())
                cvs.add(meta, height=14)

            c = _card(card_w, entry_builder)
            c.setShadow_(shadow)
            cards.append(c)

        total_h = max(
            sum(c.frame().size.height + card_gap for c in cards) + CONTENT_PAD,
            10,
        )
        self._history_container.setFrameSize_(Cocoa.NSMakeSize(content_w, total_h))

        y_cursor = total_h
        for c in cards:
            ch = c.frame().size.height
            y_cursor -= ch + card_gap
            c.setFrameOrigin_(Cocoa.NSMakePoint(CONTENT_PAD, y_cursor))
            self._history_container.addSubview_(c)

        # Scroll to top
        self._history_container.scrollPoint_(
            Cocoa.NSMakePoint(0, self._history_container.frame().size.height)
        )

    # ------------------------------------------------------------------
    # Section: Account
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_account_section(self):
        acct = account.load_account()
        content_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        card_w = content_w - CONTENT_PAD * 2

        container = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, content_w, 1200)
        )
        vs = _VStack(container, 1200 - 20, left=CONTENT_PAD, width=card_w)

        # Card 1 — Profile
        lbl1 = _section_label("Profile")
        vs.add(lbl1, height=16)
        vs.space(6)

        def profile_builder(cvs, w):
            ROW_H = 60
            row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, ROW_H))

            avatar_size = 44
            avatar_bg = Cocoa.NSBox.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, (ROW_H - avatar_size) / 2, avatar_size, avatar_size)
            )
            avatar_bg.setBoxType_(Cocoa.NSBoxCustom)
            avatar_bg.setCornerRadius_(avatar_size / 2)
            avatar_bg.setFillColor_(Cocoa.NSColor.controlAccentColor())
            avatar_bg.setBorderWidth_(0)
            avatar_bg.setContentViewMargins_(Cocoa.NSMakeSize(0, 0))
            row.addSubview_(avatar_bg)

            self._avatar_label = _label("?", font_size=20, bold=True,
                                        color=Cocoa.NSColor.whiteColor())
            self._avatar_label.setAlignment_(Cocoa.NSTextAlignmentCenter)
            self._avatar_label.setFrame_(
                Cocoa.NSMakeRect(0, (ROW_H - avatar_size) / 2, avatar_size, avatar_size)
            )
            row.addSubview_(self._avatar_label)

            info_x = avatar_size + 14
            self._profile_name_label = _label("Not signed in", font_size=15,
                                              weight=Cocoa.NSFontWeightSemibold)
            self._profile_name_label.setFrame_(
                Cocoa.NSMakeRect(info_x, ROW_H / 2 + 2, w - info_x - 110, 22)
            )
            row.addSubview_(self._profile_name_label)

            self._profile_email_label = _label(
                "", font_size=12, color=Cocoa.NSColor.secondaryLabelColor()
            )
            self._profile_email_label.setFrame_(
                Cocoa.NSMakeRect(info_x, ROW_H / 2 - 18, w - info_x - 110, 18)
            )
            row.addSubview_(self._profile_email_label)

            self._sign_in_button = Cocoa.NSButton.alloc().initWithFrame_(
                Cocoa.NSMakeRect(w - 100, (ROW_H - 28) / 2, 100, 28)
            )
            self._sign_in_button.setBezelStyle_(Cocoa.NSBezelStyleRounded)
            self._sign_in_button.setTarget_(self)
            self._sign_in_button.setAction_("toggleSignIn:")
            row.addSubview_(self._sign_in_button)

            cvs.add(row, height=ROW_H)

        card1 = _card(card_w, profile_builder)
        vs.add(card1, height=card1.frame().size.height)
        vs.space(20)

        # Card 2 — Credentials (hidden when signed in)
        lbl2 = _section_label("Credentials")
        vs.add(lbl2, height=16)
        vs.space(6)

        def cred_builder(cvs, w):
            lbl = _label("Email", font_size=12,
                         color=Cocoa.NSColor.secondaryLabelColor())
            cvs.add(lbl, height=16)
            cvs.space(4)

            self._email_field = Cocoa.NSTextField.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 24)
            )
            self._email_field.setPlaceholderString_("you@example.com")
            self._email_field.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
            cvs.add(self._email_field, height=24)
            cvs.space(14)

            lbl2 = _label("Display Name", font_size=12,
                          color=Cocoa.NSColor.secondaryLabelColor())
            cvs.add(lbl2, height=16)
            cvs.space(4)

            self._name_field = Cocoa.NSTextField.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, w, 24)
            )
            self._name_field.setPlaceholderString_("Your Name")
            self._name_field.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
            cvs.add(self._name_field, height=24)

        self._credentials_card = _card(card_w, cred_builder)
        vs.add(self._credentials_card, height=self._credentials_card.frame().size.height)

        return _scrollable_section(container, vs, 1200)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def cleanupSliderChanged_(self, sender):
        val = int(sender.intValue())
        config.set_value("cleanup_level", val)
        names = ["Light", "Moderate", "Aggressive"]
        self._cleanup_label.setStringValue_(names[val])

    def modelChanged_(self, sender):
        models = ["base.en", "small.en"]
        config.set_value("model", models[sender.indexOfSelectedItem()])

    def delaySliderChanged_(self, sender):
        val = int(sender.intValue())
        config.set_value("paste_delay_ms", val)
        self._delay_label.setStringValue_(f"{val} ms")

    def searchChanged_(self, sender):
        query = str(self._search_field.stringValue()).strip()
        if query:
            self._history_data = history.search(query)
        else:
            self._history_data = history.get_recent()
        self._rebuild_history_cards()
        self._update_history_count()

    def clearHistory_(self, sender):
        alert = Cocoa.NSAlert.alloc().init()
        alert.setMessageText_("Clear All History?")
        alert.setInformativeText_(
            "This will permanently delete all transcription history. This cannot be undone."
        )
        alert.addButtonWithTitle_("Clear All")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(Cocoa.NSAlertStyleWarning)
        if alert.runModal() == Cocoa.NSAlertFirstButtonReturn:
            history.clear_all()
            self._refresh_history()

    def toggleSignIn_(self, sender):
        acct = account.load_account()
        if acct["signed_in"]:
            account.sign_out()
        else:
            email = str(self._email_field.stringValue()).strip()
            name = str(self._name_field.stringValue()).strip()
            if not email:
                return
            account.sign_in(email, name)
        self._refresh_account_ui()

    def prefChanged_(self, sender):
        prefs = {
            "auto_copy": bool(self._auto_copy_switch.state()),
            "sound_feedback": bool(self._sound_switch.state()),
            "show_overlay": bool(self._overlay_switch.state()),
        }
        account.update_preferences(prefs)

    def contextStitchChanged_(self, sender):
        config.set_value("context_stitching", bool(sender.state()))

    def adaptiveSilenceChanged_(self, sender):
        config.set_value("adaptive_silence", bool(sender.state()))

    def confidenceReviewChanged_(self, sender):
        config.set_value("confidence_review", bool(sender.state()))

    def cadenceFeedbackChanged_(self, sender):
        config.set_value("cadence_feedback", bool(sender.state()))

    def ghostwriterEnabledChanged_(self, sender):
        config.set_value("ghostwriter_enabled", bool(sender.state()))

    def ghostwriterModeChanged_(self, sender):
        modes = ["sentence", "line", "word"]
        idx = sender.selectedSegment()
        if 0 <= idx < len(modes):
            config.set_value("ghostwriter_mode", modes[idx])

    def murmurGainChanged_(self, sender):
        val = round(sender.floatValue(), 1)
        config.set_value("murmur_gain", val)
        self._murmur_gain_label.setStringValue_(f"{val:.1f}")

    def murmurGateChanged_(self, sender):
        val = round(sender.floatValue(), 0)
        config.set_value("murmur_noise_gate_db", val)
        self._murmur_gate_label.setStringValue_(f"{int(val)} dB")

    def murmurUtteranceChanged_(self, sender):
        val = int(sender.intValue())
        config.set_value("murmur_min_utterance_ms", val)
        self._murmur_utterance_label.setStringValue_(f"{val} ms")

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    @objc.python_method
    def _refresh_history(self):
        self._history_data = history.get_recent()
        self._rebuild_history_cards()
        self._update_history_count()

    @objc.python_method
    def _update_history_count(self):
        if self._history_count_label:
            total = history.count()
            noun = "transcription" if total == 1 else "transcriptions"
            self._history_count_label.setStringValue_(f"{total} {noun}")

    @objc.python_method
    def _refresh_account_ui(self):
        acct = account.load_account()
        signed_in = acct["signed_in"]

        if self._sign_in_button:
            self._sign_in_button.setTitle_("Sign Out" if signed_in else "Sign In")

        if self._profile_name_label:
            if signed_in:
                self._profile_name_label.setStringValue_(acct["display_name"])
                self._profile_email_label.setStringValue_(acct["email"])
                initial = acct["display_name"][0].upper() if acct["display_name"] else "?"
                self._avatar_label.setStringValue_(initial)
            else:
                self._profile_name_label.setStringValue_("Not signed in")
                self._profile_email_label.setStringValue_("")
                self._avatar_label.setStringValue_("?")

        if self._email_field:
            if signed_in:
                self._email_field.setStringValue_(acct["email"])
                self._email_field.setEditable_(False)
                self._name_field.setStringValue_(acct["display_name"])
                self._name_field.setEditable_(False)
            else:
                self._email_field.setStringValue_("")
                self._email_field.setEditable_(True)
                self._name_field.setStringValue_("")
                self._name_field.setEditable_(True)

        if self._credentials_card:
            self._credentials_card.setHidden_(signed_in)

        prefs = acct["preferences"]
        if self._auto_copy_switch:
            self._auto_copy_switch.setState_(
                Cocoa.NSControlStateValueOn if prefs.get("auto_copy") else Cocoa.NSControlStateValueOff
            )
        if self._sound_switch:
            self._sound_switch.setState_(
                Cocoa.NSControlStateValueOn if prefs.get("sound_feedback") else Cocoa.NSControlStateValueOff
            )
        if self._overlay_switch:
            self._overlay_switch.setState_(
                Cocoa.NSControlStateValueOn if prefs.get("show_overlay") else Cocoa.NSControlStateValueOff
            )

    # ------------------------------------------------------------------
    # NSTableViewDataSource — sidebar only now
    # ------------------------------------------------------------------

    def numberOfRowsInTableView_(self, table_view):
        if table_view is self._sidebar_table:
            return len(SIDEBAR_ITEMS)
        return 0

    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        if table_view is self._sidebar_table:
            return SIDEBAR_ITEMS[row][1]
        return ""

    # ------------------------------------------------------------------
    # NSTableViewDelegate
    # ------------------------------------------------------------------

    def tableView_viewForTableColumn_row_(self, table_view, column, row):
        if table_view is not self._sidebar_table:
            return None

        cell_id = "SidebarCell"
        cell = table_view.makeViewWithIdentifier_owner_(cell_id, self)
        if cell is None:
            cell = Cocoa.NSTableCellView.alloc().initWithFrame_(
                Cocoa.NSMakeRect(0, 0, SIDEBAR_WIDTH - 20, 34)
            )
            cell.setIdentifier_(cell_id)

            img_view = Cocoa.NSImageView.alloc().initWithFrame_(
                Cocoa.NSMakeRect(8, 7, 20, 20)
            )
            cell.addSubview_(img_view)
            cell.setImageView_(img_view)

            txt = Cocoa.NSTextField.alloc().initWithFrame_(
                Cocoa.NSMakeRect(34, 7, SIDEBAR_WIDTH - 60, 20)
            )
            txt.setBezeled_(False)
            txt.setDrawsBackground_(False)
            txt.setEditable_(False)
            txt.setSelectable_(False)
            txt.setFont_(Cocoa.NSFont.systemFontOfSize_(13))
            cell.addSubview_(txt)
            cell.setTextField_(txt)

        icon_name, label_text, _ = SIDEBAR_ITEMS[row]
        img = _sf_symbol(icon_name, size=14)
        if img:
            cell.imageView().setImage_(img)
            cell.imageView().setContentTintColor_(Cocoa.NSColor.secondaryLabelColor())
        cell.textField().setStringValue_(label_text)

        return cell

    def tableViewSelectionDidChange_(self, notification):
        table_view = notification.object()
        if table_view is self._sidebar_table:
            row = table_view.selectedRow()
            if 0 <= row < len(SIDEBAR_ITEMS):
                section_id = SIDEBAR_ITEMS[row][2]
                self._switch_to_section(section_id)

    # ------------------------------------------------------------------
    # NSSplitViewDelegate — pin sidebar width
    # ------------------------------------------------------------------

    def splitView_constrainMinCoordinate_ofSubviewAt_(self, split_view, proposed, idx):
        if idx == 0:
            return SIDEBAR_WIDTH
        return proposed

    def splitView_constrainMaxCoordinate_ofSubviewAt_(self, split_view, proposed, idx):
        if idx == 0:
            return SIDEBAR_WIDTH
        return proposed

    def splitView_shouldAdjustSizeOfSubview_(self, split_view, subview):
        if subview is split_view.subviews()[0]:
            return False
        return True


# ---------------------------------------------------------------------------
# Menu Bar Status Item
# ---------------------------------------------------------------------------

class MenuBar(Cocoa.NSObject):
    """NSStatusBar item with dropdown menu that opens the settings window."""

    def init(self):
        self = objc.super(MenuBar, self).init()
        if self is None:
            return None
        self._status_item = None
        self._settings_controller = None
        return self

    def setup(self):
        self._settings_controller = SettingsWindowController.alloc().init()

        status_bar = Cocoa.NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            Cocoa.NSVariableStatusItemLength
        )
        button = self._status_item.button()
        button.setTitle_("M")
        button.setFont_(Cocoa.NSFont.boldSystemFontOfSize_(14))

        menu = Cocoa.NSMenu.alloc().init()

        settings_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Settings\u2026", "openSettings:", ","
        )
        settings_item.setTarget_(self)
        menu.addItem_(settings_item)

        menu.addItem_(Cocoa.NSMenuItem.separatorItem())

        quit_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit MuttR", "quitApp:", "q"
        )
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        self._status_item.setMenu_(menu)

    def openSettings_(self, sender):
        self._settings_controller.show()

    def quitApp_(self, sender):
        Cocoa.NSApp.terminate_(None)
