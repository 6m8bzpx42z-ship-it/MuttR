"""First-run onboarding wizard — 3-page welcome flow."""

import os
import subprocess

import Cocoa
import objc

from muttr import config

# ---------------------------------------------------------------------------
# Reuse helper patterns from menubar.py
# ---------------------------------------------------------------------------

def _label(text, font_size=13, bold=False, color=None, weight=None):
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


def _card(width, content_builder, fill_color=None):
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


class _VStack:
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
# Window dimensions
# ---------------------------------------------------------------------------

WIN_W = 520
WIN_H = 420
PAD = 32
CONTENT_W = WIN_W - PAD * 2

# Orange gradient for primary buttons
_ORANGE_START = Cocoa.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.55, 0.0, 1.0)
_ORANGE_END = Cocoa.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.38, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Gradient button (orange pill)
# ---------------------------------------------------------------------------

class _GradientButton(Cocoa.NSButton):
    """Rounded button with orange gradient background and white text."""

    def initWithFrame_(self, frame):
        self = objc.super(_GradientButton, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setBordered_(False)
        self.setWantsLayer_(True)
        self.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        return self

    def drawRect_(self, rect):
        bounds = self.bounds()
        radius = bounds.size.height / 2
        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, radius, radius
        )

        gradient = Cocoa.NSGradient.alloc().initWithStartingColor_endingColor_(
            _ORANGE_START, _ORANGE_END
        )
        gradient.drawInBezierPath_angle_(path, 90)

        # Draw title centered
        title = self.title()
        attrs = {
            Cocoa.NSFontAttributeName: Cocoa.NSFont.systemFontOfSize_weight_(
                14, Cocoa.NSFontWeightSemibold
            ),
            Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.whiteColor(),
        }
        attr_str = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            title, attrs
        )
        size = attr_str.size()
        x = (bounds.size.width - size.width) / 2
        y = (bounds.size.height - size.height) / 2
        attr_str.drawAtPoint_(Cocoa.NSMakePoint(x, y))


def _orange_button(title, target, action, width=120, height=34):
    btn = _GradientButton.alloc().initWithFrame_(
        Cocoa.NSMakeRect(0, 0, width, height)
    )
    btn.setTitle_(title)
    btn.setTarget_(target)
    btn.setAction_(action)
    return btn


def _link_button(title, target, action, width=220, height=28):
    """Rounded bordered button for opening System Settings."""
    btn = Cocoa.NSButton.alloc().initWithFrame_(
        Cocoa.NSMakeRect(0, 0, width, height)
    )
    btn.setTitle_(title)
    btn.setBezelStyle_(Cocoa.NSBezelStyleRounded)
    btn.setTarget_(target)
    btn.setAction_(action)
    return btn


def _sf_symbol(name, size=16):
    img = Cocoa.NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
    if img is None:
        return None
    cfg = Cocoa.NSImageSymbolConfiguration.configurationWithPointSize_weight_(
        size, Cocoa.NSFontWeightRegular
    )
    return img.imageWithSymbolConfiguration_(cfg)


# ---------------------------------------------------------------------------
# Onboarding Window Controller
# ---------------------------------------------------------------------------

