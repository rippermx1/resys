import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-crud-bot',
  templateUrl: './crud-bot.component.html',
  styleUrls: ['./crud-bot.component.sass']
})
export class CrudBotComponent implements OnInit {
  symbolOptions = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'];
  symbolLabel = this.symbolOptions[0];
  intervalOptions = ['5m', '15m', '1h'];
  intervalLabel = this.intervalOptions[0];
  volumeOptions = ['10', '20', '30'];
  volumeLabel = this.volumeOptions[0];
  leverageOptions = ['10', '25', '50'];
  leverageLabel = this.leverageOptions[0];
  bricksizeOptions = ['0.1', '0.5', '1'];
  bricksizeLabel = this.bricksizeOptions[0];
  trailingPercentageOptions = ['0.1', '0.25', '0.75'];
  trailingPercentageLabel = this.trailingPercentageOptions[0];

  constructor() { }

  ngOnInit(): void {
  }

  onClick(option: any, menu: string): void {
    console.log(option);
    switch (menu) {
      case 'symbol':
        this.symbolLabel = option;
        break;
      case 'interval':
        this.intervalLabel = option;
        break;
      case 'volume':
        this.volumeLabel = option;
        break;
      case 'leverage':
        this.leverageLabel = option;
        break;
      case 'bricksize':
        this.bricksizeLabel = option;
        break;
      case 'trailingptc':
        this.trailingPercentageLabel = option;
        break;
    }
  }

}
