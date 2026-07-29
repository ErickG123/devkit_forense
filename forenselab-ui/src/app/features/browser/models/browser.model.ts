export interface BrowserHistoryRequest {
  browser: string;
  limit?: number;
}

export interface BrowserHistoryResponse {
  status: string;
  data: any[];
}
