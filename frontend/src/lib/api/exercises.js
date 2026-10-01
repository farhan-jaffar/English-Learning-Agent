import { apiClient } from './client';

export const exercisesApi = {
  getExercises: async (params = {}) => {
    const response = await apiClient.get('/exercises/', { params });
    return response.data;
  },

  getNextExercise: async (languageCode, excludeId) => {
    const params = {};
    if (languageCode) params.language = languageCode;
    if (excludeId) params.exclude_id = excludeId;
    const response = await apiClient.get('/exercises/next/', { params });
    return response.data;
  },

  getExerciseDetail: async (id) => {
    const response = await apiClient.get(`/exercises/${id}/`);
    return response.data;
  },
};
