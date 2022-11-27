import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CrudBotComponent } from './crud-bot.component';

describe('CrudBotComponent', () => {
  let component: CrudBotComponent;
  let fixture: ComponentFixture<CrudBotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CrudBotComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CrudBotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
