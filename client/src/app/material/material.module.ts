import { NgModule } from '@angular/core';

import {MatCardModule} from '@angular/material/card';
import {MatIconModule} from '@angular/material/icon';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatDividerModule} from '@angular/material/divider';
import {MatTooltipModule} from '@angular/material/tooltip';

@NgModule({
  declarations: [],
  imports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule,
    MatTooltipModule
  ],
  exports: [
    MatCardModule,
    MatIconModule,
    MatExpansionModule,
    MatDividerModule,
    MatTooltipModule
  ]
})
export class MaterialModule { }
