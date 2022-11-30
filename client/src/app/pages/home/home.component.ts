import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { CrudBotComponent } from 'src/app/components/modals/crud-bot/crud-bot.component';
import Bot from 'src/app/interfaces/bot.interface';
import { Parameter } from 'src/app/interfaces/parameter.interface';
import { UserService } from 'src/app/services/user.service';
import { ParameterService } from 'src/app/shared/services/parameter.service';
import { Observable } from 'rxjs';
import { Menu } from 'src/app/interfaces/menu.interface';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.sass']
})
export class HomeComponent implements OnInit {
  bots: Bot[] = [];
  panelOpenState = false;
  running: boolean = false;
  editing: boolean = false;
  intervalParameter: Parameter = {options: [], label: ''};
  volumeParameter: Parameter = {options: [], label: ''};
  leverageParameter: Parameter = {options: [], label: ''};
  brickSizeParameter: Parameter = {options: [], label: ''};
  trailingPercentageParameter: Parameter = {options: [], label: ''};
  secret = "52bfd2de0a2e69dff4517518590ac32a46bd76606ec22a258f99584a6e70aca2"
  fetchingData: boolean = false;
  shouldRun: boolean = false;
  collapseTest: boolean = false;
  menu$: Observable<any> = new Observable();

  constructor(
    private userService: UserService,
    private dialog: MatDialog,
    private parameterService: ParameterService
  ) { 
    this.intervalParameter = this.parameterService.getInterval();
    this.volumeParameter = this.parameterService.getVolume();
    this.leverageParameter = this.parameterService.getLeverage();
    this.brickSizeParameter = this.parameterService.getBrickSize();
    this.trailingPercentageParameter = this.parameterService.getTrailingPercentage();
  }

  ngOnInit(): void {
    this.userService.getBots(this.secret).subscribe((response) => {
      this.bots = response.data;
    });

    this.menu$ = this.userService.getClientMenu(this.secret, '24337283-d233-4ee6-8617-d406054707e0');
    console.log(this.menu$);
  }

  openDialog() {
    const dialogRef = this.dialog.open(CrudBotComponent, {data: {title: 'Create Bot'}});

    dialogRef.afterClosed().subscribe(result => {
      console.log(`Dialog result: ${result}`);
    });
  }

  turnOn(bot: Bot) {
    this.fetchingData = true;
    bot.active = !bot.active;
    this.userService.updateBotActive(this.secret, bot.uuid, bot.active).subscribe((response) => {
      console.log(response);
      if (response)
        this.fetchingData = false;
      this.bots.find((b) => b.uuid === bot.uuid)!.status = bot.status;
    });
  }

  delete() {

  }

  edit(bot: Bot) {
    this.editing = !this.editing;
    console.log(bot);
    this.intervalParameter.label = bot.interval.toString();
    this.volumeParameter.label = bot.volume.toString();
    this.leverageParameter.label = bot.leverage.toString();
    this.brickSizeParameter.label = bot.brick_size.toString();
    this.trailingPercentageParameter.label = bot.trailing_ptc.toString();
  }

  onOpen(bot: Bot) {
    console.log(bot);
    this.panelOpenState = true;
  }

  pause(bot: Bot) {
    this.fetchingData = true;
    this.running = !this.running;
    bot.status = (this.running) ? 'PAUSED' : 'RUNNING';
    this.userService.updateBotStatus(this.secret, bot.uuid, bot.status).subscribe((response) => {
      console.log(response);
      if (response)
        this.fetchingData = false;
      this.bots.find((b) => b.uuid === bot.uuid)!.status = bot.status;
    });
  }

  onClick(option: any, menu: string): void {
    console.log(option);
    switch (menu) {
      case 'interval':
        this.intervalParameter.label = option;
        break;
      case 'volume':
        this.volumeParameter.label = option;
        break;
      case 'leverage':
        this.leverageParameter.label = option;
        break;
      case 'bricksize':
        this.brickSizeParameter.label = option;
        break;
      case 'trailingptc':
        this.trailingPercentageParameter.label = option;
        break;
    }
  }

}
