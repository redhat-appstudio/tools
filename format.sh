#!/bin/bash -ex

main() {
    local pkgs=("tests" "generate_compose")
    pipenv run isort --profile black "${pkgs[@]}"
    pipenv run black "${pkgs[@]}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
