{ pkgs ? import <nixpkgs> { } }:

let
  # Evaluate the real helper with a tiny package double, independently of
  # whichever Manim/Click versions the test runner currently supplies.
  select = manimVersion: clickVersion:
    let
      original = {
        version = manimVersion;
        postPatch = "touch upstream-hook-ran";
        overridePythonAttrs = change: original // change original;
      };
    in {
      inherit original;
      selected = import ../manim.nix {
        inherit (pkgs) lib;
        manim = original;
        click.version = clickVersion;
      };
    };
  unchanged = manimVersion: clickVersion:
    let result = select manimVersion clickVersion;
    in result.selected.postPatch == result.original.postPatch;
  affected = select "0.22.0" "8.4.2";
  before = pkgs.writeText "manim-help-before.py" ''
    init_help = "Usage: manim init [OPTIONS] COMMAND [ARGS]..."
    cfg_help = "Usage: manim cfg [OPTIONS] COMMAND [ARGS]..."
  '';
  after = pkgs.writeText "manim-help-after.py" ''
    init_help = "Usage: manim init [OPTIONS] [COMMAND] [ARGS]..."
    cfg_help = "Usage: manim cfg [OPTIONS] COMMAND [ARGS]..."
  '';
in
assert unchanged "0.21.0" "8.4.2";
assert unchanged "0.22.0" "8.3.3";
assert unchanged "0.22.0" "8.4.1";
assert unchanged "0.22.1" "8.4.2";
assert unchanged "0.23.0" "8.5.0";
assert affected.selected.postPatch != affected.original.postPatch;
assert pkgs.lib.hasPrefix affected.original.postPatch affected.selected.postPatch;
pkgs.runCommand "goobnix-manim-workaround-tests" { } ''
  mkdir -p tests/interface
  cp ${before} tests/interface/test_commands.py
  chmod u+w tests/interface/test_commands.py
  ${affected.selected.postPatch}
  cmp tests/interface/test_commands.py ${after}
  test -f upstream-hook-ran

  # An upstream-fixed source (or a repeated hook) must be left byte-for-byte
  # unchanged; unrelated help expectations must retain their original text.
  ${affected.selected.postPatch}
  cmp tests/interface/test_commands.py ${after}

  # Retired/reorganized upstream tests must not cause a missing-file failure.
  mv tests/interface/test_commands.py test-commands-moved.py
  ${affected.selected.postPatch}
  test ! -e tests/interface/test_commands.py
  printf '%s\n' 'Manim workaround version guards, exact edit, upstream hook, fixed-source no-op and missing-file checks passed'
  touch "$out"
''
