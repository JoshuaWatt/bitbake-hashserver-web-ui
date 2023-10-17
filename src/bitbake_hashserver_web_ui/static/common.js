
/*
 * User Admin functions
 */
function user_delete(username, f) {
    const req = new XMLHttpRequest();
    req.open("GET", `api/user-admin/delete?username=${encodeURIComponent(username)}`);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

function user_reset_token(username, f) {
    const req = new XMLHttpRequest();
    req.open("GET", `api/user-admin/reset?username=${encodeURIComponent(username)}`);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

function user_create(username, perms, f) {
    const perms_str = perms.join(",");
    const req = new XMLHttpRequest();
    req.open("GET", `api/user-admin/new-user?username=${encodeURIComponent(username)}&permissions=${encodeURIComponent(perms_str)}`);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

function user_set_perms(username, perms, f) {
    const perms_str = perms.join(",");
    const req = new XMLHttpRequest();
    req.open("GET", `api/user-admin/set-perms?username=${encodeURIComponent(username)}&permissions=${encodeURIComponent(perms_str)}`);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

/*
 * Database Admin functions
 */
function db_remove_unused_entries(f) {
    const req = new XMLHttpRequest();
    const seconds = parseInt(document.getElementById("unused-age").value) * parseInt(document.getElementById("unused-age-scale").value);
    req.open("GET", `api/db/remove-unused?age-seconds=${encodeURIComponent(seconds)}`);
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

function db_remove_entries(where, f) {
    let query = [];

    for (const key of Object.keys(where)) {
        query.push(encodeURIComponent(key) + "=" + encodeURIComponent(where[key]));
    }

    if (query.length == 0) {
        return;
    }

    const req = new XMLHttpRequest();
    req.open("GET", "api/db/remove?" + query.join("&"));
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}

/*
 * Stats Admin functions
 */
function stats_reset(f) {
    const req = new XMLHttpRequest();
    req.open("GET", "api/reset-stats");
    req.addEventListener("load", function () {
        const data = JSON.parse(req.responseText);
        f(data);
    })
    req.send();
}
