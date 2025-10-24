// api.jsx
import axios from 'axios';

// Your FastAPI backend runs on port 8000, not 3000
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const requirementsAPI = {
  // Fixed: Use the correct endpoint paths
  getAllProjects: async () => {
    try {
      console.log('Fetching projects from Neo4j...');
      const response = await api.get('/project/debug-projects');
      console.log('Neo4j projects response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error getting projects from Neo4j:', error);
      // Fallback to simple projects endpoint
      try {
        const fallbackResponse = await api.get('/project/list-all-projects');
        return fallbackResponse.data;
      } catch (fallbackError) {
        console.error('Error getting projects from memory:', fallbackError);
        return { projects: [], count: 0 };
      }
    }
  },

  listProjects: async () => {
    try {
      const response = await api.get('/project/list-all-projects');
      return response.data;
    } catch (error) {
      console.error('Error listing projects:', error);
      return { projects: [] };
    }
  },

  // Test Cases methods
  generateTestCases: async (threadId, requirementIndex) => {
    const response = await api.post('/project/generate-test-cases', {
      thread_id: threadId,
      requirement_index: requirementIndex
    });
    return response.data;
  },

  saveTestCases: async (threadId, requirementIndex, testCases) => {
    const response = await api.post('/project/save-test-cases', {
      thread_id: threadId,
      requirement_index: requirementIndex,
      test_cases: testCases
    });
    return response.data;
  },

  getTestCases: async (threadId, requirementIndex) => {
    const response = await api.get(`/project/test-cases/${threadId}/${requirementIndex}`);
    return response.data;
  },

  // Project methods
  createProject: async (projectData) => {
    const response = await api.post('/project/create', projectData);
    return response.data;
  },

  regenerateWithFeedback: async (feedbackData) => {
    const response = await api.post('/project/regenerate-with-feedback', feedbackData);
    return response.data;
  },

  updateItem: async (updateData) => {
    const response = await api.post('/project/update-item', updateData);
    return response.data;
  },

  selectKeyword: async (threadId, keywordIndex) => {
    const response = await api.post('/project/select-keyword', {
      thread_id: threadId,
      keyword_index: keywordIndex
    });
    return response.data;
  },

  regenerate: async (threadId, regenerateType) => {
    const response = await api.post('/project/regenerate', {
      thread_id: threadId,
      regenerate_type: regenerateType
    });
    return response.data;
  },

  // Selective operations
  regenerateRequirements: async (threadId, requirementIndexes) => {
    const response = await api.post('/project/regenerate-requirements', {
      thread_id: threadId,
      requirement_indexes: requirementIndexes
    });
    return response.data;
  },

  regenerateRisks: async (threadId, riskIndexes) => {
    const response = await api.post('/project/regenerate-risks', {
      thread_id: threadId,
      risk_indexes: riskIndexes
    });
    return response.data;
  },

  getRisksFromNeo4j: async (projectName, riskIndexes = null) => {
    try {
      console.log('Fetching risks from Neo4j for project:', projectName);
      
      const params = {
        project_name: projectName
      };

      if (riskIndexes) {
        params.risk_indexes = Array.isArray(riskIndexes) 
          ? riskIndexes.join(',') 
          : riskIndexes;
      }

      console.log('API call params:', params);
      
      const response = await api.get('/project/risks-from-neo4j', { 
        params: params 
      });
      
      console.log('Risks fetched successfully:', response.data);
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error occurred';
      console.error('Error fetching risks from Neo4j:', errorMsg);
      
      return {
        risks: [],
        count: 0,
        message: `Error loading risks: ${errorMsg}`,
      };
    }
  },

  getProjectDataFromNeo4j: async (projectName) => {
    try {
      console.log('Loading project from Neo4j:', projectName);
      
      const response = await api.post('/project/load-from-neo4j', null, {
        params: { project_name: projectName }
      });
      
      console.log('Project loaded:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error loading project:', error);
      return {
        requirements: [],
        risks: [],
        message: `Error loading project: ${error.response?.data?.detail || error.message}`
      };
    }
  },

  saveSelectedRequirements: async (threadId, requirements, risks, keyword) => {
    const response = await api.post('/project/save-selected', {
      thread_id: threadId,
      requirements: requirements,
      risks: risks,
      keyword: keyword
    });
    return response.data;
  },

  updateRisksInNeo4j: async (threadId, riskData) => {
    const response = await api.post('/project/update-risks', {
      thread_id: threadId,
      risk_data: riskData
    });
    return response.data;
  },

  updateSingleRisk: async (threadId, riskIndex, risk, requirement) => {
    const response = await api.post('/project/update-single-risk', {
      thread_id: threadId,
      risk_index: riskIndex,
      risk: risk,
      requirement: requirement
    });
    return response.data;
  },

  saveProject: async (threadId) => {
    const response = await api.post('/project/save', null, {
      params: { thread_id: threadId }
    });
    return response.data;
  },

  getProject: async (threadId) => {
    const response = await api.get(`/project/${threadId}`);
    return response.data;
  },

  queryRisks: async (query) => {
    try {
      const response = await api.post('/project/search-risks', null, {
        params: { query: query }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching risks:', error);
      return [];
    }
  }
};

export default api;