/* ==========================================================================
   api.js — single place that knows how to talk to the Kilkaari backend.
   Every other script (main.js, donate page, etc.) calls window.KilkaariAPI.*
   instead of hardcoding fetch() + the base URL everywhere.
   ========================================================================== */

(function () {
  // Point this at wherever the FastAPI backend is actually running.
  // Local dev default matches `python run.py` / `uvicorn app.main:app --reload`.
  const API_BASE_URL = window.KILKAARI_API_BASE_URL || 'https://killaari-bachpan-ki.onrender.com';

  async function apiRequest(path, { method = 'GET', body, token } = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    let data = null;
    try {
      data = await res.json();
    } catch (_) {
      /* no JSON body (e.g. 204 No Content) */
    }

    if (!res.ok) {
      const message = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
      throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
    }
    return data;
  }

  window.KilkaariAPI = {
    baseUrl: API_BASE_URL,

    // --- Public forms ---
    subscribeNewsletter: (email) =>
      apiRequest('/api/newsletter/subscribe', { method: 'POST', body: { email } }),

    submitContactMessage: (payload) =>
      apiRequest('/api/contact-messages', { method: 'POST', body: payload }),

    submitVolunteerApplication: (payload) =>
      apiRequest('/api/volunteer-applications', { method: 'POST', body: payload }),

    createDonation: (payload) =>
      apiRequest('/api/donations', { method: 'POST', body: payload }),

    confirmTestPayment: (donationId) =>
      apiRequest(`/api/donations/${donationId}/confirm-test-payment`, { method: 'POST' }),

    // --- Public content (for pages that want to render live data) ---
    getPrograms: () => apiRequest('/api/programs'),
    getEvents: () => apiRequest('/api/events'),
    getCampaigns: () => apiRequest('/api/campaigns'),
    getGallery: () => apiRequest('/api/gallery'),
    getTestimonials: () => apiRequest('/api/testimonials'),
    getCenters: () => apiRequest('/api/centers'),
    getStudentStories: () => apiRequest('/api/student-stories'),

    // --- Auth ---
    login: (email, password) =>
      apiRequest('/api/auth/login', { method: 'POST', body: { email, password } }),
    register: (payload) =>
      apiRequest('/api/auth/register', { method: 'POST', body: payload }),
  };
})();
