import { Component, OnInit } from '@angular/core';
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
    private userService: UserService
  ) { }

  ngOnInit(): void {
    let secret = "52bfd2de0a2e69dff4517518590ac32a46bd76606ec22a258f99584a6e70aca2"
    this.userService.getBots(secret).subscribe((response) => {
      this.bots = response.data;
    });
  }

}
