"""Always-on-top overlay bubble UI with sprite animation support."""

import glob
import os

import Cocoa
import Quartz
import objc


# ---------------------------------------------------------------------------
# Frame loader — looks for PNGs in resources/overlay/
# ---------------------------------------------------------------------------

_RESOURCES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resources", "overlay",
)


def _load_frames(prefix):
    """Load numbered PNGs matching prefix (e.g. 'recording_01.png').

    Returns a list of NSImage or empty list if none found.
    """
    pattern = os.path.join(_RESOURCES, f"{prefix}_*.png")
    paths = sorted(glob.glob(pattern))
    frames = []
    for p in paths:
        img = Cocoa.NSImage.alloc().initWithContentsOfFile_(p)
        if img:
            frames.append(img)
    return frames


# ---------------------------------------------------------------------------
# Dimensions — bigger bubble when using sprite frames
# ---------------------------------------------------------------------------

# Waveform fallback dimensions
_WAVE_W = 140
_WAVE_H = 44

# Sprite animation dimensions
_SPRITE_W = 100
_SPRITE_H = 100

CORNER_RADIUS = 22
BAR_COUNT = 5
BG_COLOR = (0.15, 0.15, 0.15, 0.85)

# Animation rate for sprite frames (fps)
SPRITE_FPS = 10


# ---------------------------------------------------------------------------
# Waveform view (fallback when no sprite frames exist)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Sprite view — draws frames from PNG sequences
# ---------------------------------------------------------------------------

class SpriteView(Cocoa.NSView):
    """Cycles through pre-loaded image frames for animation."""

    def initWithFrame_(self, frame):
        self = objc.super(SpriteView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._frames = []
        self._frame_idx = 0
        self._state = "idle"
        return self

    def setFrames_(self, frames):
        self._frames = frames
        self._frame_idx = 0
        self.setNeedsDisplay_(True)

    def setState_(self, state):
        self._state = state
        self.setNeedsDisplay_(True)

    def advance(self):
        """Move to the next frame in the loop."""
        if self._frames:
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)
            self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        if self._state == "idle" or not self._frames:
            return

        bounds = self.bounds()

        # Draw rounded background
        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, CORNER_RADIUS, CORNER_RADIUS
        )
        bg = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(*BG_COLOR)
        bg.setFill()
        path.fill()

        # Clip to rounded rect so the sprite doesn't bleed outside
        path.addClip()

        # Draw current frame centered
        img = self._frames[self._frame_idx]
        img_size = img.size()
        # Scale to fit within bounds while preserving aspect ratio
        scale = min(
            bounds.size.width / img_size.width,
            bounds.size.height / img_size.height,
        )
        draw_w = img_size.width * scale
        draw_h = img_size.height * scale
        draw_x = (bounds.size.width - draw_w) / 2
        draw_y = (bounds.size.height - draw_h) / 2

        draw_rect = Cocoa.NSMakeRect(draw_x, draw_y, draw_w, draw_h)
        img.drawInRect_fromRect_operation_fraction_(
            draw_rect, Cocoa.NSZeroRect, Cocoa.NSCompositingOperationSourceOver, 1.0
        )


# ---------------------------------------------------------------------------
# Overlay — auto-selects sprite vs waveform based on available assets
# ---------------------------------------------------------------------------

class Overlay:
    def __init__(self):
        self._panel = None
        self._view = None
        self._timer = None
        self._use_sprites = False
        self._recording_frames = []
        self._transcribing_frames = []

    def setup(self):
        """Create the overlay panel. Must be called on the main thread."""
        # Try to load sprite frames
        self._recording_frames = _load_frames("recording")
        self._transcribing_frames = _load_frames("transcribing")
        self._use_sprites = bool(self._recording_frames)

        if self._use_sprites:
            bubble_w, bubble_h = _SPRITE_W, _SPRITE_H
        else:
            bubble_w, bubble_h = _WAVE_W, _WAVE_H

        screen = Cocoa.NSScreen.mainScreen()
        screen_frame = screen.frame()

        x = (screen_frame.size.width - bubble_w) / 2
        y = 80  # just above the Dock

        frame = Cocoa.NSMakeRect(x, y, bubble_w, bubble_h)

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

        content_frame = Cocoa.NSMakeRect(0, 0, bubble_w, bubble_h)
        if self._use_sprites:
            self._view = SpriteView.alloc().initWithFrame_(content_frame)
        else:
            self._view = WaveformView.alloc().initWithFrame_(content_frame)
        self._panel.setContentView_(self._view)

    def show_recording(self):
        """Show overlay in recording state."""
        if self._use_sprites:
            self._view.setFrames_(self._recording_frames)
            self._view.setState_("recording")
            self._panel.orderFront_(None)
            self._start_sprite_animation()
        else:
            self._view.setState_("recording")
            self._panel.orderFront_(None)
            self._start_waveform_animation()

    def show_transcribing(self):
        """Show overlay in transcribing state."""
        self._stop_animation()
        if self._use_sprites and self._transcribing_frames:
            self._view.setFrames_(self._transcribing_frames)
            self._view.setState_("transcribing")
            self._start_sprite_animation()
        elif self._use_sprites:
            # No transcribing frames — just freeze on last recording frame
            self._view.setState_("transcribing")
            self._view.setNeedsDisplay_(True)
        else:
            self._view.setState_("transcribing")
            self._view.setNeedsDisplay_(True)

    def hide(self):
        """Hide the overlay."""
        self._stop_animation()
        self._view.setState_("idle")
        self._panel.orderOut_(None)

    def update_level(self, level):
        """Update audio level for waveform animation."""
        if not self._use_sprites:
            self._view.setLevel_(level)

    def _start_waveform_animation(self):
        self._stop_animation()
        self._timer = Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0 / 30,  # 30fps
            True,
            lambda timer: self._view.setNeedsDisplay_(True),
        )

    def _start_sprite_animation(self):
        self._stop_animation()
        self._timer = Cocoa.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            1.0 / SPRITE_FPS,
            True,
            lambda timer: self._view.advance(),
        )

    def _stop_animation(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
