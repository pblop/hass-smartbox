with import <nixpkgs> {
  overlays = [
    (self: super: {
      pythonOverrides = pySelf: pySuper: {
        inherit (super.nur.repos.graham33.python39Packages)
          hass-smartbox smartbox homeassistant-stubs monkeytype pytest-homeassistant-custom-component;
      };
    })
    (self: super: rec {
      pythonOverrides = self.lib.composeExtensions super.pythonOverrides (pySelf: pySuper: rec {
        smartbox = pySuper.smartbox.overridePythonAttrs (o: {
          src = ../smartbox;
        });
        hass-smartbox = (pySuper.hass-smartbox.override {
          inherit smartbox;
        }).overridePythonAttrs (o: {
          src = ./.;
        });
      });
      python39 = super.python39.override {
        self = python39;
        packageOverrides = pythonOverrides;
      };
    })
  ];
};
let
  pythonEnv = python39.withPackages (ps: with ps; [
    flake8
    hass-smartbox
    # TODO: duplicating checkInputs from hass-smartbox
    homeassistant-stubs
    monkeytype
    mypy
    pytest
    pytest-aiohttp
    pytest-asyncio
    pytest-cov
    pytest-flake8
    pytest-homeassistant-custom-component
    pytest-mypy
    pytest-randomly
    pytest-sugar
    tox
    voluptuous
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}
