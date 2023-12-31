function escapeHTML(unsafeText) {
    let div = document.createElement('div');
    div.innerText = unsafeText;
    return div.innerHTML;
}

function post_request(endpoint, f, data) {
    const req = new XMLHttpRequest();
    req.open("POST", endpoint);
    req.setRequestHeader("Content-Type", "application/json");
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send(JSON.stringify(data));
}

function get_request(endpoint, f) {
    const req = new XMLHttpRequest();
    req.open("GET", endpoint);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

/*
 * Query functions
 */

function db_query(method, taskhash, outhash, f) {
    post_request("api/query", f, {
        "method": method,
        "taskhash": taskhash,
        "outhash": outhash
    });
}

/*
 * User Admin functions
 */
function user_delete(username, f) {
    post_request("api/user-admin/delete", f, {
        "username": username
    });
}

function user_reset_token(username, f) {
    post_request( "api/user-admin/reset", f, {
        "username": username
    });
}

function user_create(username, perms, f) {
    post_request("api/user-admin/new-user", f, {
        "username": username,
        "permissions": perms
    });
}

function user_set_perms(username, perms, f) {
    post_request("api/user-admin/set-perms", f, {
        "username": username,
        "permissions": perms
    });
}

function get_all_users(f) {
    get_request("api/user-admin/all-users", f);
}

/*
 * Database Admin functions
 */
function db_remove_unused_entries(age_seconds, f) {
    post_request("api/db/remove-unused", f, {
        "age-seconds": age_seconds
    });
}

function db_remove_entries(where, f) {
    post_request("api/db/remove", f, {
        "where": where
    });
}

function db_get_usage(f) {
    get_request("api/db/usage", f);
}

/*
 * Stats Admin functions
 */
function stats_reset(f) {
    post_request("api/reset-stats", f, null);
}

function update_dismiss_button() {
    const dismissButton = document.getElementById("dismissAllAlerts");
    const alertList = document.querySelectorAll(".alert");
    dismissButton.hidden = (alertList.length <= 1);
}

function live_alert(type, message) {
    const alertPlaceholder = document.getElementById("liveAlertPlaceholder");
    let div = document.createElement("div");
    div.classList.add("alert");
    div.classList.add(`alert-${type}`);
    div.classList.add("alert-dismissible");
    div.setAttribute("role", "alert");
    div.innerHTML = [
        `<div>${message}</div>`,
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    ].join("")
    alertPlaceholder.prepend(div);

    div.addEventListener("closed.bs.alert", update_dismiss_button);

    update_dismiss_button();
}

function dismiss_all_alerts() {
    const alertList = document.querySelectorAll(".alert");
    alertList.forEach(function (alert) {
        let a = new bootstrap.Alert(alert);
        a.close();
    });

    update_dismiss_button();
}

/*
 * Event helpers
 */
function on_confirm_dialog_show(event) {
    const button = event.relatedTarget;
    const dialog = event.target;

    const username = button.getAttribute("data-bs-username");

    let e = dialog.querySelector("#username");
    if (e) {
        e.textContent = username;
    }

    dialog.querySelector("#confirm-button").setAttribute("data-bs-username", username);
}
