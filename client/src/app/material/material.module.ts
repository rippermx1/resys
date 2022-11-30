import { NgModule } from '@angular/core';

import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatDividerModule} from '@angular/material/divider';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatButtonModule} from '@angular/material/button';
import {MatDialogModule} from '@angular/material/dialog';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSidenavModule} from '@angular/material/sidenav';

@NgModule({
  declarations: [],
  imports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule,
    MatTooltipModule,
    MatButtonModule,
    MatDialogModule,
    MatInputModule,
    MatSelectModule,
    MatMenuModule,
    MatProgressBarModule,
    MatSidenavModule
  ],
  exports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule,
    MatTooltipModule,
    MatButtonModule,
    MatDialogModule,
    MatInputModule,
    MatSelectModule,
    MatMenuModule,
    MatProgressBarModule,
    MatSidenavModule
  ]
})
export class MaterialModule { }
