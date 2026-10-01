import { apiClient } from './client';

export const recordingsApi = {
  getRecordings: async (params = {}) => {
    const response = await apiClient.get('/recordings/', { params });
    return response.data;
  },

  getRecordingDetail: async (id) => {
    const response = await apiClient.get(`/recordings/${id}/`);
    return response.data;
  },

  getProgress: async (windowRange = '7d', languageCode = null) => {
    const params = { window: windowRange };
    if (languageCode) params.language = languageCode;
    const response = await apiClient.get('/recordings/progress/', { params });
    return response.data;
  },

  uploadRecording: async (exerciseId, audioBlob, durationSeconds) => {
    const formData = new FormData();
    formData.append('exercise_id', exerciseId);
    formData.append('audio_file', audioBlob, 'recording.webm');
    if (durationSeconds) {
      formData.append('duration_seconds', durationSeconds);
    }

    const response = await apiClient.post('/recordings/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getScenarios: async () => {
    const response = await apiClient.get('/recordings/scenarios/');
    return response.data;
  },

  getConversationSessions: async () => {
    const response = await apiClient.get('/recordings/sessions/');
    return response.data;
  },

  startConversationSession: async (scenarioId, customTitle = '') => {
    const response = await apiClient.post('/recordings/sessions/', {
      scenario_id: scenarioId,
      custom_title: customTitle,
    });
    return response.data;
  },

  getConversationSessionDetail: async (sessionId) => {
    const response = await apiClient.get(`/recordings/sessions/${sessionId}/`);
    return response.data;
  },

  sendConversationTurnReply: async (sessionId, audioBlob, durationSeconds) => {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'turn_reply.webm');
    if (durationSeconds) {
      formData.append('duration_seconds', durationSeconds);
    }

    const response = await apiClient.post(`/recordings/sessions/${sessionId}/turn/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  concludeConversationSession: async (sessionId) => {
    const response = await apiClient.post(`/recordings/sessions/${sessionId}/conclude/`);
    return response.data;
  },
};

