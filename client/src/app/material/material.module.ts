import { NgModule } from '@angular/core';

import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatDividerModule} from '@angular/material/divider';

@NgModule({
  declarations: [],
  imports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule
  ],
  exports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule
  ]
})
export class MaterialModule { }
