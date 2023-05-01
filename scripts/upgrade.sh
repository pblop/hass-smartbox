#!/usr/bin/env zsh

set -euo pipefail

update_requirements() {
    pkg=$1
    dep_name=$2
    method=$3
    version=$(nix eval ".#packages.x86_64-linux.$pkg.version" | sed -e 's/"//g')
    if [[ $method == "minor" ]]; then
        minor_version=$(echo $version | sed -e 's/[^\.]\+$/0/')
        next_minor_version=$(semver bump minor $minor_version)
        sed -i "s/^${dep_name}[>=].*$/$dep_name>=$minor_version,<$next_minor_version/" requirements_test.txt
    elif [[ $method == "exact" ]]; then
        sed -i "s/^${dep_name}[>=].*$/$dep_name==$version/" requirements_test.txt
    else
        echo "Unknown method $method" >&2
        exit 1
    fi
}

# Update everything
nix flake update

nur_rev=$(jq -r '.nodes.nur.locked.rev' flake.lock)
echo nix-community/NUR: $nur_rev

graham33_nur_rev=$(curl -s https://raw.githubusercontent.com/nix-community/NUR/$nur_rev/repos.json.lock | jq -r '.repos.graham33.rev')
echo graham33/nur-packages: $graham33_nur_rev

# Make sure we're using the same nixpkgs as graham33/nur-packages
# This doesn't work for some reason...
#nix flake lock --update-input nixpkgs --inputs-from github:graham33/nur-packages/$graham33_nur_rev
# Get nixpkgs revision from graham33/nur-packages' lock file and use this:
nur_nixpkgs_rev=$(curl -s https://raw.githubusercontent.com/graham33/nur-packages/$graham33_nur_rev/flake.lock | jq -r '.nodes.nixpkgs.locked.rev')
echo graham33/nur-packages nixpkgs rev: $nur_nixpkgs_rev
nix flake lock --update-input nixpkgs --override-input nixpkgs github:NixOS/nixpkgs/$nur_nixpkgs_rev

update_requirements home-assistant homeassistant minor
update_requirements python3Packages.homeassistant-stubs homeassistant-stubs minor
update_requirements pkgs.nur.repos.graham33.pytest-homeassistant-custom-component pytest-homeassistant-custom-component exact
