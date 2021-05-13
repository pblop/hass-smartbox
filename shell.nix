with import <nixpkgs> {};
let
  python = python38.override {
    packageOverrides = pySelf: pySuper: {
      inherit (nur.repos.graham33.python3Packages) pytest-homeassistant-custom-component;
      hass-smartbox = nur.repos.graham33.python3Packages.hass-smartbox.overrideAttrs (o: {
        src = ./.;
      });
    };
  };
  pythonEnv = python.withPackages (ps: with ps; [
    flake8
    hass-smartbox
    # TODO: duplicating checkInputs from hass-smartbox
    mypy
    pytest
    pytest-aiohttp
    pytest-asyncio
    pytest-cov
    pytest-homeassistant-custom-component
    pytest-randomly
    pytest-sugar
    tox
  ]);
in mkShell {
  buildInputs = [
    black
    pythonEnv
  ];
}
