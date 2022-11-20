#!/bin/sh

set -eu

manifest_version() {
    sed -n -e 's/^.*"version": "\([0-9\.]\+\)".*$/\1/p' custom_components/smartbox/manifest.json
}

module_version() {
    sed -n -e 's/^__version__ = "\([0-9\.]\+\)".*$/\1/p' custom_components/smartbox/__init__.py
}

manifest_smartbox_version() {
    sed -n -e 's/^.*\(smartbox==[0-9\.]\+\(b[0-9]\+\)\?\).*$/\1/p' custom_components/smartbox/manifest.json
}

requirements_smartbox_version() {
    sed -n -e 's/^.*\(smartbox==[0-9\.]\+\(b[0-9]\+\)\?\).*$/\1/p' requirements_common.txt
}

if [ $(manifest_version) != $(module_version) ]
then
    echo "Manifest version $(manifest_version) does not match module $(module_version)" >&2
    exit 1
fi

if [ $(manifest_smartbox_version) != $(requirements_smartbox_version) ]
then
    echo "Manifest smartbox version $(manifest_smartbox_version) does not match requirements smartbox version $(requirements_smartbox_version)" >&2
    exit 1
fi

black --check .

flake8
