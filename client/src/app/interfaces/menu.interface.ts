export interface Menu {
    label: string;
    url: string;
    have_items: boolean;
    visible: boolean;
    enabled: boolean;
    items: Menu[];
}

export interface ClientMenu {
    uuid: string; // 24337283-d233-4ee6-8617-d406054707e0
    category: string;
    menu: Menu[];
}