#!/usr/bin/env python3

"""Clean spacerequests"""

import datetime
from types import ModuleType
from typing import Callable

import click
from kubernetes import client, config  # type: ignore

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_config(conf: ModuleType) -> None:
    """Load configs from cluster or pod"""
    try:
        conf.load_incluster_config()
    except conf.ConfigException:
        conf.load_kube_config()


def get_tenant_namespaces(lister: Callable) -> list[str]:
    """Get names of all tenant namespaces"""
    return [
        item.metadata.name
        for item in lister(
            label_selector="toolchain.dev.openshift.com/type=tenant"
        ).items
    ]


def get_old_namespace_requests(
    lister: Callable, namespace: str, time_threshold: datetime.datetime
) -> list[str]:
    """Get all old spacerequest for a given namespace"""
    return [
        req["metadata"]["name"]
        for req in lister(
            group="toolchain.dev.openshift.com",
            version="v1alpha1",
            namespace=namespace,
            plural="spacerequests",
        )["items"]
        if datetime.datetime.strptime(req["metadata"]["creationTimestamp"], TIME_FORMAT)
        < time_threshold
    ]


def delete_namespace_requests(
    deleter: Callable, namespace: str, requests: list[str]
) -> None:
    """Delete namespace spacerequests"""
    for req in requests:
        try:
            deleter(
                group="toolchain.dev.openshift.com",
                version="v1alpha1",
                namespace=namespace,
                plural="spacerequests",
                name=req,
            )
            print(f"Deleted spacerequest {req}")
        except client.ApiException as e:
            print(f"Failed deleting spacerequest {req}: {e}")


@click.command()
@click.option(
    "--hours-to-keep",
    help="Threshold in hours after which space requests will be deleted",
    type=int,
    default=4,
    envvar="HOURS_TO_KEEP",
)
def main(hours_to_keep: int) -> None:
    """Clean old space requests"""
    load_config(config)

    tenant_ns = get_tenant_namespaces(client.CoreV1Api().list_namespace)

    for ns in tenant_ns:
        print(f"Processing namespace: {ns}")
        old_reqs = get_old_namespace_requests(
            client.CustomObjectsApi().list_namespaced_custom_object,
            ns,
            datetime.datetime.utcnow() - datetime.timedelta(hours=hours_to_keep),
        )

        print(f"Old Reqs: {old_reqs}")

        delete_namespace_requests(
            client.CustomObjectsApi().delete_namespaced_custom_object, ns, old_reqs
        )


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
