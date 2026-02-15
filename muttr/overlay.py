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
_SPRITE_W = 140
_SPRITE_H = 140
_SPRITE_IMG_H = 110   # space for the dog
_SPRITE_LABEL_H = 24  # space for the status text

CORNER_RADIUS = 22
BAR_COUNT = 5
BG_COLOR = (0.15, 0.15, 0.15, 0.85)

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
        self._level = 0.0
        self._smoothed_level = 0.0
        self._smoothed_motion = 0.0  # extra-smooth value for transform effects
        self._tick = 0  # render tick counter for frame pacing
        return self

    def setFrames_(self, frames):
        self._frames = frames
        self._frame_idx = 0
        self.setNeedsDisplay_(True)

    def setLevel_(self, level):
        self._level = level
        self._smoothed_level = self._smoothed_level * 0.7 + level * 0.3
        self.setNeedsDisplay_(True)

    def setState_(self, state):
        self._state = state
        self.setNeedsDisplay_(True)

    def tick(self):
        """Called at 30 FPS. Advance sprite frame at variable rate."""
        self._tick += 1
        # 3-frame ear-flop loop (~1s per frame, full cycle ~3s)
        interval = 30
        if self._frames and self._tick >= interval:
            self._tick = 0
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        import math
        import time

        if self._state == "idle" or not self._frames:
            return

        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height
        level = self._smoothed_level

        # Draw rounded background
        path = Cocoa.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, CORNER_RADIUS, CORNER_RADIUS
        )
        bg = Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(*BG_COLOR)
        bg.setFill()
        path.fill()

        Cocoa.NSGraphicsContext.saveGraphicsState()
        path.addClip()

        # --- Soft pulsing glow behind the dog ---
        # Draw concentric ovals from large (faint) to small (brighter)
        # to simulate a radial gradient glow. Scales with audio level.
        if level > 0.002:
            cx = w / 2
            cy = _SPRITE_LABEL_H + (h - _SPRITE_LABEL_H) / 2
            # Clamp level into a usable 0-1 intensity range
            intensity = min(1.0, level * 8.0)
            layers = 5
            max_radius = 50 + intensity * 20
            for ring in range(layers):
                # ring 0 = outermost (biggest, faintest), ring 4 = innermost
                t_ring = ring / (layers - 1)  # 0.0 outer → 1.0 inner
                r = max_radius * (1.0 - t_ring * 0.6)  # outer=full, inner=40%
                a = intensity * (0.03 + t_ring * 0.12)  # outer=0.03, inner=0.15
                glow_rect = Cocoa.NSMakeRect(cx - r, cy - r, r * 2, r * 2)
                Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    1.0, 0.5, 0.3, a
                ).setFill()
                Cocoa.NSBezierPath.bezierPathWithOvalInRect_(glow_rect).fill()

        # --- Draw current sprite frame with programmatic motion ---
        img = self._frames[self._frame_idx]
        img_size = img.size()
        img_area_h = h - _SPRITE_LABEL_H
        scale = min(w / img_size.width, img_area_h / img_size.height)
        draw_w = img_size.width * scale
        draw_h = img_size.height * scale
        draw_x = (w - draw_w) / 2
        draw_y = _SPRITE_LABEL_H + (img_area_h - draw_h) / 2

        t = time.time()

        # Boost low audio levels so even quiet speech gets a strong response
        boosted_target = math.sqrt(min(1.0, level * 10.0)) if level > 0.005 else 0.0
        # Smooth the motion value heavily — 93% old / 7% new for buttery easing
        self._smoothed_motion = self._smoothed_motion * 0.93 + boosted_target * 0.07
        motion = self._smoothed_motion

        # 1. Breathing / scale pulse
        idle_breath = math.sin(t * math.pi) * 0.02  # gentle 0.5 Hz oscillation
        speak_scale = motion * 0.22
        scale_factor = 1.0 + idle_breath + speak_scale

        # 2. Vertical bounce
        bounce_y = motion * 12.0

        # 3. Head tilt — slow deliberate cock to one side, not fast wobble
        tilt_rad = motion * 6.0 * math.sin(t * 3 * math.pi) * (math.pi / 180)

        # Apply transform: translate to sprite center, rotate, scale, translate back
        xf = Cocoa.NSAffineTransform.transform()
        cx = draw_x + draw_w / 2
        cy = draw_y + draw_h / 2 + bounce_y
        xf.translateXBy_yBy_(cx, cy)
        xf.rotateByRadians_(tilt_rad)
        xf.scaleBy_(scale_factor)
        xf.translateXBy_yBy_(-cx, -cy)

        Cocoa.NSGraphicsContext.saveGraphicsState()
        xf.concat()
        draw_rect = Cocoa.NSMakeRect(draw_x, draw_y, draw_w, draw_h)
        img.drawInRect_fromRect_operation_fraction_(
            draw_rect, Cocoa.NSZeroRect, Cocoa.NSCompositingOperationSourceOver, 1.0
        )
        Cocoa.NSGraphicsContext.restoreGraphicsState()

        # --- Status label + live dots in label area ---
        if self._state == "recording":
            label = "Listening"
        else:
            label = "Working..."

        attrs = {
            Cocoa.NSFontAttributeName: Cocoa.NSFont.systemFontOfSize_weight_(
                11, Cocoa.NSFontWeightMedium
            ),
            Cocoa.NSForegroundColorAttributeName: Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0, 1.0, 1.0, 0.7
            ),
        }
        attr_str = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
            label, attrs
        )
        text_size = attr_str.size()

        if self._state == "recording":
            # Draw label + dots together, centered as a unit
            t = time.time()
            dot_count = 3
            dot_r = 1.5
            dot_gap = 3.5
            dots_w = dot_count * dot_r * 2 + (dot_count - 1) * dot_gap
            spacing = 4.0  # gap between text and dots
            total_unit_w = text_size.width + spacing + dots_w

            label_x = (w - total_unit_w) / 2
            label_y = (_SPRITE_LABEL_H - text_size.height) / 2
            attr_str.drawAtPoint_(Cocoa.NSMakePoint(label_x, label_y))

            # Dots to the right of the label, vertically centered on text
            dots_start_x = label_x + text_size.width + spacing
            dot_center_y = label_y + text_size.height / 2

            Cocoa.NSColor.colorWithCalibratedRed_green_blue_alpha_(
                1.0, 1.0, 1.0, 0.7
            ).setFill()

            for i in range(dot_count):
                phase = math.sin(t * 5 + i * 0.9) * 0.5 + 0.5
                bounce = min(level * 60, 3.0) * phase
                dcx = dots_start_x + i * (dot_r * 2 + dot_gap) + dot_r
                dcy = dot_center_y + bounce
                dot_rect = Cocoa.NSMakeRect(
                    dcx - dot_r, dcy - dot_r, dot_r * 2, dot_r * 2,
                )
                Cocoa.NSBezierPath.bezierPathWithOvalInRect_(dot_rect).fill()
        else:
            # Non-recording: just center the label
            label_x = (w - text_size.width) / 2
            label_y = (_SPRITE_LABEL_H - text_size.height) / 2
            attr_str.drawAtPoint_(Cocoa.NSMakePoint(label_x, label_y))

        Cocoa.NSGraphicsContext.restoreGraphicsState()


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
        """Update audio level for waveform/sprite animation."""
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
            1.0 / 30,  # 30 FPS render loop; frame advance is tick-paced inside SpriteView
            True,
            lambda timer: self._view.tick(),
        )

    def _stop_animation(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