class OnboardingWindowController(Cocoa.NSObject):
    """3-page onboarding wizard shown on first run."""

    def init(self):
        self = objc.super(OnboardingWindowController, self).init()
        if self is None:
            return None
        self._window = None
        self._pages = []
        self._current_page = 0
        self._back_btn = None
        self._next_btn = None
        self._content_host = None
        return self

    @objc.python_method
    def show(self):
        if self._window is None:
            self._build()
        self._window.makeKeyAndOrderFront_(None)
        Cocoa.NSApp.activateIgnoringOtherApps_(True)

    # ------------------------------------------------------------------
    # Build window
    # ------------------------------------------------------------------

    @objc.python_method
    def _build(self):
        style = (
            Cocoa.NSWindowStyleMaskTitled
            | Cocoa.NSWindowStyleMaskClosable
        )
        rect = Cocoa.NSMakeRect(0, 0, WIN_W, WIN_H)
        self._window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, Cocoa.NSBackingStoreBuffered, False
        )
        self._window.setTitle_("Welcome to MuttR")
        self._window.center()
        self._window.setReleasedWhenClosed_(False)

        root = self._window.contentView()

        # Content area (above bottom bar)
        BAR_H = 52
        self._content_host = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, BAR_H, WIN_W, WIN_H - BAR_H)
        )
        root.addSubview_(self._content_host)

        # Bottom navigation bar
        bar = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WIN_W, BAR_H)
        )

        # Separator line at top of bar
        sep = Cocoa.NSBox.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, BAR_H - 1, WIN_W, 1)
        )
        sep.setBoxType_(Cocoa.NSBoxSeparator)
        bar.addSubview_(sep)

        self._back_btn = Cocoa.NSButton.alloc().initWithFrame_(
            Cocoa.NSMakeRect(PAD, 10, 80, 32)
        )
        self._back_btn.setTitle_("Back")
        self._back_btn.setBezelStyle_(Cocoa.NSBezelStyleRounded)
        self._back_btn.setTarget_(self)
        self._back_btn.setAction_("goBack:")
        bar.addSubview_(self._back_btn)

        self._next_btn = _orange_button("Get Started", self, "goNext:", width=130, height=32)
        self._next_btn.setFrameOrigin_(Cocoa.NSMakePoint(WIN_W - PAD - 130, 10))
        bar.addSubview_(self._next_btn)

        root.addSubview_(bar)

        # Build pages
        self._pages = [
            self._build_welcome_page(),
            self._build_permissions_page(),
            self._build_done_page(),
        ]

        self._show_page(0)

    # ------------------------------------------------------------------
    # Page navigation
    # ------------------------------------------------------------------

    @objc.python_method
    def _show_page(self, idx):
        self._current_page = idx

        for sub in list(self._content_host.subviews()):
            sub.removeFromSuperview()

        page = self._pages[idx]
        page.setFrame_(self._content_host.bounds())
        self._content_host.addSubview_(page)

        # Update buttons
        self._back_btn.setHidden_(idx == 0)

        if idx == 0:
            self._next_btn.setTitle_("Get Started")
        elif idx == 1:
            self._next_btn.setTitle_("Next")
        else:
            self._next_btn.setTitle_("Finish")

        self._next_btn.setNeedsDisplay_(True)

    def goBack_(self, sender):
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    def goNext_(self, sender):
        if self._current_page < 2:
            self._show_page(self._current_page + 1)
        else:
            # Finish: save config and close
            config.set_value("onboarding_completed", True)
            self._window.close()

    # ------------------------------------------------------------------
    # Page 1: Welcome
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_welcome_page(self):
        h = WIN_H - 52  # content area height
        page = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WIN_W, h)
        )

        # App icon
        icon_size = 96
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "resources", "MuttR.icns"
        )
        icon_img = Cocoa.NSImage.alloc().initWithContentsOfFile_(icon_path)
        if icon_img:
            icon_img.setSize_(Cocoa.NSMakeSize(icon_size, icon_size))

        icon_view = Cocoa.NSImageView.alloc().initWithFrame_(
            Cocoa.NSMakeRect((WIN_W - icon_size) / 2, h - icon_size - 50, icon_size, icon_size)
        )
        if icon_img:
            icon_view.setImage_(icon_img)
        page.addSubview_(icon_view)

        # Heading
        heading = _label("Talk, don't type.", font_size=24, bold=True)
        heading.setAlignment_(Cocoa.NSTextAlignmentCenter)
        heading.setFrame_(Cocoa.NSMakeRect(PAD, h - icon_size - 100, CONTENT_W, 32))
        page.addSubview_(heading)

        # Description
        desc = _label(
            "MuttR turns your voice into text \u2014 instantly,\nprivately, right on your Mac.",
            font_size=14,
            color=Cocoa.NSColor.secondaryLabelColor(),
        )
        desc.setAlignment_(Cocoa.NSTextAlignmentCenter)
        desc.setFrame_(Cocoa.NSMakeRect(PAD, h - icon_size - 155, CONTENT_W, 44))
        page.addSubview_(desc)

        return page

    # ------------------------------------------------------------------
    # Page 2: Permissions
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_permissions_page(self):
        h = WIN_H - 52
        page = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WIN_W, h)
        )

        card_w = CONTENT_W

        # Section heading
        heading = _label("MuttR needs two permissions", font_size=20, bold=True)
        heading.setAlignment_(Cocoa.NSTextAlignmentCenter)
        heading.setFrame_(Cocoa.NSMakeRect(PAD, h - 52, card_w, 28))
        page.addSubview_(heading)

        # Card 1: Accessibility
        def acc_builder(cvs, w):
            # Icon + title row
            row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 24))
            icon = _sf_symbol("accessibility", size=18)
            if icon:
                iv = Cocoa.NSImageView.alloc().initWithFrame_(
                    Cocoa.NSMakeRect(0, 0, 24, 24)
                )
                iv.setImage_(icon)
                iv.setContentTintColor_(Cocoa.NSColor.controlAccentColor())
                row.addSubview_(iv)
            title = _label("Accessibility", font_size=15, weight=Cocoa.NSFontWeightSemibold)
            title.setFrameOrigin_(Cocoa.NSMakePoint(30, 2))
            row.addSubview_(title)
            cvs.add(row, height=24)
            cvs.space(6)

            desc = _label(
                "So MuttR can type what you say into any app.\n"
                "Click below, then add MuttR to the list and turn it on.",
                font_size=12, color=Cocoa.NSColor.secondaryLabelColor()
            )
            desc.setFrame_(Cocoa.NSMakeRect(0, 0, w, 32))
            cvs.add(desc, height=32)
            cvs.space(10)

            btn = _link_button(
                "Open Accessibility Settings", self, "openAccessibility:"
            )
            cvs.add(btn, height=28)

        card1 = _card(card_w, acc_builder)
        card1_h = card1.frame().size.height
        card1.setFrameOrigin_(Cocoa.NSMakePoint(PAD, h - 60 - card1_h))
        page.addSubview_(card1)

        # Card 2: Microphone
        def mic_builder(cvs, w):
            row = Cocoa.NSView.alloc().initWithFrame_(Cocoa.NSMakeRect(0, 0, w, 24))
            icon = _sf_symbol("mic.fill", size=18)
            if icon:
                iv = Cocoa.NSImageView.alloc().initWithFrame_(
                    Cocoa.NSMakeRect(0, 0, 24, 24)
                )
                iv.setImage_(icon)
                iv.setContentTintColor_(Cocoa.NSColor.controlAccentColor())
                row.addSubview_(iv)
            title = _label("Microphone", font_size=15, weight=Cocoa.NSFontWeightSemibold)
            title.setFrameOrigin_(Cocoa.NSMakePoint(30, 2))
            row.addSubview_(title)
            cvs.add(row, height=24)
            cvs.space(6)

            desc = _label(
                "macOS will ask your permission the first time you\n"
                "record. Just click Allow when the popup appears.",
                font_size=12, color=Cocoa.NSColor.secondaryLabelColor()
            )
            desc.setFrame_(Cocoa.NSMakeRect(0, 0, w, 32))
            cvs.add(desc, height=32)
            cvs.space(10)

            hint = _label(
                "Already denied it? Click below to fix it.",
                font_size=11, color=Cocoa.NSColor.tertiaryLabelColor()
            )
            cvs.add(hint, height=14)
            cvs.space(6)

            btn = _link_button(
                "Open Microphone Settings", self, "openMicrophone:"
            )
            cvs.add(btn, height=28)

        card2 = _card(card_w, mic_builder)
        card2_h = card2.frame().size.height
        card2_y = h - 60 - card1_h - 14 - card2_h
        card2.setFrameOrigin_(Cocoa.NSMakePoint(PAD, card2_y))
        page.addSubview_(card2)

        return page

    def openAccessibility_(self, sender):
        subprocess.Popen([
            "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        ])

    def openMicrophone_(self, sender):
        subprocess.Popen([
            "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
        ])

    # ------------------------------------------------------------------
    # Page 3: Done
    # ------------------------------------------------------------------

    @objc.python_method
    def _build_done_page(self):
        h = WIN_H - 52
        page = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, WIN_W, h)
        )

        # Checkmark icon
        icon_size = 64
        icon = _sf_symbol("checkmark.circle.fill", size=48)
        if icon:
            iv = Cocoa.NSImageView.alloc().initWithFrame_(
                Cocoa.NSMakeRect((WIN_W - icon_size) / 2, h - icon_size - 60, icon_size, icon_size)
            )
            iv.setImage_(icon)
            iv.setContentTintColor_(
                Cocoa.NSColor.colorWithRed_green_blue_alpha_(0.2, 0.78, 0.35, 1.0)
            )
            page.addSubview_(iv)

        # Heading
        heading = _label("You're all set!", font_size=24, bold=True)
        heading.setAlignment_(Cocoa.NSTextAlignmentCenter)
        heading.setFrame_(Cocoa.NSMakeRect(PAD, h - icon_size - 110, CONTENT_W, 32))
        page.addSubview_(heading)

        # Instruction
        instruction = _label(
            "Hold the fn key and start talking.\nRelease to paste.",
            font_size=14,
            color=Cocoa.NSColor.secondaryLabelColor(),
        )
        instruction.setAlignment_(Cocoa.NSTextAlignmentCenter)
        instruction.setFrame_(Cocoa.NSMakeRect(PAD, h - icon_size - 165, CONTENT_W, 44))
        page.addSubview_(instruction)

        return page
