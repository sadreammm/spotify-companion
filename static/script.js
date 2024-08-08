document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.songs').forEach(function (element) {
        element.addEventListener('click', function () {
            var trackId = this.getAttribute('data-track-id');
            window.location.href = '/song/' + trackId;
        });
    });

    document.querySelectorAll('.playlist').forEach(function (element) {
        element.addEventListener('click', function () {
            var playlistId = this.getAttribute('data-track-id');
            window.location.href = '/playlist/' + playlistId;
        });
    });

    var modal = document.getElementById("myModal");
    var confirmModal = document.getElementById("confirmModal");
    var span = document.getElementsByClassName("close");
    var notification = document.getElementById('notification');

    document.querySelectorAll('.addToPlaylistBtn').forEach(function (btn) {
        btn.addEventListener('click', function (event) {
            event.stopPropagation();
            var trackUri = this.getAttribute('data-track-uri');
            document.getElementById('trackUriInput').value = trackUri;
            modal.style.display = "block";
        });
    });

    for (let i = 0; i < span.length; i++) {
        span[i].onclick = function () {
            modal.style.display = "none";
            confirmModal.style.display = "none";
        };
    }

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        } else if (event.target == confirmModal) {
            confirmModal.style.display = "none";
        }
    };

    var addPlaylistForm = document.getElementById("addPlaylistForm");
    addPlaylistForm.onsubmit = function (event) {
        event.preventDefault();
        var formData = new FormData(addPlaylistForm);
        fetch('/add-playlist', {
            method: 'POST',
            body: formData
        }).then(response => response.json()).then(data => {
            if (data.exists) {
                modal.style.display = "none";
                confirmModal.style.display = "block";
                document.querySelector("#confirmAddTrack input[name='track_uri']").value = data.track_uri;
                document.querySelector("#confirmAddTrack input[name='playlist_id']").value = data.playlist_id;
            } else {
                showNotification("Added to playlist");
                modal.style.display = "none";
                setTimeout(function () {
                    location.reload();
                }, 1000);
            }
        });
    };

    var cancelBtn = document.getElementById('cancelBtn');
    cancelBtn.onclick = function () {
        confirmModal.style.display = "none";
    };

    var confirmPlaylistForm = document.getElementById("confirmAddTrack");
    confirmPlaylistForm.onsubmit = function(event){
        event.preventDefault();
        var formData = new FormData(confirmPlaylistForm);
        fetch('/confirm-add', {
            method: 'POST',
            body: formData
        }).then(response => response.json()).then(data => {
            showNotification("Added to playlist");
            confirmModal.style.display = "none";
            setTimeout(function () {
                location.reload();
            }, 1000);
        });
    };

    function showNotification(message) {
        notification.innerText = message;
        notification.style.display = "block";
        setTimeout(function () {
            notification.style.display = "none";
        }, 6000);
    }
});
