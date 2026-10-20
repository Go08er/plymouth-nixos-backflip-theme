{ lib, manim, click }:

# Click 8.4.2 intentionally brackets optional subcommands (pallets/click#3507).
# Manim 0.22.0's init-help snapshot still expects the old spelling. Limit this
# correction to the affected pair; a newer Manim uses Nixpkgs unchanged.
if manim.version == "0.22.0" && lib.versionAtLeast click.version "8.4.2" then
  manim.overridePythonAttrs (old: {
    postPatch = (old.postPatch or "") + "\n" + ''
      # Nixpkgs patches and its postPatch have already run. If upstream fixes
      # this same Manim version, the old expectation is absent: do nothing.
      if [ -f tests/interface/test_commands.py ] && \
        grep -Fq 'Usage: manim init [OPTIONS] COMMAND [ARGS]...' tests/interface/test_commands.py; then
        substituteInPlace tests/interface/test_commands.py \
          --replace-fail \
            'Usage: manim init [OPTIONS] COMMAND [ARGS]...' \
            'Usage: manim init [OPTIONS] [COMMAND] [ARGS]...'
      fi
    '';
  })
else
  manim
