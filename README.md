# bitbake-hashserver-web-ui

A Flask Based WebUI front-end for managing the bitbake Hash Equivalence Server

## Authentication

This UI service doesn't implement any sort of authentication by itself.
Instead, it relies on a reverse proxy front-end implementing an authenticate
mechanism to authenticate users with whatever site authentication mechanism is
desired (e.g. Oauth2-proxy, LDAP, HTTP Basic auth, etc.). The reverse proxy
should then pass the name of the authenticated user to this application in a
HTTP header (see `HSUI_USERNAME_HEADER`). This application will then use its
admin user to impersonate the user when interacting with the hash equivalence
server.

This method is chosen so that users can self-administer their own hashserver
accounts. This allows users to reset their hashserver login token without
needing to know the existing token, because they access this UI using their
external credentials (e.g. LDAP, etc.)

Similarly, hashserver administrators can access the admin UI using their
external credentials (e.g. LDAP, etc.) instead of needing to know their
hashserver token.

## Configuration

The server is configured using a series of environment variable:

| Variable                      | Description                                   |
|-------------------------------|-----------------------------------------------|
| `HSUI_BITBAKE_PATH`           | The patch to bitbake. Defaults to `/usr/share/bitbake-hashserver` |
| `HSUI_HASHSERVER_ADDRESS`     | The address of the hash equivalence server |
| `HSUI_HASHSERVER_USER`        | The username to use when connecting to the hash equivalence server. Must have `@user-admin` permissions |
| `HSUI_HASHSERVER_PASSWORD`    | The password to use when connecting to the hash equivalence server |
| `HSUI_SELF_REGISTER_ENABLED`  | If set to `1` or `true`, authenticated users will be able to create their own user accounts in the server. The users permissions will default to `HSUI_DEFAULT_PERMS`. Defaults to `false` |
| `HSUI_DEFAULT_PERMS`          | A space separated list of default permissions to give to users who self register. If you want to give users no permissions by default, use `@none` |
| `HSUI_ADMIN_CONTACT`          | _(optional)_ The email address of the server administrator |
| `HSUI_USERNAME_HEADER`        | The HTTP header that contains the authenticated users username |

**The following variables are only for testing purpose and should not be used in production**

| Variable                      | Description                                   |
|-------------------------------|-----------------------------------------------|
| `HSUI_HOST`                   | The host to bind to when running the application in [development mode][devmode]. Defaults to `127.0.0.1` |
| `HSUI_PORT`                   | The port to bind to when running the application in [development mode][devmode]. Defaults to `8000` |
| `HSUI_TEST_USER`              | The username to use if no username header is specified in the HTTP request. This is useful for testing the server without a reverse-proxy front end but **should not** ever be set in production! |

## Examples

### nginx and Oauth2-proxy on Kubernetes

This provides an example for how to use Oauth2-proxy to authenticate users for
this service.

First, make sure that your Oauth2-proxy is passed the `--set-xauthrequest=true`
argument when it starts up so that it provides the headers to identify the
authenticated users.

Once this is done, the ingress for this Web UI service might look like:

```yaml
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webui
  annotations:
    # Authenticate users against oauth2
    nginx.ingress.kubernetes.io/auth-signin: 'https://$host/oauth2/start?rd=$escaped_request_uri'
    nginx.ingress.kubernetes.io/auth-url: 'https://$host/oauth2/auth'

    # Ensure oauth2 user headers are passed to the application
    nginx.ingress.kubernetes.io/auth-response-headers: X-Auth-Request-User,X-Auth-Request-Groups,X-Auth-Request-Email,X-Auth-Request-Preferred-Username
spec:
  rules:
    - host: hashserver.your.domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: webui
                port:
                  name: http
```

Finally, you'll need to configure this web UI service to read the authenticate
username out of the HTTP headers. Depending on the configuration of the
Oauth2-proxy and how you want user accounts to be identified in the hash
equivalence server, you'll need to pass one of the following environment
variable values to the service:

* `HSUI_USERNAME_HEADER=X-Auth-Request-User`
* `HSUI_USERNAME_HEADER=X-Auth-Request-Preferred-Username`
* `HSUI_USERNAME_HEADER=X-Auth-Request-Email`

[devmode]: https://flask.palletsprojects.com/en/latest/server/
