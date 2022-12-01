import { Injectable } from '@angular/core';
import { Parameter } from 'src/app/interfaces/parameter.interface';

@Injectable({
  providedIn: 'root'
})
export class ParameterService {
  private symbol = {
    options: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    label: 'BTCUSDT'
  }
  private interval = {
    options: ['5m', '15m', '1h'],
    label: '5m'
  }
  private volume = {
    options: ['10', '20', '30'],
    label: '10'
  }
  private leverage = {
    options: ['10', '25', '50'],
    label: '10'
  }
  private bricksize = {
    options: ['0.1', '0.5', '1'],
    label: '0.1'
  }
  private trailingPercentage = {
    options: ['0.1', '0.25', '0.75'],
    label: '0.1'
  }

  constructor() { }

  getSymbol(): Parameter {
    return this.symbol;
  }
  getInterval(): Parameter {
    return this.interval;
  }
  getVolume(): Parameter {
    return this.volume;
  }
  getLeverage(): Parameter {
    return this.leverage;
  }
  getBrickSize(): Parameter {
    return this.bricksize;
  }
  getTrailingPercentage(): Parameter {
    return this.trailingPercentage;
  }
}