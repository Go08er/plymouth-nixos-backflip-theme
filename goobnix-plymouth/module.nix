{ config, lib, pkgs, ... }:

let
  cfg = config.boot.plymouth.goobnix;
  colorType = lib.types.strMatching "#[0-9a-fA-F]{6}";
in
{
  options.boot.plymouth.goobnix = {
    enable = lib.mkEnableOption "the build-time rendered Goobnix Plymouth theme";
    oddColor = lib.mkOption {
      type = colorType;
      default = "#FFFF00";
      example = "#FFBF00";
      description = "Color of clockwise pieces 1, 3 and 5, starting at the upper-left arm.";
    };
    evenColor = lib.mkOption {
      type = colorType;
      default = "#00FFFF";
      example = "#00BFFF";
      description = "Color of clockwise pieces 2, 4 and 6.";
    };
    size = lib.mkOption {
      type = lib.types.ints.between 128 1024;
      default = 480;
      example = 320;
      description = "Square frame size in pixels. Smaller frames reduce initrd and decoded-image costs.";
    };
  };

  config = lib.mkIf cfg.enable {
    boot.plymouth = {
      enable = true;
      theme = "goobnix";
      themePackages = [
        (pkgs.callPackage ./default.nix {
          inherit (cfg) oddColor evenColor size;
        })
      ];
    };
  };
}
