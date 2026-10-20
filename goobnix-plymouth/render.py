"""Render and validate lossless Plymouth assets; used only during the Nix build."""

import argparse
from pathlib import Path
import re

from manim import config, tempconfig
from PIL import Image, ImageColor

from throbber_spring import SpringBackflip


def hex_color(value: str) -> str:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise argparse.ArgumentTypeError("expected a #RRGGBB color")
    return value.upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odd-color", type=hex_color, required=True)
    parser.add_argument("--even-color", type=hex_color, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 128 <= args.size <= 1024:
        parser.error("size must be between 128 and 1024")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    # 50 fps at twice the former speed samples exactly the same 60 poses.
    # Direct PNG output avoids H.264 artifacts and preserves configured colors.
    # Manim 0.22 replaced the old output switches with an explicit sequence
    # format. Detect the API so existing Nixpkgs inputs keep working too.
    legacy_output = "write_to_movie" in config
    output_settings = (
        {"format": "png", "write_to_movie": False, "save_last_frame": False}
        if legacy_output else {"format": "png-sequence"}
    )
    with tempconfig({
        **output_settings,
        "renderer": "cairo",
        "pixel_width": args.size,
        "pixel_height": args.size,
        "frame_rate": 50,
        "disable_caching": True,
        "progress_bar": "none",
        "media_dir": str(output.parent / "render-work"),
        "images_dir": str(output),
        "output_file": "frame-",
        "zero_pad": 2,
    }):
        SpringBackflip(
            odd_color=args.odd_color,
            even_color=args.even_color,
            playback_speed=2.0,
        ).render()

    if not legacy_output:
        # New Manim writes frame-/00.png instead of frame-00.png. Keep the
        # installed Plymouth filenames identical across both render APIs.
        sequence = output / "frame-"
        rendered = [sequence / f"{i:02d}.png" for i in range(60)]
        if sorted(sequence.glob("*.png")) != rendered:
            raise RuntimeError("render did not produce exactly 60 numbered sequence frames")
        for i, frame in enumerate(rendered):
            frame.rename(output / f"frame-{i:02d}.png")
        sequence.rmdir()

    expected = [output / f"frame-{i:02d}.png" for i in range(60)]
    if sorted(output.glob("*.png")) != expected:
        raise RuntimeError("render did not produce exactly frame-00.png through frame-59.png")
    for frame in expected:
        with Image.open(frame) as image:
            if image.size != (args.size, args.size):
                raise RuntimeError(f"wrong dimensions: {frame.name}")
            if image.convert("RGBA").getchannel("A").getextrema() != (255, 255):
                raise RuntimeError(f"unexpected transparent background: {frame.name}")
            rgb = image.convert("RGB")
        rgb.save(frame, optimize=True, compress_level=9)

    with Image.open(expected[0]) as image:
        colors = {color for _, color in image.getcolors(maxcolors=args.size * args.size)}
        for color in (args.odd_color, args.even_color):
            if ImageColor.getrgb(color) not in colors:
                raise RuntimeError(f"configured color {color} missing from the rendered logo")
    total = sum(frame.stat().st_size for frame in expected)
    print(f"Validated 60 lossless {args.size}x{args.size} frames; {total:,} bytes; 50 fps / 1.2 s")


if __name__ == "__main__":
    main()
