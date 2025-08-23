/**
 * Example JavaScript client for real-time streaming functionality.
 * 
 * This demonstrates how to:
 * - Connect to SSE endpoints for job progress
 * - Handle different event types
 * - Manage connection lifecycle
 * - Implement reconnection logic
 */

class StreamingClient {
    constructor(baseUrl, authToken) {
        this.baseUrl = baseUrl;
        this.authToken = authToken;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.listeners = new Map();
    }

    /**
     * Connect to job progress stream
     */
    connectToJobStream(jobId) {
        const url = `${this.baseUrl}/v1/streaming/jobs/${jobId}/stream`;
        this.connect(url, `job-${jobId}`);
    }

    /**
     * Connect to user updates stream
     */
    connectToUserStream() {
        const url = `${this.baseUrl}/v1/streaming/user/stream`;
        this.connect(url, 'user-updates');
    }

    /**
     * Generic connection method
     */
    connect(url, streamId) {
        try {
            // Close existing connection
            this.disconnect();

            console.log(`Connecting to stream: ${url}`);

            // Create EventSource with auth headers
            this.eventSource = new EventSource(url, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            // Connection opened
            this.eventSource.onopen = (event) => {
                console.log(`✅ Connected to ${streamId} stream`);
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.emit('connected', { streamId });
            };

            // Handle messages
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log(`📨 Message received:`, data);
                    this.emit('message', data);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            };

            // Handle job updates
            this.eventSource.addEventListener('job_update', (event) => {
                try {
                    const jobData = JSON.parse(event.data);
                    console.log(`🔄 Job update:`, jobData);
                    this.emit('job_update', jobData);
                    
                    // Emit specific progress events
                    if (jobData.progress_percentage !== undefined) {
                        this.emit('progress', {
                            jobId: jobData.id,
                            progress: jobData.progress_percentage,
                            stage: jobData.current_stage,
                            status: jobData.status
                        });
                    }
                } catch (error) {
                    console.error('Failed to parse job update:', error);
                }
            });

            // Handle system messages
            this.eventSource.addEventListener('system_message', (event) => {
                try {
                    const messageData = JSON.parse(event.data);
                    console.log(`📢 System message:`, messageData);
                    this.emit('system_message', messageData);
                } catch (error) {
                    console.error('Failed to parse system message:', error);
                }
            });

            // Handle ping/keepalive
            this.eventSource.addEventListener('ping', (event) => {
                console.log('🏓 Ping received');
                this.emit('ping');
            });

            // Handle errors
            this.eventSource.onerror = (event) => {
                console.error(`❌ Stream error for ${streamId}:`, event);
                this.emit('error', { streamId, event });
                
                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect(url, streamId);
                } else {
                    console.error(`Max reconnection attempts reached for ${streamId}`);
                    this.emit('max_reconnect_attempts', { streamId });
                }
            };

        } catch (error) {
            console.error('Failed to connect to stream:', error);
            this.emit('connection_error', { streamId, error });
        }
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect(url, streamId) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Reconnecting to ${streamId} in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(url, streamId);
        }, delay);
    }

    /**
     * Disconnect from stream
     */
    disconnect() {
        if (this.eventSource) {
            console.log('🔌 Disconnecting from stream');
            this.eventSource.close();
            this.eventSource = null;
            this.emit('disconnected');
        }
    }

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to listeners
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.eventSource && this.eventSource.readyState === EventSource.OPEN;
    }
}

// Usage example
function createStreamingExample() {
    const client = new StreamingClient('http://localhost:8000', 'your-auth-token');

    // Set up event listeners
    client.on('connected', (data) => {
        console.log('🎉 Connected to stream:', data.streamId);
        updateConnectionStatus('Connected');
    });

    client.on('disconnected', () => {
        console.log('👋 Disconnected from stream');
        updateConnectionStatus('Disconnected');
    });

    client.on('job_update', (jobData) => {
        console.log('📊 Job update received:', jobData);
        updateJobProgress(jobData);
    });

    client.on('progress', (progressData) => {
        console.log('📈 Progress update:', progressData);
        updateProgressBar(progressData.progress);
        updateStageIndicator(progressData.stage);
    });

    client.on('system_message', (messageData) => {
        console.log('📢 System message:', messageData);
        showSystemMessage(messageData.message, messageData.type);
    });

    client.on('error', (errorData) => {
        console.error('❌ Stream error:', errorData);
        updateConnectionStatus('Error');
    });

    return client;
}

// Helper functions for UI updates (implement based on your UI framework)
function updateConnectionStatus(status) {
    console.log(`Connection status: ${status}`);
    // Update UI connection indicator
}

function updateJobProgress(jobData) {
    console.log(`Job ${jobData.id}: ${jobData.status} - ${jobData.progress_percentage}%`);
    // Update job progress in UI
}

function updateProgressBar(progress) {
    console.log(`Progress: ${progress}%`);
    // Update progress bar element
}

function updateStageIndicator(stage) {
    console.log(`Current stage: ${stage}`);
    // Update stage indicator in UI
}

function showSystemMessage(message, type) {
    console.log(`System ${type}: ${message}`);
    // Show system message in UI (toast, notification, etc.)
}

// Example usage
const streamingClient = createStreamingExample();

// Connect to user stream for all job updates
streamingClient.connectToUserStream();

// Or connect to specific job stream
// streamingClient.connectToJobStream('job-id-here');

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    streamingClient.disconnect();
});

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamingClient;
}