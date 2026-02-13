"""Always-on-top overlay bubble UI."""

import Cocoa
import Quartz
import objc


BUBBLE_WIDTH = 140
BUBBLE_HEIGHT = 44
CORNER_RADIUS = 22
BAR_COUNT = 5
BG_COLOR = (0.15, 0.15, 0.15, 0.85)


class WaveformView(Cocoa.NSView):
    """Custom view that draws mic icon + animated waveform bars."""

    def initWithFrame_(self, frame):
        self = objc.super(WaveformView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._level = 0.0
        self._state = "idle"  # idle, recording, transcribing
        return self

    def setLevel_(self, level):
        self._level = level
        self.setNeedsDisplay_(True)

    def setState_(self, state):
        self._state = state
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        # Draw rounded background
        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            self.bounds(), CORNER_RADIUS, CORNER_RADIUS
        )
        bg = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(*BG_COLOR)
        bg.setFill()
        path.fill()

        if self._state == "transcribing":
            self._draw_transcribing_text()
        elif self._state == "recording":
            self._draw_mic_icon()
            self._draw_waveform()

    def _draw_mic_icon(self):
        attrs = {
            Cocoa.NSFontAttributeName: Cocoa.NSFont.systemFontOfSize_(18),
            Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.whiteColor(),
        }
        mic = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            "\U0001f3a4", attrs
        )
        mic.drawAtPoint_(Cocoa.NSMakePoint(12, 10))

    def _draw_waveform(self):
        bar_area_x = 44
        bar_width = 4
        bar_spacing = 6
        max_height = 24
        center_y = self.bounds().size.height / 2

        white = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
            1.0, 1.0, 1.0, 0.9
        )
        white.setFill()

        import math
        import time

        t = time.time()

        for i in range(BAR_COUNT):
            # Animate bars with sine wave offset + audio level
            phase = math.sin(t * 6 + i * 1.2) * 0.5 + 0.5
            height = max(4, (self._level * 300 + phase * 8) * (max_height / 30))
            height = min(height, max_height)

            x = bar_area_x + i * (bar_width + bar_spacing)
            y = center_y - height / 2

            bar_rect = Cocoa.NSMakeRect(x, y, bar_width, height)
            bar_path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                bar_rect, bar_width / 2, bar_width / 2
            )
            bar_path.fill()

    def _draw_transcribing_text(self):
        attrs = {
            Cocoa.NSFontAttributeName: Cocoa.NSFont.systemFontOfSize_(13),
            Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0, 1.0, 1.0, 0.7
            ),
        }
        text = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            "Transcribing...", attrs
        )
        size = text.size()
        x = (self.bounds().size.width - size.width) / 2
        y = (self.bounds().size.height - size.height) / 2
        text.drawAtPoint_(Cocoa.NSMakePoint(x, y))


class Overlay:
    def __init__(self):
        self._panel = None
        self._view = None
        self._timer = None

    def setup(self):
        """Create the overlay panel. Must be called on the main thread."""
        screen = Cocoa.NSScreen.mainScreen()
        screen_frame = screen.frame()

        x = (screen_frame.size.width - BUBBLE_WIDTH) / 2
        y = 80  # just above the Dock

        frame = Cocoa.NSMakeRect(x, y, BUBBLE_WIDTH, BUBBLE_HEIGHT)

        self._panel = Cocoa.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            Cocoa.NSWindowStyleMaskBorderless | Cocoa.NSWindowStyleMaskNonactivatingPanel,
            Cocoa.NSBackingStoreBuffered,
            False,
        )
        self._panel.setLevel_(Cocoa.NSStatusWindowLevel)
        self._panel.setOpaque_(False)
        self._panel.setBackgroundColor_(Cocoa.NSColor.clearColor())
        self._panel.setHasShadow_(True)
        self._panel.setIgnoresMouseEvents_(True)
        self._panel.setCollectionBehavior_(
            Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces
            | Cocoa.NSWindowCollectionBehaviorStationary
        )

        content_frame = Cocoa.NSMakeRect(0, 0, BUBBLE_WIDTH, BUBBLE_HEIGHT)
        self._view = WaveformView.alloc().initWithFrame_(content_frame)
        self._panel.setContentView_(self._view)

    def show_recording(self):
        """Show overlay in recording state with animated waveform."""
        self._view.setState_("recording")
        self._panel.orderFront_(None)
        self._start_animation()

    def show_transcribing(self):
        """Show overlay in transcribing state."""
        self._stop_animation()
        self._view.setState_("transcribing")
        self._view.setNeedsDisplay_(True)

    def hide(self):
        """Hide the overlay."""
        self._stop_animation()
        self._view.setState_("idle")
        self._panel.orderOut_(None)

    def update_level(self, level):
        """Update audio level for waveform animation."""
        self._view.setLevel_(level)

    def _start_animation(self):
        """Start a timer to refresh the waveform animation."""
        self._stop_animation()
        self._timer = Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0 / 30,  # 30fps
            True,
            lambda timer: self._view.setNeedsDisplay_(True),
        )

    def _stop_animation(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
