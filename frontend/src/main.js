/**
 * Sentry Frontend - Webcam Video Ingestion
 * Uses getUserMedia to capture webcam and send frames to backend
 */

// Configuration
const API_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8080';
let streamId = null;
let isStreaming = false;
let frameCount = 0;
let detectionCount = 0;
let latencyHistory = [];
let videoStream = null;
let processingInterval = null;

// DOM elements
const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const settingsBtn = document.getElementById('settingsBtn');
const statusEl = document.getElementById('status');
const logsEl = document.getElementById('logs');
const configPanel = document.getElementById('configPanel');
const framesProcessedEl = document.getElementById('framesProcessed');
const detectionsCountEl = document.getElementById('detectionsCount');
const avgLatencyEl = document.getElementById('avgLatency');

// Config inputs
const sampleRateInput = document.getElementById('sampleRate');
const sampleRateValue = document.getElementById('sampleRateValue');
const minConfidenceInput = document.getElementById('minConfidence');
const minConfidenceValue = document.getElementById('minConfidenceValue');
const enableClipsInput = document.getElementById('enableClips');

// Event listeners
startBtn.addEventListener('click', startStreaming);
stopBtn.addEventListener('click', stopStreaming);
settingsBtn.addEventListener('click', toggleSettings);

sampleRateInput.addEventListener('input', (e) => {
    sampleRateValue.textContent = e.target.value;
});

minConfidenceInput.addEventListener('input', (e) => {
    const value = (e.target.value / 100).toFixed(2);
    minConfidenceValue.textContent = value;
});

/**
 * Start webcam streaming and processing
 */
async function startStreaming() {
    try {
        log('Requesting webcam access...');

        // Get webcam stream
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        });

        video.srcObject = videoStream;

        // Wait for video to be ready
        await new Promise(resolve => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });

        // Setup canvas overlay
        overlay.width = video.videoWidth;
        overlay.height = video.videoHeight;

        log('Webcam connected');

        // Start stream session with backend
        const config = {
            stream_id: `stream_${Date.now()}`,
            frame_sample_rate: parseInt(sampleRateInput.value),
            min_confidence: parseFloat(minConfidenceInput.value) / 100,
            enable_clip_recording: enableClipsInput.checked
        };

        const response = await fetch(`${API_URL}/streams`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (!response.ok) throw new Error('Failed to start stream');

        const data = await response.json();
        streamId = data.stream_id;

        log(`Stream started: ${streamId}`);
        updateStatus('streaming', 'Streaming Active');

        isStreaming = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;

        // Start processing frames
        processFrames();

    } catch (error) {
        console.error('Error starting stream:', error);
        log(`ERROR: ${error.message}`, 'error');
        updateStatus('error', `Error: ${error.message}`);
    }
}

/**
 * Stop streaming
 */
async function stopStreaming() {
    try {
        isStreaming = false;

        if (processingInterval) {
            clearInterval(processingInterval);
            processingInterval = null;
        }

        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }

        if (streamId) {
            await fetch(`${API_URL}/streams/${streamId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            log(`Stream stopped: ${streamId}`);
        }

        streamId = null;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        updateStatus('idle', 'Idle');

        // Clear overlay
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);

    } catch (error) {
        console.error('Error stopping stream:', error);
        log(`ERROR: ${error.message}`, 'error');
    }
}

/**
 * Process video frames and send to backend
 */
function processFrames() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    processingInterval = setInterval(async () => {
        if (!isStreaming || !video.videoWidth) return;

        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Convert to base64
        const frameData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

        // Send to backend
        const startTime = Date.now();

        try {
            const response = await fetch(`${API_URL}/streams/${streamId}/frames`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frame_index: frameCount,
                    frame: frameData
                })
            });

            if (!response.ok) throw new Error('Frame processing failed');

            const result = await response.json();
            const latency = Date.now() - startTime;

            frameCount++;

            // Update stats
            if (result.sampled) {
                detectionCount += result.detections?.length || 0;
                latencyHistory.push(latency);
                if (latencyHistory.length > 20) latencyHistory.shift();

                updateStats();

                // Draw detections
                if (result.detections && result.detections.length > 0) {
                    drawDetections(result.detections);
                    log(`Detected ${result.detections.length} object(s)`);
                }
            }

        } catch (error) {
            console.error('Frame processing error:', error);
            log(`Frame error: ${error.message}`, 'error');
        }

    }, 1000 / 10);  // Process at ~10 FPS (server-side sampling will reduce actual processing)
}

/**
 * Draw detection bounding boxes on overlay
 */
function drawDetections(detections) {
    const ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    const scaleX = overlay.width / video.videoWidth;
    const scaleY = overlay.height / video.videoHeight;

    detections.forEach(detection => {
        const [x1, y1, x2, y2] = detection.bounding_box;

        // Scale coordinates
        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const width = (x2 - x1) * scaleX;
        const height = (y2 - y1) * scaleY;

        // Draw box
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(sx1, sy1, width, height);

        // Draw label
        const label = `${detection.class_name} (${(detection.confidence * 100).toFixed(0)}%)`;
        ctx.fillStyle = '#00ff00';
        ctx.fillRect(sx1, sy1 - 25, ctx.measureText(label).width + 10, 25);

        ctx.fillStyle = '#000';
        ctx.font = '16px sans-serif';
        ctx.fillText(label, sx1 + 5, sy1 - 7);
    });
}

/**
 * Update statistics display
 */
function updateStats() {
    framesProcessedEl.textContent = frameCount;
    detectionsCountEl.textContent = detectionCount;

    if (latencyHistory.length > 0) {
        const avgLatency = latencyHistory.reduce((a, b) => a + b, 0) / latencyHistory.length;
        avgLatencyEl.textContent = `${Math.round(avgLatency)}ms`;
    }
}

/**
 * Update status display
 */
function updateStatus(type, message) {
    statusEl.className = `status ${type}`;
    statusEl.textContent = `● ${message}`;
}

/**
 * Toggle settings panel
 */
function toggleSettings() {
    configPanel.style.display = configPanel.style.display === 'none' ? 'block' : 'none';
}

/**
 * Add log entry
 */
function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `[${timestamp}] ${message}`;

    if (type === 'error') {
        entry.style.color = '#fc8181';
    }

    logsEl.appendChild(entry);
    logsEl.scrollTop = logsEl.scrollHeight;

    // Keep only last 50 entries
    while (logsEl.children.length > 50) {
        logsEl.removeChild(logsEl.firstChild);
    }
}

// Initialize
log('[SYSTEM] Frontend initialized');
log(`API URL: ${API_URL}`);
