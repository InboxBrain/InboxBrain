-- Ensure default AI_PROMPT
INSERT INTO settings(`key`,`value`)
SELECT 'AI_PROMPT', 'Sei un assistente che classifica email e restituisce SOLO JSON valido. Schema: {"intent":"...","confidence":0-1,"priority":"...","entities":{}}'
WHERE NOT EXISTS (SELECT 1 FROM settings WHERE `key`='AI_PROMPT');
