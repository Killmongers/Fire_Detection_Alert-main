document.addEventListener('DOMContentLoaded', function() {
    fetchCameras();
});

function fetchCameras() {
    fetch('/get_cameras')
        .then(response => response.json())
        .then(data => {
            data.forEach(camera => {
                addCameraToList(camera._id, camera.name);
                addCameraFeed(camera._id, camera.name);
            });
        })
        .catch(error => console.error('Error:', error));
}

function addCameraToList(cameraId, name) {
    const cameraList = document.getElementById('camera-list');
    const listItem = document.createElement('li');
    listItem.innerHTML = `
        <a href="#" onclick="showFeed('${cameraId}')">${name}</a>
        <button class="btn btn-danger btn-sm ml-2" onclick="removeCamera('${cameraId}')">Remove</button>
    `;
    cameraList.appendChild(listItem);
}

function addCameraFeed(cameraId, name) {
    const cameraFeedContainer = document.getElementById('camera-feed-container');
    const cameraDiv = document.createElement('div');
    cameraDiv.id = `feed-${cameraId}`;
    cameraDiv.className = 'camera-feed';
    cameraDiv.innerHTML = `
        <h3>${name}</h3>
        <img src="/video_feed/${cameraId}" alt="Camera ${cameraId}">
    `;
    cameraFeedContainer.appendChild(cameraDiv);
    cameraDiv.style.display = 'none'; // Initially hide the feed
}

function showFeed(cameraId) {
    const allFeeds = document.querySelectorAll('.camera-feed');
    allFeeds.forEach(feed => {
        feed.style.display = 'none';
    });
    document.getElementById(`feed-${cameraId}`).style.display = 'block';
}

document.getElementById('show-form-btn').addEventListener('click', function() {
    $('#camera-modal').modal('show');
});

document.getElementById('camera-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const ipAddress = document.getElementById('ip_address').value;

    fetch('/add_camera', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'name': name,
            'ip_address': ipAddress
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Camera added successfully') {
            addCameraToList(data.camera_id, name);
            addCameraFeed(data.camera_id, name);
            $('#camera-modal').modal('hide');
        } else {
            showFormFeedback(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFormFeedback('Error adding camera');
    });
});

function showFormFeedback(message) {
    const feedback = document.getElementById('form-feedback');
    feedback.textContent = message;
    feedback.className = 'alert alert-danger';
}

function removeCamera(cameraId) {
    fetch(`/remove_camera/${cameraId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Camera removed successfully') {
            document.querySelector(`#camera-list li:has(button[onclick*="${cameraId}"])`).remove();
            document.getElementById(`feed-${cameraId}`).remove();
        } else {
            console.error('Error:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}