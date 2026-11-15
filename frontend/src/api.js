const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "formcraft_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

async function request(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && getToken()) headers.Authorization = `Bearer ${getToken()}`;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message = "Something went wrong";
    if (typeof data.detail === "string") message = data.detail;
    else if (Array.isArray(data.detail) && data.detail.length) message = data.detail[0].msg;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

export const registerUser = (full_name, email, password) =>
  request("/auth/register", { method: "POST", body: { full_name, email, password } });

export const loginUser = (email, password) =>
  request("/auth/login", { method: "POST", body: { email, password } });

export const getDashboardOverview = () => request("/dashboard/overview", { auth: true });
