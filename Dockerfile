FROM registry.access.redhat.com/ubi9/python-311:9.5-1741002173

LABEL \
    description="Tools for Red Hat AppStudio" \
    io.k8s.description="Tools for Red Hat AppStudio" \
    io.k8s.display-name="Tools for Red Hat AppStudio" \
    io.openshift.tags="appstudio" \
    summary="This image contains various tools that are used within Red Hat \
AppStudio. The included tools are, for the most part, written in Python."

ENV \
    ENABLE_PIPENV=true \
    PIN_PIPENV_VERSION=2023.11.15 \
    REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem

USER 0
ADD . /tmp/src
ADD --chown=root:root --chmod=644 data/ca-trust/* /etc/pki/ca-trust/source/anchors
RUN /usr/bin/fix-permissions /tmp/src \
    && /usr/bin/update-ca-trust
RUN yum install -y krb5-workstation skopeo
RUN curl -L https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
RUN wget https://github.com/mikefarah/yq/releases/download/v4.45.1/yq_linux_amd64.tar.gz -O - |\
    tar xz && mv yq_linux_amd64 /usr/bin/yq
COPY data/kerberos/krb5.conf /etc

USER 1001

RUN \
    curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.12.36/openshift-client-linux.tar.gz \
    | tar -C /opt/app-root/bin/ -xvzf - oc \
    && /usr/libexec/s2i/assemble
