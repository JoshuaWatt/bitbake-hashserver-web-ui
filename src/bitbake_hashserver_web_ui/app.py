#! /usr/bin/env python3
#
#   Copyright 2023 Garmin Ltd. or its subsidiaries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys
import os
import contextlib
from functools import wraps
import flask
from flask import Flask, request, render_template

app = Flask(__name__)
app.config.from_prefixed_env("HSUI")

# The path to bitbake
BITBAKE_PATH = app.config.get("BITBAKE_PATH", "/usr/share/bitbake-hashserver")

sys.path.insert(0, f"{BITBAKE_PATH}/lib")

import hashserv
import hashserv.server
import bb.asyncrpc

# Optional host where the application should bind
HOST = app.config.get("HOST", "127.0.0.1")

# Optional port where the application should bind
PORT = int(app.config.get("PORT", 8000))

# The address to use to connect to the hash equivalence server
HASHSERVER_ADDRESS = app.config["HASHSERVER_ADDRESS"]

# The user this application should use to authenticate with the hash
# equivalence server. This user must have "@user-admin" permissions
HASHSERVER_USER = app.config["HASHSERVER_USER"]

# The password (or token) that this user should use to authenticate with the
# hash equivalence server
HASHSERVER_PASSWORD = app.config["HASHSERVER_PASSWORD"]

# The default permissions that should be assigned to users when they self
# register, as a space separated list. "@read" or "@none" is recommended
DEFAULT_PERMS = app.config["DEFAULT_PERMS"].split()

# Optional boolean that indicates if authenticated users are allowed to
# register their own user accounts. If enabled, the account will be given the
# DEFAULT_PERMS permissions when created
SELF_REGISTER_ENABLED = app.config.get("SELF_REGISTER_ENABLED", 0) in (1, "true")

# Optional contact information for the server admin. Will be shown to users if
# self-registration is disabled
ADMIN_CONTACT = app.config.get("ADMIN_CONTACT")

# The name of the HTTP header that contains the name of the authenticated user.
# If set, it is expected that a front end authentication mechanism is being
# used to authenticate users, and the name of the user is set in this header.
# For example, if you are using OAuth2-proxy, this should be
# "X-Auth-Request-User"
USERNAME_HEADER = app.config.get("USERNAME_HEADER")


# Optional user to authenticate as if the system cannot otherwise determine the
# user. This is ONLY FOR TESTING as it is highly insecure.
TEST_USER = app.config.get("TEST_USER")


def get_username():
    if USERNAME_HEADER and USERNAME_HEADER in request.headers:
        return request.headers[USERNAME_HEADER]

    if TEST_USER:
        return TEST_USER

    app.logger.error("Unable to determine current user. Headers:\n%s", request.headers)

    return None


def admin_client():
    return hashserv.create_client(
        HASHSERVER_ADDRESS,
        HASHSERVER_USER,
        HASHSERVER_PASSWORD,
    )


@contextlib.contextmanager
def user_client(username):
    with admin_client() as client:
        client.become_user(username)
        yield client


@contextlib.contextmanager
def api_client():
    username = get_username()
    if username is None:
        raise Exception("Unable to determine current user")

    with admin_client() as client:
        client.become_user(username)
        yield client


def error_page(message, detail):
    return render_template("error.html.j2", message=message, detail=detail)


def no_user_error_page():
    return error_page(
        "Unable to determine current user",
        "Server is probably configured incorrectly",
    )


def api(proc):
    @wraps(proc)
    def decorator():
        try:
            with api_client() as client:
                return proc(client)
        except (bb.asyncrpc.InvokeError, bb.asyncrpc.ClientError) as e:
            return {"error": "Unable to complete request: " + str(e)}
        except Exception as e:
            return {"error": str(e)}

    return decorator


def user_page(proc):
    @wraps(proc)
    def decorator():
        username = get_username()
        if username is None:
            return no_user_error_page()

        try:
            return proc(username)
        except (bb.asyncrpc.InvokeError, bb.asyncrpc.ClientError) as e:
            return error_page("Error accessing server", str(e))

    return decorator


