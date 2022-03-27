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
      });
    })
  ];
};
let
  pythonEnv = home-assistant.python.withPackages (ps: with ps; [
    flake8
    # TODO: duplicating checkInputs from hass-smartbox
    homeassistant-stubs
    monkeytype
    mypy
    pytest
    pytest-aiohttp
    pytest-cov
    pytest-flake8
    pytest-homeassistant-custom-component
    pytest-mypy
    pytest-randomly
    pytest-sugar
    smartbox
    tox
    voluptuous
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}
