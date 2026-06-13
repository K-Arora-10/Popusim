export function connectSimulationWS(simulationId, onMessage, onError, onClose) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // If we are on Vite dev server port 5173, point to backend on port 8000
  const host = window.location.host.includes('5173') ? 'localhost:8000' : window.location.host;
  const wsUrl = `${protocol}//${host}/ws/simulation/${simulationId}`;
  
  console.log(`Connecting to WebSocket: ${wsUrl}`);
  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message content:', e);
    }
  };

  socket.onerror = (error) => {
    if (onError) onError(error);
  };

  socket.onclose = (event) => {
    if (onClose) onClose(event);
  };

  // Heartbeat ping-pong to keep connection alive in long simulations
  const pingInterval = setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send('ping');
    }
  }, 15000);

  return () => {
    clearInterval(pingInterval);
    if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
      socket.close();
    }
  };
}
