// Mirrors backend/app/models.py

export type Status = 'planning' | 'in_progress' | 'completed'
export type SentimentLabel = 'positive' | 'neutral' | 'negative' | 'mixed'

export interface Objective {
  theme: string
  goal: string
}

export interface Turn {
  objective_index: number
  lead_in: string
  question: string
  answer: string | null
  asked_at: string
  answered_at: string | null
}

export interface Finding {
  objective: string
  finding: string
  quote: string
}

export interface Summary {
  overview: string
  findings: Finding[]
  themes: { name: string; description: string }[]
  key_points: string[]
  sentiment: { label: SentimentLabel; score: number; rationale: string }
  emotions: { name: string; intensity: 'low' | 'medium' | 'high' }[]
  keywords: string[]
}

export interface ClassicAnalysis {
  method: string
  sentiment_label: SentimentLabel
  sentiment_score: number
  answer_scores: number[]
  keywords: string[]
}

export interface Interview {
  id: string
  topic: string
  status: Status
  provider: string
  model: string
  research_goal: string
  plan: Objective[]
  turns: Turn[]
  summary: Summary | null
  analysis: ClassicAnalysis | null
  created_at: string
  completed_at: string | null
  awaiting_summary: boolean
}

export interface InterviewListItem {
  id: string
  topic: string
  completed_at: string | null
  num_questions: number
  sentiment: SentimentLabel | null
  overview: string | null
}

export interface AppConfig {
  provider: 'openai' | 'foundry'
  model: string
  demo: boolean
}
