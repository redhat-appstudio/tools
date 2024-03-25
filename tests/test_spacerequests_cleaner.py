"""Test spacerequests_cleaner.py"""

import datetime
from unittest.mock import MagicMock, call, create_autospec

import pytest
from kubernetes import client, config  # type: ignore
from pytest import MonkeyPatch

from clean_spacerequests import spacerequests_cleaner
from clean_spacerequests.spacerequests_cleaner import (
    TIME_FORMAT,
    delete_namespace_requests,
    get_old_namespace_requests,
    get_tenant_namespaces,
    load_config,
)

# pylint: disable=too-few-public-methods


class TestLoadConfig:
    """Test load_config"""

    def test_load_config_from_cluster(self) -> None:
        """Test load config as if running inside a pod"""
        conf: MagicMock = create_autospec(config)
        load_config(conf)
        conf.load_incluster_config.assert_called_once_with()
        conf.load_kube_config.assert_not_called()

    def test_load_config_from_kube_config(self) -> None:
        """Test load config as if running outside of the cluster"""
        conf: MagicMock = create_autospec(config)
        conf.ConfigException = config.ConfigException
        conf.load_incluster_config.side_effect = config.ConfigException
        load_config(conf)
        conf.load_incluster_config.assert_called_once_with()
        conf.load_kube_config.assert_called_once_with()


def get_mock_with_name_attribute(name: str) -> MagicMock:
    """Since name is an argument to the Mock constructor, if we want mock object with
    name attribute, we need to set it after the mock has been created"""
    mock = MagicMock()
    mock.name = name
    return mock


class TestGetTenantNamespaces:
    """Test get_tenant_namespaces"""

    @pytest.mark.parametrize(
        ("namespaces", "tenant_namespaces"),
        [
            pytest.param(MagicMock(items=[]), [], id="no namespaces"),
            pytest.param(
                MagicMock(
                    items=[MagicMock(metadata=get_mock_with_name_attribute("foo"))]
                ),
                ["foo"],
                id="one namespace",
            ),
            pytest.param(
                MagicMock(
                    items=[
                        MagicMock(metadata=get_mock_with_name_attribute("foo")),
                        MagicMock(metadata=get_mock_with_name_attribute("bar")),
                    ]
                ),
                ["foo", "bar"],
                id="multiple namespaces",
            ),
        ],
    )
    def test_get_tenant_namespaces(
        self, namespaces: MagicMock, tenant_namespaces: list[str]
    ) -> None:
        """Test getting tenant namespaces"""
        lister = create_autospec(client.CoreV1Api().list_namespace)
        lister.return_value = namespaces
        out = get_tenant_namespaces(lister)
        assert set(out) == set(tenant_namespaces)


THRESHOLD_TIMESTAMP = datetime.datetime(2024, 3, 18, 15, 43, 14, 282530)


class TestGetOldNamespaceRequests:
    """Test get_old_namespace_requests"""

    @pytest.mark.parametrize(
        ("requests", "old_requests"),
        [
            pytest.param({"items": []}, [], id="no requests"),
            pytest.param(
                {
                    "items": [
                        {
                            "metadata": {
                                "name": "old",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP - datetime.timedelta(hours=1)
                                ).strftime(TIME_FORMAT),
                            },
                        }
                    ]
                },
                ["old"],
                id="one old request",
            ),
            pytest.param(
                {
                    "items": [
                        {
                            "metadata": {
                                "name": "old",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP - datetime.timedelta(hours=1)
                                ).strftime(TIME_FORMAT),
                            },
                        },
                        {
                            "metadata": {
                                "name": "new",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP + datetime.timedelta(hours=1)
                                ).strftime(TIME_FORMAT),
                            },
                        },
                    ]
                },
                ["old"],
                id="one old request and one new request",
            ),
            pytest.param(
                {
                    "items": [
                        {
                            "metadata": {
                                "name": "old",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP - datetime.timedelta(hours=1)
                                ).strftime(TIME_FORMAT),
                            },
                        },
                        {
                            "metadata": {
                                "name": "new",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP + datetime.timedelta(hours=1)
                                ).strftime(TIME_FORMAT),
                            },
                        },
                        {
                            "metadata": {
                                "name": "older",
                                "creationTimestamp": (
                                    THRESHOLD_TIMESTAMP - datetime.timedelta(hours=10)
                                ).strftime(TIME_FORMAT),
                            },
                        },
                    ]
                },
                ["old", "older"],
                id="multiple old requests and one new request",
            ),
        ],
    )
    def test_get_old_namespace_requests(
        self, requests: dict, old_requests: list[str]
    ) -> None:
        """Test get_old_namespace_requests"""
        lister = create_autospec(
            client.CustomObjectsApi().list_namespaced_custom_object
        )
        lister.return_value = requests
        threshold = THRESHOLD_TIMESTAMP
        out = get_old_namespace_requests(lister, "some-ns", threshold)
        assert set(out) == set(old_requests)


