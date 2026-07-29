import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { MailAnalysisRequest, MailAnalysisResponse } from '../models/mail.model';

@Injectable({
  providedIn: 'root'
})
export class MailService {
  private apiUrl = 'http://127.0.0.1:8000/api/mail';

  constructor(private http: HttpClient) {}

  analyze(request: MailAnalysisRequest): Observable<MailAnalysisResponse> {
    return this.http.post<MailAnalysisResponse>(`${this.apiUrl}/analyze`, request).pipe(
      catchError(error => {
        console.error('Error analyzing mail:', error);
        return throwError(() => new Error('Failed to analyze mail'));
      })
    );
  }
}
