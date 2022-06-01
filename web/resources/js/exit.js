function exit(choice) {
    let url_to_sending = document.URL;
    let xhr = new XMLHttpRequest();

    xhr.open("POST", url_to_sending, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    let data = JSON.stringify({
        "choice": choice
    });
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            window.location.href = xhr.responseURL
        }
    }
    xhr.send(data);
}