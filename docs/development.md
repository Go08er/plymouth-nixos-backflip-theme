# Development

## Build and test

From the repository root:

```bash
nix-build -E 'let pkgs = import <nixpkgs> {}; in pkgs.callPackage ./goobnix-plymouth {
  oddColor = "#FFFF00";
  evenColor = "#00FFFF";
  size = 480;
}'
nix-build goobnix-plymouth/tests --no-out-link
```

Nix provides Manim, Pillow and their dependencies; no global Python setup
or existing video is required. `result/share/plymouth/themes/goobnix/`
contains only 60 RGB PNGs, the theme descriptor and a Plymouth script.
Rendering dependencies do not enter the theme's runtime closure.
Code and logo license notices are included under `share/doc/goobnix-plymouth/`.

Each build validates frame count, dimensions, opacity and configured colors.
The 91 script checks use Plymouth's real parser/interpreter with mocked
graphics and daemon APIs. They cover frame sequencing, password masking,
messages, display repositioning and immediate quit. They do not replace
real boot testing, especially encrypted-disk unlock.

The verified environment is x86_64 Linux, Nixpkgs 26.11pre-git, Python 3.14.7,
Manim 0.21.0 / 0.22.0 and Plymouth 26.134.222. The package uses the caller's
Nixpkgs; other versions and platforms are not yet verified.

### Manim compatibility

Manim 0.22 removed `write_to_movie` and changed `format = "png"` to mean
the last frame only. The renderer detects the available output API, selects
`png-sequence` on 0.22+, and normalizes the new numbered subdirectory to
Plymouth's existing `frame-00.png` through `frame-59.png` filenames. Earlier
Manim keeps its original output settings. See the [upstream migration notes](https://github.com/ManimCommunity/manim/releases/tag/v0.22.0).

Test the Nixpkgs revision introducing Manim 0.22 independently of the system's
package input:

```bash
nix-build goobnix-plymouth/tests --no-out-link --arg pkgs \
  'import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/2a32e69922a9f432cea6ac49dca08c45e8669af4.tar.gz";
    sha256 = "sha256-fUeyDAaCPu3ibqp7G01vrbkayF6r4pTX0swHOKTscsY=";
  }) {}'
```

## Local module

As an alternative to `pkgs.callPackage`, import `goobnix-plymouth/module.nix`
and set:

```nix
boot.plymouth.goobnix = {
  enable = true;
  oddColor = "#FFFF00";
  evenColor = "#00FFFF";
  size = 480;
};
```

Do not combine this with the README's direct theme configuration. For a
flake-based system, keep these sources inside the tracked configuration
repository or use a pinned source input. Keep the repository layout intact,
including both Python sources, `goobnix-plymouth/`, `LICENSE` and `NOTICE`.

## Animation

`throbber_spring.py` contains the active motion; `throbber_polygon.py`
supplies its shared logo geometry. Odd pieces are 1, 3, 5 clockwise from the
upper-left arm; even pieces are 2, 4, 6. Identically colored partners make
one round visually periodic. The current loop plays the original 60 poses
at twice their former speed, without interpolation or changed motion curves.

```bash
nix-shell manim-inv.nix --run 'manim -r 480,480 --fps 50 throbber_spring.py SpringBackflip'
```

For a GIF from the built frames, enter `nix-shell manim-inv.nix`, then run:

```bash
ffmpeg -framerate 50 \
  -i result/share/plymouth/themes/goobnix/frame-%02d.png \
  -filter_complex '[0:v]split[frames][colors];[colors]palettegen=stats_mode=full[palette];[frames][palette]paletteuse=dither=bayer:bayer_scale=3' \
  -frames:v 60 -loop 0 docs/demo.gif
```

The GIF encodes a 20 ms delay per frame and loops indefinitely. Actual browser
playback cadence can vary. It is documentation only, not an input to the build.

## Boot resource use

The default PNGs total about 431 KiB on disk. Decoded RGBA buffers require
about 53 MiB at 480×480, or 23 MiB at 320×320, before Plymouth overhead.
Frame size accepts integers from 128 to 1024. The script preloads the frames,
swaps one sprite's image at 50 Hz, pauses for input and quits immediately.
Actual cadence depends on the machine and display backend.
