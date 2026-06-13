const API_BASE = '/api';

export async function startSimulation(url, numPersonas = 3, useSharedSession = false) {
  const response = await fetch(`${API_BASE}/simulation/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, num_personas: numPersonas, use_shared_session: useSharedSession })
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to start simulation.');
  }
  return response.json();
}

export async function getBootstrapStatus() {
  const response = await fetch(`${API_BASE}/session/bootstrap/status`);
  if (!response.ok) throw new Error('Failed to fetch bootstrap status.');
  return response.json();
}

export async function startBootstrap(url) {
  const response = await fetch(`${API_BASE}/session/bootstrap/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to start browser bootstrap.');
  }
  return response.json();
}

export async function saveBootstrap() {
  const response = await fetch(`${API_BASE}/session/bootstrap/save`, {
    method: 'POST'
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to save session state.');
  }
  return response.json();
}

export async function cancelBootstrap() {
  const response = await fetch(`${API_BASE}/session/bootstrap/cancel`, {
    method: 'POST'
  });
  if (!response.ok) throw new Error('Failed to cancel browser bootstrap.');
  return response.json();
}

export async function getSimulationHistory() {
  const response = await fetch(`${API_BASE}/simulation/history`);
  if (!response.ok) throw new Error('Failed to fetch simulation history.');
  return response.json();
}

export async function getSimulationStatus(id) {
  const response = await fetch(`${API_BASE}/simulation/${id}/status`);
  if (!response.ok) throw new Error('Failed to fetch simulation status.');
  return response.json();
}

export async function getSimulationReport(id) {
  const response = await fetch(`${API_BASE}/simulation/${id}/report`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch report.');
  }
  return response.json();
}

export async function getChatHistory(id) {
  const response = await fetch(`${API_BASE}/simulation/${id}/chat/history`);
  if (!response.ok) throw new Error('Failed to fetch chat history.');
  return response.json();
}

export async function sendChatMessage(id, message) {
  const response = await fetch(`${API_BASE}/simulation/${id}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  if (!response.ok) throw new Error('Failed to send message.');
  return response.json();
}

export async function deleteSimulation(id) {
  const response = await fetch(`${API_BASE}/simulation/${id}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete simulation.');
  return response.json();
}
