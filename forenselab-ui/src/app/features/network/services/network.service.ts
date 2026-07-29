import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { NetworkScanRequest, NetworkScanResponse } from '../models/network.model';

@Injectable({
  providedIn: 'root'
})
export class NetworkService {
  private apiUrl = 'http://127.0.0.1:8000/network';

  constructor(private http: HttpClient) {}

  scan(request: NetworkScanRequest): Observable<NetworkScanResponse> {
    return this.http.post<NetworkScanResponse>(`${this.apiUrl}/scan`, request).pipe(
      catchError(error => {
        console.error('Error scanning network:', error);
        return throwError(() => new Error('Failed to scan network'));
      })
    );
  }
}
