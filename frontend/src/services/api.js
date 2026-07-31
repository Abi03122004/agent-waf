import axios from 'axios';

const API_BASE_URL = typeof window !== 'undefined' && window.location.port === '5173'
  ? ''
  : 'http://127.0.0.1:8001';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendAgentChat = async (message, agentId = 'sample-agent', sessionId = 'default-session') => {
  const response = await client.post('/agent/chat', {
    message,
    agent_id: agentId,
    session_id: sessionId,
  });
  return response.data;
};

export const getMetrics = async () => {
  const response = await client.get('/metrics');
  return response.data;
};

export const getAuditLogs = async (limit = 100) => {
  const response = await client.get('/audit', { params: { limit } });
  return response.data;
};

export const getRules = async () => {
  const response = await client.get('/rules');
  return response.data;
};

export const reloadRules = async () => {
  const response = await client.post('/rules/reload');
  return response.data;
};

export const resetWafLogs = async () => {
  const response = await client.delete('/agent/logs/reset');
  return response.data;
};

export default {
  sendAgentChat,
  getMetrics,
  getAuditLogs,
  getRules,
  reloadRules,
  resetWafLogs,
};
