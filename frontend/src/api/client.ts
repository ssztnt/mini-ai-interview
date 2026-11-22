import type { AppConfig, Interview, InterviewListItem, Objective } from './types'

export class ApiError extends Error {
  readonly status: number
  /** Machine-readable reason, e.g. 'inappropriate_language'. */
  readonly code: string | null

  constructor(status: number, message: string, code: string | null = null) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(
      0,
      'Cannot reach the server. Check that the backend is running on port 8000.',
    )
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg: string }) => d.msg).join('. ')
          : `Request failed (${response.status})`
    throw new ApiError(response.status, message, body?.code ?? null)
  }
  return response.json() as Promise<T>
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })

export const api = {
  config: () => request<AppConfig>('/config'),
  listInterviews: () => request<InterviewListItem[]>('/interviews'),
  getInterview: (id: string) => request<Interview>(`/interviews/${id}`),
  createInterview: (topic: string, numQuestions: number) =>
    post<Interview>('/interviews', { topic, num_questions: numQuestions }),
  updatePlan: (id: string, objectives: Objective[]) =>
    request<Interview>(`/interviews/${id}/plan`, {
      method: 'PUT',
      body: JSON.stringify({ objectives }),
    }),
  start: (id: string) => post<Interview>(`/interviews/${id}/start`),
  answer: (id: string, answer: string) => post<Interview>(`/interviews/${id}/answers`, { answer }),
  complete: (id: string) => post<Interview>(`/interviews/${id}/complete`),
}
