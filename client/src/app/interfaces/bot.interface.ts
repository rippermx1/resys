export default interface Bot {
    pid: number;
    symbol: string;
    short_symbol: string;
    interval: string;
    volume: number;
    leverage: number;
    brick_size: number;
    trailing_ptc: number;
    active: boolean;
    enabled: boolean;
    status: string;
    visible: boolean;
    uuid: string; // "42f8120f-d69a-4733-a6ab-7310bed4ad8f",
    market: string;
  }