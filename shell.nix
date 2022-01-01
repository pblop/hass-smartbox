with import <nixpkgs> {
  overlays = [
    (self: super: rec {
      home-assistant = super.nur.repos.graham33.home-assistant.override {
        packageOverrides = self.lib.composeExtensions super.nur.repos.graham33.homeAssistantPackageOverrides pythonOverrides;
      };

      pythonOverrides = (pySelf: pySuper: rec {
        smartbox = pySuper.smartbox.overridePythonAttrs (o: {
          src = ../smartbox;
        });

        hass-smartbox = (super.nur.repos.graham33.hass-smartbox.override {
          inherit home-assistant;
        }).overrideAttrs (o: {
          src = ./.;
        });
      });
    })
  ];
};
let
  pythonEnv = home-assistant.python.withPackages (ps: with ps; [
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
