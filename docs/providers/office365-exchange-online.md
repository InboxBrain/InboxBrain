# Office 365 / Exchange Online

- Server IMAP: `outlook.office365.com`
- Porta: `993` (SSL)
- Autenticazione: preferibile OAuth2; App Password se l'org lo consente.

**Nota**: molte tenant aziendali disabilitano IMAP basic auth. In tal caso serve ingestor con OAuth IMAP o — meglio — usare **Graph** + webhook (estensione non inclusa). 
