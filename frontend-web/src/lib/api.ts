export interface QueryRequest {
  question: string;
  top_k?: number;
  enable_google_search?: boolean;
}

export interface SourceNode {
  source_type: "document" | "web";
  text: string;
  file_name?: string;
  url?: string;
  title?: string;
  score?: number;
  metadata?: Record<string, any>;
}

export interface QueryResponse {
  answer: string;
  sources: SourceNode[];
  llm_model: string;
  query_time_ms: number;
}

export async function askQuestion(request: QueryRequest): Promise<QueryResponse> {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";
  
  const response = await fetch(`${apiUrl}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorDetail = "An error occurred while generating the response.";
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      // Ignored if json parsing fails
    }
    throw new Error(errorDetail);
  }

  return await response.json();
}
