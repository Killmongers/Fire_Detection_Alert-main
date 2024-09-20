document.addEventListener('DOMContentLoaded', function() {
    fetchCameras();
    fetchAlerts();
});
function fetchAlerts() {
    fetch('/get_alerts')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            data.forEach(alert => {
                addAlertToTop(alert._id, alert.timestamp, alert.message, alert.camera_name);
            });
        })
        .catch(error => console.error('Error fetching alerts:', error));
}

function addAlertToTop(alertId, timestamp, message, cameraName) {
    const alertList = document.getElementById('alert-list');
    const listItem = document.createElement('li');
    listItem.innerHTML = `
        <span>${timestamp}: ${message} (Camera: ${cameraName})</span>
        <button class="btn btn-danger btn-sm ml-2" onclick="removeAlert('${alertId}')">Remove</button>
    `;
    alertList.insertBefore(listItem, alertList.firstChild); // Insert at the top

    // Limit to 5 alerts
    while (alertList.children.length > 5) {
        alertList.removeChild(alertList.lastChild);
    }
}

function removeAlert(alertId) {
    fetch(`/remove_alert/${alertId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Alert removed successfully') {
            document.querySelector(`#alert-list li:has(button[onclick*="${alertId}"])`).remove();
        } else {
            console.error('Error:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

function triggerAlert(cameraId) {
    // Assuming `currentUser` is available globally and contains the user's session data
    fetch('/send-alert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            camera_name: getCameraName(cameraId).trim(),  // Trim the camera name
            camera_id: cameraId,                  
            user_id: currentUser.userId,           
            email: currentUser.email               
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Alert added') {
            console.log('Alert successfully added:', data.alert_id);
        } else {
            console.error('Failed to trigger fire alert. Status code:', data.status);
        }
    })
    .catch(error => console.error('Error:', error));
}





function getCameraName(cameraId) {
    return document.querySelector(`#camera-${cameraId}`).getAttribute('data-camera-name');
}

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
        <div class="controls">
            <button onclick="pauseVideo()">Pause</button>
        </div>
    `;
    cameraFeedContainer.appendChild(cameraDiv);
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

function pauseVideo() {
    fetch('/pause')
        .then(response => response.text())
        .then(text => alert(text));
}

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
