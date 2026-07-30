class WafWebSocketManager {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.statusListeners = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 10000;
    this.isConnected = false;
  }

  getUrl() {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      if (window.location.port === '5173') {
        return `${protocol}//${window.location.host}/dashboard/ws`;
      }
    }
    return 'ws://127.0.0.1:8001/dashboard/ws';
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this._notifyStatus('connecting');

    try {
      this.ws = new WebSocket(this.getUrl());

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this._notifyStatus('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((callback) => callback(data));
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this._notifyStatus('disconnected');
        this._scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.warn('WebSocket encountered error:', error);
        this.ws?.close();
      };
    } catch (err) {
      this.isConnected = false;
      this._notifyStatus('error');
      this._scheduleReconnect();
    }
  }

  _scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
    callback(this.isConnected ? 'connected' : 'disconnected');
    return () => this.statusListeners.delete(callback);
  }

  _notifyStatus(status) {
    this.statusListeners.forEach((callback) => callback(status));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsManager = new WafWebSocketManager();
export default wsManager;
