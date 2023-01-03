{
  description = "Smartbox Home Assistant Custom Component";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    nur.url = "github:nix-community/NUR";
  };

  outputs = { self, nixpkgs, nur }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [
        (self: super: {
          nur = import nur {
            nurpkgs = self;
            pkgs = self;
          };
        })
      ];
    };
  in {
    devShells.${system}.default = let
      python = pkgs.nur.repos.graham33.home-assistant.python;
      hass-smartbox = pkgs.nur.repos.graham33.hass-smartbox.overridePythonAttrs (o: {
        propagatedBuildInputs = (o.propagatedBuildInputs or []) ++ (with python.pkgs; [
        ]);
      });
    in pkgs.mkShell {
      inputsFrom = [
        hass-smartbox
      ];
      packages = with pkgs; [
        black
        mypy
        py-spy
        python3Packages.flake8
      ];
    };
  };
}
