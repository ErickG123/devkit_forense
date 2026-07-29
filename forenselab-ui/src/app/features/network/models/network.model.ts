export interface NetworkScanRequest {
  target: string;
  ports?: number[];
}

export interface NetworkScanResponse {
  target: string;
  status: string;
  data: any[];
}
