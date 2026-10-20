{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: [
    (ps.callPackage ./goobnix-plymouth/manim.nix { })
    ps.pillow
  ]);
in
pkgs.mkShell {
  packages = with pkgs; [
    python
    ffmpeg
    poppler-utils
  ];
}
