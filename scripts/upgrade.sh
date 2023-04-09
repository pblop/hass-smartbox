#!/usr/bin/env zsh

set -euo pipefail

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
