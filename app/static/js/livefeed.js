document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.getElementById('addButton');
    const modal = document.getElementById('cameraModal');
    const closeModal = document.querySelector('.modal .close');
    const saveButton = document.getElementById('saveCamera');
    const list = document.getElementById('list');
    const mediaPlayerContainer = document.getElementById('mediaPlayerContainer');
    
    // Array to keep track of added cameras
    let cameras = [];

    addButton.addEventListener('click', function() {
        modal.style.display = 'block';
    });

    closeModal.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    saveButton.addEventListener('click', function() {
        const cameraName = document.getElementById('cameraName').value.trim();
        const cameraIP = document.getElementById('cameraIP').value.trim();

        // Validate input fields
        if (cameraName === '' || cameraIP === '') {
            alert('Please enter both camera name and IP address.');
            return;
        }

        // Check if the camera name and IP address already exist
        if (cameras.some(camera => camera.name === cameraName || camera.ip === cameraIP)) {
            alert('Camera name or IP address already exists.');
            return;
        }

        // Validate IP address format
        if (!isValidIP(cameraIP)) {
            alert('Invalid IP address format. Must be a valid IPv4 address.');
            return;
        }

        // Check if IP address starts with "192.168."
        if (!cameraIP.startsWith('192.168.')) {
            alert('IP address must start with "192.168."');
            return;
        }

        // Add new camera to the list and the array
        const newItem = document.createElement('li');
        newItem.textContent = `${cameraName} - ${cameraIP}`;
        newItem.dataset.ip = cameraIP; // Store IP address in data attribute
        list.appendChild(newItem);

        // Save camera to the array
        cameras.push({ name: cameraName, ip: cameraIP });

        // Clear input fields and close modal
        document.getElementById('cameraName').value = '';
        document.getElementById('cameraIP').value = '';
        modal.style.display = 'none';

        // Add media player for the new camera
        addMediaPlayer(cameraIP);
    });

    // Function to validate IPv4 address
    function isValidIP(ip) {
        const ipRegex = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }

    // Function to simulate loading video from the camera
    function loadCameraFeed(ip, videoElement) {
        // Simulate a video feed by setting the video source
        videoElement.src = `http://${ip}/video_feed`; // Placeholder URL
        videoElement.play();
    }

    // Function to create and add a new media player
    function addMediaPlayer(ip) {
        // Create media player container
        const mediaPlayer = document.createElement('div');
        mediaPlayer.className = 'mediaPlayer';
        
        // Create video element
        const video = document.createElement('video');
        video.controls = true;
        mediaPlayer.appendChild(video);

        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'close-media';
        closeButton.textContent = 'Close';
        mediaPlayer.appendChild(closeButton);

        // Load video feed
        loadCameraFeed(ip, video);

        // Add media player to container
        mediaPlayerContainer.appendChild(mediaPlayer);

        // Close button functionality
        closeButton.addEventListener('click', function() {
            // Stop the video feed and remove the media player
            video.pause();
            video.src = ''; // Stop the video feed
            mediaPlayerContainer.removeChild(mediaPlayer);
            
            // Remove camera from the list and array
            const itemToRemove = Array.from(list.children).find(item => item.dataset.ip === ip);
            if (itemToRemove) {
                list.removeChild(itemToRemove);
            }
            cameras = cameras.filter(camera => camera.ip !== ip);
        });
    }

    // Event delegation to handle clicks on list items
    list.addEventListener('click', function(event) {
        if (event.target.tagName === 'LI') {
            const selectedIP = event.target.dataset.ip;
            if (selectedIP) {
                // Check if media player already exists for this camera
                if (!Array.from(mediaPlayerContainer.children).some(mediaPlayer => mediaPlayer.querySelector('video').src.includes(selectedIP))) {
                    addMediaPlayer(selectedIP);
                }
            }
        }
    });
});
