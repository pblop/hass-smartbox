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
      home-assistant = pkgs.nur.repos.graham33.home-assistant;
      python = home-assistant.python;
      pythonPackages = python.pkgs;
      hass-smartbox = pkgs.nur.repos.graham33.hass-smartbox.overridePythonAttrs (o: {
        propagatedBuildInputs = (o.propagatedBuildInputs or []) ++ (with pythonPackages; [
        ]);
      });
    in pkgs.mkShell {
      inputsFrom = [
        hass-smartbox
      ];
      packages = with pkgs; [
        black
        mypy
        #py-spy
        ruff
        semver-tool
      ];
    };
    packages."${system}" = pkgs;
  };
}
