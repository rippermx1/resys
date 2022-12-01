import { NgModule } from '@angular/core';

import { LoginRoutingModule } from './login-routing.module';
import { ActivateComponent } from './activate/activate.component';
import { LoginComponent } from './login.component';


@NgModule({
  declarations: [
    ActivateComponent,
    LoginComponent
  ],
  imports: [  
    LoginRoutingModule
  ]
})
export class LoginModule { }
