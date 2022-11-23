import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';
import Endpoint from '../endpoints/endpoints';
import Bot from '../interfaces/bot.interface';
import { Response } from '../interfaces/response.interface';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  constructor(
    private http: HttpClient
  ) { }

  getBots(secret: string): Observable<Response<Bot[]>> {
    return this.http.post<Response<Bot[]>>(`${environment.apiUrl}${Endpoint.GET_BOT}`, {secret});
  }
}
