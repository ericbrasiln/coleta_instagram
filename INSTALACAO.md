# Coleta Instagram — Instruções de Instalação e Coleta

> **Apenas metadata e métricas — sem download de imagens.**

## Instalação (rodar uma vez)

```bash
mkdir -p coleta_instagram && cd coleta_instagram
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows
pip install instaloader
```

Copie para dentro da pasta os scripts `coletar_metadata.py` e `gerar_relatorio.py`.

## Login (rodar uma vez)

```bash
source venv/bin/activate
python coletar_metadata.py --login SEU_USERNAME
```

Vai pedir a senha e pode pedir verificação (código SMS/email). A sessão fica salva e não precisa mais da senha.

## Coleta dos perfis

```bash
source venv/bin/activate

# Perfil 1: euempregadadomestica
python coletar_metadata.py SEU_USERNAME euempregadadomestica

# Aguardar ~3 minutos, depois:

# Perfil 2: fenatrad.br
python coletar_metadata.py SEU_USERNAME fenatrad.br
```

Isso salva **apenas metadata** (JSON): dados do perfil + texto e métricas de cada post. **Não baixa imagens.**

Resultado em `dados/euempregadadomestica/` e `dados/fenatrad.br/`.

## Gerar o relatório

```bash
python gerar_relatorio.py
```

Gera `relatorio_descritivo.md` com volume, métricas, hashtags top, engajamento, etc.

## Após a coleta

Compacte e envie os JSONs:

```bash
# Apenas os JSONs (leve):
tar czf metadata.tar.gz dados/*/profile_metadata.json dados/*/posts_metadata.json

# Ou tudo:
zip -r coleta_instagram.zip dados/
```

Me envie pelo Telegram e eu gero o relatório.