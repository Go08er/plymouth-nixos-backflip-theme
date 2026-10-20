{ pkgs ? import <nixpkgs> { } }:

let
  theme = pkgs.callPackage ../default.nix { };
  workaroundChecks = import ./manim-workaround.nix { inherit pkgs; };
in
pkgs.runCommand "goobnix-plymouth-script-tests" {
  nativeBuildInputs = [ pkgs.stdenv.cc pkgs.pkg-config ];
  buildInputs = [ pkgs.plymouth ];
} ''
  test -e ${workaroundChecks}
  cc -Wall -Wextra ${./runner.c} \
    -I${pkgs.plymouth.src}/src/plugins/splash/script \
    $(pkg-config --cflags ply-splash-graphics) \
    ${pkgs.plymouth}/lib/plymouth/script.so \
    $(pkg-config --libs ply-splash-graphics) -o script-check
  ./script-check ${./mocks.script} \
    ${theme}/share/plymouth/themes/goobnix/goobnix.script \
    ${./assertions.script}
  touch "$out"
''
