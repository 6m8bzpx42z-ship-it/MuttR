#!/usr/bin/env python3
"""Generate the MuttR app icon using CoreGraphics.

Creates a bold "M" on a rounded-rect gradient background with a small
microphone accent. Outputs an .icns file via iconutil.
"""

import math
import os
import shutil
import subprocess
import sys
import tempfile

import Quartz
from Quartz import (
    CGBitmapContextCreate,
    CGBitmapContextCreateImage,
    CGColorSpaceCreateDeviceRGB,
    CGContextAddArc,
    CGContextAddLineToPoint,
    CGContextBeginPath,
    CGContextClip,
    CGContextClosePath,
    CGContextDrawLinearGradient,
    CGContextFillPath,
    CGContextMoveToPoint,
    CGContextRestoreGState,
    CGContextSaveGState,
    CGContextSetLineCap,
    CGContextSetLineJoin,
    CGContextSetLineWidth,
    CGContextSetRGBFillColor,
    CGContextSetRGBStrokeColor,
    CGContextStrokePath,
    CGGradientCreateWithColorComponents,
    CGImageDestinationAddImage,
    CGImageDestinationCreateWithURL,
    CGImageDestinationFinalize,
    CGPointMake,
    kCGImageAlphaPremultipliedLast,
    kCGLineCapRound,
    kCGLineJoinRound,
)
from CoreFoundation import CFURLCreateWithFileSystemPath, kCFAllocatorDefault, kCFURLPOSIXPathStyle


ICON_SIZES = [16, 32, 128, 256, 512, 1024]


def create_context(size):
    """Create an RGBA bitmap context at the given pixel size."""
    cs = CGColorSpaceCreateDeviceRGB()
    ctx = CGBitmapContextCreate(
        None, size, size, 8, size * 4, cs, kCGImageAlphaPremultipliedLast
    )
    return ctx


def draw_rounded_rect(ctx, x, y, w, h, radius):
    """Draw a rounded rectangle path."""
    CGContextBeginPath(ctx)
    # Start at top-left, after the corner
    CGContextMoveToPoint(ctx, x + radius, y)
    # Bottom edge
    CGContextAddLineToPoint(ctx, x + w - radius, y)
    CGContextAddArc(ctx, x + w - radius, y + radius, radius, -math.pi / 2, 0, 0)
    # Right edge
    CGContextAddLineToPoint(ctx, x + w, y + h - radius)
    CGContextAddArc(ctx, x + w - radius, y + h - radius, radius, 0, math.pi / 2, 0)
    # Top edge
    CGContextAddLineToPoint(ctx, x + radius, y + h)
    CGContextAddArc(ctx, x + radius, y + h - radius, radius, math.pi / 2, math.pi, 0)
    # Left edge
    CGContextAddLineToPoint(ctx, x, y + radius)
    CGContextAddArc(ctx, x + radius, y + radius, radius, math.pi, 3 * math.pi / 2, 0)
    CGContextClosePath(ctx)


def draw_gradient_bg(ctx, size):
    """Fill the background with a deep blue-to-purple gradient in a rounded rect."""
    margin = size * 0.02
    radius = size * 0.22
    draw_rounded_rect(ctx, margin, margin, size - 2 * margin, size - 2 * margin, radius)

    CGContextSaveGState(ctx)
    CGContextClip(ctx)

    cs = CGColorSpaceCreateDeviceRGB()
    # Deep navy blue -> rich purple gradient
    colors = [
        0.10, 0.12, 0.28, 1.0,  # dark navy at bottom
        0.30, 0.15, 0.50, 1.0,  # rich purple at top
    ]
    locations = [0.0, 1.0]
    gradient = CGGradientCreateWithColorComponents(cs, colors, locations, 2)
    CGContextDrawLinearGradient(
        ctx, gradient,
        CGPointMake(size / 2, 0),
        CGPointMake(size / 2, size),
        0,
    )
    CGContextRestoreGState(ctx)


def draw_letter_m(ctx, size):
    """Draw a bold stylized 'M' in white."""
    CGContextSaveGState(ctx)

    # M dimensions
    lw = size * 0.09  # stroke width
    left = size * 0.18
    right = size * 0.82
    bottom = size * 0.20
    top = size * 0.78
    mid_x = size * 0.50
    mid_y = size * 0.38  # how low the V dips

    CGContextSetRGBStrokeColor(ctx, 1.0, 1.0, 1.0, 1.0)
    CGContextSetLineWidth(ctx, lw)
    CGContextSetLineCap(ctx, kCGLineCapRound)
    CGContextSetLineJoin(ctx, kCGLineJoinRound)

    CGContextBeginPath(ctx)
    CGContextMoveToPoint(ctx, left, bottom)
    CGContextAddLineToPoint(ctx, left, top)
    CGContextAddLineToPoint(ctx, mid_x, mid_y)
    CGContextAddLineToPoint(ctx, right, top)
    CGContextAddLineToPoint(ctx, right, bottom)
    CGContextStrokePath(ctx)

    CGContextRestoreGState(ctx)


