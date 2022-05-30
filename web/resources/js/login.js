function sendJSON() {
    let url_to_sending = document.URL;
    let url = document.querySelector('#url');
    let branch = document.querySelector('#branch');
    let path_to_file = document.querySelector('#path_to_file')
    let xhr = new XMLHttpRequest();

    xhr.open("POST", url_to_sending, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    let data = JSON.stringify({
        "url": url.value,
        "branch": branch.value,
        "path_to_file": path_to_file.value
    });
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            window.location.href = "solutions"
        }
    }
    xhr.send(data);
}