#!/bin/bash -ex

main() {
    local pkgs=("tests" "generate_compose" "verify_rpms" "clean_spacerequests")
    pipenv run isort --profile black "${pkgs[@]}"
    pipenv run black "${pkgs[@]}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
