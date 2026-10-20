{
  lib,
  stdenvNoCC,
  python3,
  oddColor ? "#FFFF00",
  evenColor ? "#00FFFF",
  size ? 480,
}:

assert lib.assertMsg (builtins.isString oddColor && builtins.match "#[0-9a-fA-F]{6}" oddColor != null)
  "goobnix-plymouth: oddColor must be a #RRGGBB color";
assert lib.assertMsg (builtins.isString evenColor && builtins.match "#[0-9a-fA-F]{6}" evenColor != null)
  "goobnix-plymouth: evenColor must be a #RRGGBB color";
assert lib.assertMsg (builtins.isInt size && size >= 128 && size <= 1024)
  "goobnix-plymouth: size must be an integer between 128 and 1024";

let
  python = python3.withPackages (ps: [
    (ps.callPackage ./manim.nix { })
    ps.pillow
  ]);
  frameCount = 60;
  frameRate = 50;
in
stdenvNoCC.mkDerivation {
  pname = "goobnix-plymouth";
  version = "2.0.0";

  # Only these source files enter the build. Preview videos, caches and
  # unrelated desktop themes neither trigger rebuilds nor enter the output.
  dontUnpack = true;
  nativeBuildInputs = [ python ];
  strictDeps = true;
  PYTHONDONTWRITEBYTECODE = "1";

  buildPhase = ''
    runHook preBuild
    cp ${../throbber_spring.py} throbber_spring.py
    cp ${../throbber_polygon.py} throbber_polygon.py
    cp ${./render.py} render.py
    python render.py \
      --odd-color ${lib.escapeShellArg oddColor} \
      --even-color ${lib.escapeShellArg evenColor} \
      --size ${toString size} --output frames
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    themeDir="$out/share/plymouth/themes/goobnix"
    mkdir -p "$themeDir"
    install -m 644 frames/frame-*.png "$themeDir/"
    substitute ${./goobnix.plymouth.in} "$themeDir/goobnix.plymouth" \
      --subst-var-by THEME_DIR "$themeDir"
    substitute ${./goobnix.script.in} "$themeDir/goobnix.script" \
      --subst-var-by FRAME_COUNT ${toString frameCount} \
      --subst-var-by FRAME_RATE ${toString frameRate}
    install -D -m 644 ${../LICENSE} "$out/share/doc/goobnix-plymouth/LICENSE"
    install -D -m 644 ${../NOTICE} "$out/share/doc/goobnix-plymouth/NOTICE"
    runHook postInstall
  '';

  # The theme must not pull Python, Manim, FFmpeg or source trees into initrd.
  allowedReferences = [ "out" ];

  passthru = {
    inherit oddColor evenColor size frameCount frameRate;
    duration = 1.2;
  };

  meta = {
    description = "Build-time rendered, two-color Nix orbit animation for Plymouth";
    license = [ lib.licenses.mit lib.licenses.cc-by-40 ];
    platforms = lib.platforms.linux;
  };
}
