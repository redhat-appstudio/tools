# Developing this repo

## Python local development prerequisites
* Python 3.11
* pipenv (At least 2022.4.20)
* yum packages: krb5-devel, gcc, python3.11-devel

## Working with the container image

### To build this repo into a container:
```
podman build -t appstudio-tools .
```

### To run the built container and gain an interactive shell:
```
podman run -it --rm appstudio-tools bash
```
Within the container, all the tools will be available in `$PATH`.

### Checking for ODCS connectivity:

You will need to obtain a keytab file with credentials for an account that
can use ODCS. The `odcs_ping` tool can then be used to check the connectivity.
```
podman run -it --rm \
    -e KRB5CCNAME=/tmp/foo \
    -e KRB5_CLIENT_KTNAME=/tmp/kt \
    -v $KT_PATH:/tmp/kt:Z \
    appstudio-tools odcs_ping
```
(Here we assume the path to a local copy of an appropriate keytab file was
stored in the `$KT_PATH` variable).

If everything goes well, the output will resemble the following (Some
parts omitted for brevity):
```
Connected ODCS version 0.7.0.post5+git.2d65205
Signing keys: [...]
Allowed users:
  ...
Allowed groups:
  ...

Attempting to generate a compose
Compose done:
  repo file at: http://.../odcs-1234567.repo
  owner: your-keytab-user-here
```