def draw_microphone(ctx, size):
    """Draw a small microphone accent in the bottom-right area."""
    CGContextSaveGState(ctx)

    # Position mic in bottom-right
    mic_x = size * 0.76
    mic_bottom = size * 0.08
    mic_w = size * 0.06
    mic_h = size * 0.10
    mic_radius = mic_w / 2

    # Mic body (capsule shape) - warm orange/amber accent
    CGContextSetRGBFillColor(ctx, 0.95, 0.60, 0.20, 0.9)

    # Bottom half-circle
    CGContextBeginPath(ctx)
    CGContextAddArc(ctx, mic_x, mic_bottom + mic_radius, mic_radius, math.pi, 0, 0)
    # Rectangle body
    CGContextAddLineToPoint(ctx, mic_x + mic_radius, mic_bottom + mic_h - mic_radius)
    # Top half-circle
    CGContextAddArc(ctx, mic_x, mic_bottom + mic_h - mic_radius, mic_radius, 0, math.pi, 0)
    CGContextClosePath(ctx)
    CGContextFillPath(ctx)

    # Mic stand line
    stand_w = size * 0.012
    CGContextSetRGBStrokeColor(ctx, 0.95, 0.60, 0.20, 0.7)
    CGContextSetLineWidth(ctx, stand_w)
    CGContextSetLineCap(ctx, kCGLineCapRound)

    # Curved cradle
    cradle_r = mic_w * 0.8
    CGContextBeginPath(ctx)
    CGContextAddArc(ctx, mic_x, mic_bottom + mic_h * 0.4, cradle_r, 0, math.pi, 0)
    CGContextStrokePath(ctx)

    # Vertical stand
    CGContextBeginPath(ctx)
    CGContextMoveToPoint(ctx, mic_x, mic_bottom + mic_h * 0.4 - cradle_r)
    CGContextAddLineToPoint(ctx, mic_x, mic_bottom - size * 0.01)
    CGContextStrokePath(ctx)

    # Base
    base_w = size * 0.04
    CGContextBeginPath(ctx)
    CGContextMoveToPoint(ctx, mic_x - base_w / 2, mic_bottom - size * 0.01)
    CGContextAddLineToPoint(ctx, mic_x + base_w / 2, mic_bottom - size * 0.01)
    CGContextStrokePath(ctx)

    CGContextRestoreGState(ctx)


def draw_icon(size):
    """Draw the complete icon at the given pixel size and return a CGImage."""
    ctx = create_context(size)
    draw_gradient_bg(ctx, size)
    draw_letter_m(ctx, size)
    draw_microphone(ctx, size)
    return CGBitmapContextCreateImage(ctx)


def save_png(image, path):
    """Save a CGImage as a PNG file."""
    url = CFURLCreateWithFileSystemPath(
        kCFAllocatorDefault, path, kCFURLPOSIXPathStyle, False
    )
    dest = CGImageDestinationCreateWithURL(url, "public.png", 1, None)
    CGImageDestinationAddImage(dest, image, None)
    CGImageDestinationFinalize(dest)


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resources_dir = os.path.join(project_root, "resources")
    os.makedirs(resources_dir, exist_ok=True)

    iconset_dir = os.path.join(resources_dir, "MuttR.iconset")
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir)

    # Generate PNGs at all required sizes (1x and 2x)
    needed = set()
    for s in ICON_SIZES:
        needed.add(s)
    # Also need 2x versions for Retina
    retina_bases = [16, 32, 128, 256, 512]

    for s in sorted(needed):
        print(f"  Generating {s}x{s}...")
        img = draw_icon(s)

        # 1x version
        if s <= 512:
            name = f"icon_{s}x{s}.png"
            save_png(img, os.path.join(iconset_dir, name))

        # 2x version (e.g., 32px image -> icon_16x16@2x.png)
        half = s // 2
        if half in retina_bases:
            name_2x = f"icon_{half}x{half}@2x.png"
            save_png(img, os.path.join(iconset_dir, name_2x))

    # 512@2x uses the 1024 image
    img_1024 = draw_icon(1024)
    save_png(img_1024, os.path.join(iconset_dir, "icon_512x512@2x.png"))

    # Convert to .icns
    icns_path = os.path.join(resources_dir, "MuttR.icns")
    print(f"  Converting to .icns...")
    subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
        check=True,
    )

    # Clean up iconset
    shutil.rmtree(iconset_dir)

    print(f"  Icon saved to {icns_path}")
    return icns_path


if __name__ == "__main__":
    print("Generating MuttR icon...")
    main()
    print("Done!")
