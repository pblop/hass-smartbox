with import <nixpkgs> {};
with python38Packages;

buildPythonPackage rec {
  name = "hass-smartbox";
  src = ".";
  propagatedBuildInputs = [ flake8
                            yapf
                          ];
}
