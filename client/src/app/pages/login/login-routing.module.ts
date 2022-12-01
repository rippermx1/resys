import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  { path: '',
    loadChildren: () => import('./login.component').then(m => m.LoginComponent)
  },
  {
    path: 'activate',
    loadChildren: () => import('./activate/activate.component').then(m => m.ActivateComponent)
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class LoginRoutingModule { }