class TestDeleteNamespaceRequests:
    """Test delete_namespace_requests"""

    @pytest.mark.parametrize(
        ("old_reqs"),
        [
            pytest.param([], id="no requests"),
            pytest.param(["o1"], id="one request"),
            pytest.param(["o1", "o2", "o3"], id="multiple requests"),
        ],
    )
    def test_delete_namespace_requests(self, old_reqs: list[str]) -> None:
        """Test delete_namespace_requests"""
        deleter = create_autospec(
            client.CustomObjectsApi().delete_namespaced_custom_object
        )
        ns = "some-ns"
        delete_namespace_requests(deleter, ns, old_reqs)
        assert deleter.call_count == len(old_reqs)
        for req in old_reqs:
            deleter.assert_any_call(
                group="toolchain.dev.openshift.com",
                version="v1alpha1",
                namespace=ns,
                plural="spacerequests",
                name=req,
            )

    def test_delete_namespace_requests_endures_expected_exception(self) -> None:
        """Test delete_namespace_requests does not fail when failing to delete"""
        deleter = create_autospec(
            client.CustomObjectsApi().delete_namespaced_custom_object
        )
        deleter.side_effect = [None, client.ApiException("oh no"), None]
        ns = "some-ns"
        reqs = ["o1", "o2", "o3"]
        delete_namespace_requests(deleter, ns, reqs)
        assert deleter.call_count == len(reqs)

    def test_delete_namespace_requests_crashes_on_unexpected_exception(self) -> None:
        """Test delete_namespace_requests fails on any other exception"""
        deleter = create_autospec(
            client.CustomObjectsApi().delete_namespaced_custom_object
        )
        deleter.side_effect = [None, Exception, None]
        ns = "some-ns"
        reqs = ["o1", "o2", "o3"]
        with pytest.raises(Exception):
            delete_namespace_requests(deleter, ns, reqs)


class TestMain:
    """Test main"""

    @pytest.fixture()
    def load_config_mock(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkeypatch load_config_mock"""
        mock = create_autospec(load_config)
        monkeypatch.setattr(spacerequests_cleaner, load_config.__name__, mock)
        return mock

    @pytest.fixture()
    def get_tenant_namespaces_mock(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkeypatch get_tenant_namespaces_mock"""
        mock = create_autospec(get_tenant_namespaces)
        monkeypatch.setattr(spacerequests_cleaner, get_tenant_namespaces.__name__, mock)
        return mock

    @pytest.fixture()
    def get_old_namespace_requests_mock(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkeypatch get_old_namespace_requests_mock"""
        mock = create_autospec(get_old_namespace_requests)
        monkeypatch.setattr(
            spacerequests_cleaner, get_old_namespace_requests.__name__, mock
        )
        return mock

    @pytest.fixture()
    def delete_namespace_requests_mock(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkeypatch delete_namespace_requests_mock"""
        mock = create_autospec(delete_namespace_requests)
        monkeypatch.setattr(
            spacerequests_cleaner, delete_namespace_requests.__name__, mock
        )
        return mock

    @pytest.fixture()
    def client_mock(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkeypatch client"""
        mock = create_autospec(client)
        monkeypatch.setattr(spacerequests_cleaner, "client", mock)
        return mock

    def test_main(  # pylint: disable=too-many-arguments
        self,
        load_config_mock: MagicMock,
        get_tenant_namespaces_mock: MagicMock,
        get_old_namespace_requests_mock: MagicMock,
        delete_namespace_requests_mock: MagicMock,
        client_mock: MagicMock,
    ) -> None:
        """Test main"""
        get_tenant_namespaces_mock.return_value = ["ns1", "ns2"]
        get_old_namespace_requests_mock.return_value = ["o1", "o2"]
        spacerequests_cleaner.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--hours-to-keep",
                "2",
            ],
            obj={},
            standalone_mode=False,
        )

        load_config_mock.assert_called_once_with(config)
        assert delete_namespace_requests_mock.call_args_list == [
            call(
                client_mock.CustomObjectsApi().delete_namespaced_custom_object,
                "ns1",
                ["o1", "o2"],
            ),
            call(
                client_mock.CustomObjectsApi().delete_namespaced_custom_object,
                "ns2",
                ["o1", "o2"],
            ),
        ]
