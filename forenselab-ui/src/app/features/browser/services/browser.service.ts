import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BrowserHistoryRequest, BrowserHistoryResponse } from '../models/browser.model';

@Injectable({
  providedIn: 'root'
})
export class BrowserService {
  private apiUrl = 'http://127.0.0.1:8000/api/browser';

  constructor(private http: HttpClient) {}

  getHistory(request: BrowserHistoryRequest): Observable<BrowserHistoryResponse> {
    return this.http.post<BrowserHistoryResponse>(`${this.apiUrl}/history`, request).pipe(
      catchError(error => {
        console.error('Error getting browser history:', error);
        return throwError(() => new Error('Failed to get browser history'));
      })
    );
  }
}
