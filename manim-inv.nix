{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: [
    ps.manim
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
