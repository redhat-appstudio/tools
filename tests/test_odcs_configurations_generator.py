"""Test odcs_configurations_generator.py"""

import pytest
from odcs.client.odcs import ComposeSourceBuild  # type: ignore
from odcs.client.odcs import (
    ComposeSourceModule,
    ComposeSourcePulp,
    ComposeSourceRawConfig,
    ComposeSourceTag,
)

from generate_compose.odcs_configurations_generator import ODCSConfigurationsGenerator
from generate_compose.protocols import ODCSComposeConfig, ODCSComposesConfigs


@pytest.mark.parametrize(
    "compose_inputs,expected_odcs_composes_configs",
    [
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "tag": "my-tag",
                        },
                        "kind": "ComposeSourceTag",
                        "additional_args": {},
                    },
                    {
                        "spec": {
                            "modules": ["mod1", "mod2", "mod3"],
                        },
                        "kind": "ComposeSourceModule",
                        "additional_args": {},
                    },
                    {
                        "spec": {
                            "content_sets": ["set1", "set2", "set3"],
                        },
                        "kind": "ComposeSourcePulp",
                        "additional_args": {},
                    },
                    {
                        "spec": {
                            "config_name": "my-conf",
                            "commit": "my-commit",
                        },
                        "kind": "ComposeSourceRawConfig",
                        "additional_args": {},
                    },
                    {
                        "spec": {
                            "builds": ["build1", "build2"],
                        },
                        "kind": "ComposeSourceBuild",
                        "additional_args": {},
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceTag("my-tag"),
                        additional_args={},
                    ),
                    ODCSComposeConfig(
                        spec=ComposeSourceModule(["mod1", "mod2", "mod3"]),
                        additional_args={},
                    ),
                    ODCSComposeConfig(
                        spec=ComposeSourcePulp(["set1", "set2", "set3"]),
                        additional_args={},
                    ),
                    ODCSComposeConfig(
                        spec=ComposeSourceRawConfig("my-conf", "my-commit"),
                        additional_args={},
                    ),
                    ODCSComposeConfig(
                        spec=ComposeSourceBuild(["build1", "build2"]),
                        additional_args={},
                    ),
                ]
            ),
            id="Composes of all types with mandatory inputs only",
        ),
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "tag": "t1",
                            "packages": ["p1", "p2"],
                            "builds": ["b1", "b2"],
                            "sigkeys": ["s1", "s2"],
                            "koji_event": 22,
                            "modular_koji_tags": ["mkt1", "mkt2"],
                            "module_defaults_url": "my-url",
                            "module_defaults_commit": "my-commit",
                            "scratch_modules": ["sm1", "sm2"],
                        },
                        "kind": "ComposeSourceTag",
                        "additional_args": {},
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceTag(
                            "t1",
                            packages=["p1", "p2"],
                            builds=["b1", "b2"],
                            sigkeys=["s1", "s2"],
                            koji_event=22,
                            modular_koji_tags=["mkt1", "mkt2"],
                            module_defaults_url="my-url",
                            module_defaults_commit="my-commit",
                            scratch_modules=["sm1", "sm2"],
                        ),
                        additional_args={},
                    ),
                ]
            ),
            id="Compose of type tag with all named arguments",
        ),
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "modules": ["m1", "m2"],
                            "sigkeys": ["s1", "s2"],
                            "module_defaults_url": "my-url",
                            "module_defaults_commit": "my-commit",
                            "scratch_modules": ["sm1", "sm2"],
                        },
                        "kind": "ComposeSourceModule",
                        "additional_args": {},
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceModule(
                            ["m1", "m2"],
                            sigkeys=["s1", "s2"],
                            module_defaults_url="my-url",
                            module_defaults_commit="my-commit",
                            scratch_modules=["sm1", "sm2"],
                        ),
                        additional_args={},
                    ),
                ]
            ),
            id="Compose of type module with all named arguments",
        ),
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "config_name": "my-conf",
                            "commit": "my-commit",
                            "koji_event": 22,
                        },
                        "kind": "ComposeSourceRawConfig",
                        "additional_args": {},
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceRawConfig(
                            "my-conf",
                            "my-commit",
                            koji_event=22,
                        ),
                        additional_args={},
                    ),
                ]
            ),
            id="Compose of type raw-config with all named arguments",
        ),
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "builds": ["build1", "build2"],
                            "sigkeys": ["s1", "s2"],
                        },
                        "kind": "ComposeSourceBuild",
                        "additional_args": {},
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceBuild(
                            ["build1", "build2"],
                            sigkeys=["s1", "s2"],
                        ),
                        additional_args={},
                    ),
                ]
            ),
            id="Compose of type build with all named arguments",
        ),
        pytest.param(
            {
                "composes": [
                    {
                        "spec": {
                            "builds": ["build1"],
                            "spec_kw_arg": "spec-kw-value",
                            "another_spec_kw_arg": "another-spec-kw-value",
                        },
                        "kind": "ComposeSourceBuild",
                        "additional_args": {
                            "some_arg": "some-value",
                            "another_arg": "another-value",
                            "one_more_arg": "one-more-value",
                        },
                    },
                ]
            },
            ODCSComposesConfigs(
                [
                    ODCSComposeConfig(
                        spec=ComposeSourceBuild(
                            ["build1"],
                            spec_kw_arg="spec-kw-value",
                            another_spec_kw_arg="another-spec-kw-value",
                        ),
                        additional_args={
                            "some_arg": "some-value",
                            "another_arg": "another-value",
                            "one_more_arg": "one-more-value",
                        },
                    ),
                ]
            ),
            id="Compose with source kwargs and additional arguments",
        ),
    ],
)
def test_odcs_configurations_generator(
    compose_inputs: dict, expected_odcs_composes_configs: ODCSComposesConfigs
) -> None:
    """test ODCSConfigurationsGenerator.__call__"""
    odcs_config_gen = ODCSConfigurationsGenerator(compose_inputs)
    odcs_composes_configs = odcs_config_gen()
    assert isinstance(odcs_composes_configs, ODCSComposesConfigs)
    assert len(odcs_composes_configs.configs) == len(
        expected_odcs_composes_configs.configs
    )
    for actual_composes, expected_composes in zip(
        odcs_composes_configs.configs, expected_odcs_composes_configs.configs
    ):
        assert actual_composes.spec.source == expected_composes.spec.source
        assert isinstance(actual_composes.spec, type(expected_composes.spec))
        assert actual_composes.additional_args == expected_composes.additional_args
