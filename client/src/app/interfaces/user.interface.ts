import Bot from './bot.interface';

export default interface User {
    id: string;
    public_key: string;
    secret_key: string;
    accept_terms: boolean;
    active: boolean;
    enable: boolean;
    rut: string;
    passport: string;
    email: string;
    cellphone: string;
    vip: boolean;
    admin: boolean;
    permission: string[];
    bots: Bot[];
    secret: string; // "52bfd2de0a2e69dff4517518590ac32a46bd76606ec22a258f99584a6e70aca2"
}
