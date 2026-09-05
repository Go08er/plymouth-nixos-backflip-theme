{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [
    python3Packages.manim
    ffmpeg
    poppler-utils
  ];
}
