import axios from 'axios';

// Use relative URLs so nginx can proxy the requests
const METRICS_API = process.env.REACT_APP_METRICS_API || '';
const EVENTS_API = process.env.REACT_APP_EVENTS_API || '';

export const fetchApplications = async () => {
  try {
    const response = await axios.get(`${METRICS_API}/api/applications`);
    return response.data || [];
  } catch (error) {
    console.error('Error fetching applications:', error);
    return [];
  }
};

export const fetchStats = async () => {
  try {
    const response = await axios.get(`${EVENTS_API}/api/stats`);
    return response.data || { total_deployments: 0, successful_deployments: 0, failed_deployments: 0, total_applications: 0 };
  } catch (error) {
    console.error('Error fetching stats:', error);
    // Return default stats if event-processor is not available
    return { total_deployments: 0, successful_deployments: 0, failed_deployments: 0, total_applications: 0 };
  }
};

export const fetchEvents = async (appName = null) => {
  try {
    const url = appName 
      ? `${EVENTS_API}/api/events?app_name=${appName}`
      : `${EVENTS_API}/api/events`;
    const response = await axios.get(url);
    return response.data || { events: [] };
  } catch (error) {
    console.error('Error fetching events:', error);
    return { events: [] };
  }
};
