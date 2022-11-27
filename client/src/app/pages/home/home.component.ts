import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { CrudBotComponent } from 'src/app/components/modals/crud-bot/crud-bot.component';
import Bot from 'src/app/interfaces/bot.interface';
import { UserService } from 'src/app/services/user.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.sass']
})
export class HomeComponent implements OnInit {
  bots: Bot[] = [];
  panelOpenState = false;

  constructor(
    private userService: UserService,
    private dialog: MatDialog
  ) { }

  ngOnInit(): void {
    let secret = "52bfd2de0a2e69dff4517518590ac32a46bd76606ec22a258f99584a6e70aca2"
    this.userService.getBots(secret).subscribe((response) => {
      this.bots = response.data;
    });
  }

  openDialog() {
    const dialogRef = this.dialog.open(CrudBotComponent);

    dialogRef.afterClosed().subscribe(result => {
      console.log(`Dialog result: ${result}`);
    });
  }

}