@app.route("/")
@user_page
def main(username):
    register = request.args.get("register", "false") == "true"

    with admin_client() as client:
        user = client.get_user(username)

        if user is None:
            if register and SELF_REGISTER_ENABLED:
                try:
                    user = client.new_user(username, DEFAULT_PERMS)
                except (bb.asyncrpc.InvokeError, bb.asyncrpc.ClientError) as e:
                    return error_page(f"Unable to create user {username}", str(e))
            else:
                return render_template(
                    "no-user.html.j2",
                    username=username,
                    self_reg_enabled=SELF_REGISTER_ENABLED,
                    admin_contact=ADMIN_CONTACT,
                )

        return render_template(
            "index.html.j2",
            user=user,
            self_reg_enabled=SELF_REGISTER_ENABLED,
        )


@app.route("/users")
@user_page
def get_users(username):
    with user_client(username) as client:
        return render_template(
            "all-users.html.j2",
            all_perms=sorted(list(hashserv.server.ALL_PERMISSIONS)),
            admin_user=HASHSERVER_USER,
            default_perms=DEFAULT_PERMS,
            user=client.get_user(),
        )


@app.route("/api/user-admin/delete")
@api
def user_admin_delete(client):
    mod_username = request.args.get("username")
    if not mod_username:
        raise Exception("username not specified")

    client.delete_user(mod_username)
    return {"deleted": [mod_username]}


@app.route("/api/user-admin/set-perms")
@api
def user_admin_set_perms(client):
    mod_username = request.args.get("username")
    if not mod_username:
        raise Exception("username not specified")

    permissions = request.args.get("permissions")
    if not permissions:
        raise Exception("permissions not specified")

    return client.set_user_perms(mod_username, permissions.split(","))


@app.route("/api/user-admin/reset")
@api
def user_admin_reset_token(client):
    mod_username = request.args.get("username")
    if not mod_username:
        raise Exception("username not specified")

    return client.refresh_token(mod_username)


@app.route("/api/user-admin/new-user")
@api
def user_admin_new_user(client):
    mod_username = request.args.get("username")
    if not mod_username:
        raise Exception("username not specified")

    permissions = request.args.get("permissions")
    if not permissions:
        raise Exception("permissions not specified")

    return client.new_user(mod_username, permissions.split(","))


@app.route("/api/user-admin/all-users")
@api
def user_admin_all_users(client):
    return {"users": client.get_all_users()}


@app.route("/database")
@user_page
def database(username):
    with user_client(username) as client:
        return render_template(
            "database.html.j2",
            query_columns=sorted(client.get_db_query_columns()),
            user=client.get_user(),
        )


@app.route("/api/db/remove-unused")
@api
def db_remove_unused(client):
    age_seconds = request.args.get("age-seconds")
    if not age_seconds:
        raise Exception("age-seconds not specified")

    try:
        age_seconds = int(age_seconds)
    except TypeError:
        raise Exception("age-seconds is not an integer")

    return client.clean_unused(age_seconds)


@app.route("/api/db/remove")
@api
def db_remove(client):
    return client.remove(request.args)


@app.route("/api/db/usage")
@api
def db_stats(client):
    return {"usage": client.get_db_usage()}


@app.route("/stats")
@user_page
def stats(username):
    with user_client(username) as client:
        user = client.get_user()

        stats = client.get_stats()
        info = []
        columns = set()

        for name in sorted(stats.keys()):
            s = {"name": name}
            for k, v in stats[name].items():
                if isinstance(v, float):
                    v = "{0:.3f}".format(v)
                s[k] = v
                columns.add(k)
            info.append(s)

        return render_template(
            "stats.html.j2",
            info=info,
            columns=sorted(list(columns)),
            user=user,
        )


@app.route("/api/reset-stats")
@api
def reset_stats(client):
    return client.reset_stats()


@app.after_request
def disable_caching(r):
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers[
        "Cache-Control"
    ] = "no-cache, no-store, must-revalidate, public, max-age=0"
    return r


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
