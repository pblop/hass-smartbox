with import <nixpkgs> {};
let
  python = python39.override {
    packageOverrides = pySelf: pySuper: {
      inherit (nur.repos.graham33.python39Packages) homeassistant-stubs monkeytype pytest-homeassistant-custom-component;
      hass-smartbox = nur.repos.graham33.python39Packages.hass-smartbox.overrideAttrs (o: {
        src = ./.;
      });
    };
  };
  pythonEnv = python.withPackages (ps: with ps; [
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
