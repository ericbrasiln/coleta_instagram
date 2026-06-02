# Coleta Instagram — TCC Bianca Souza

Dados dos perfis `@euempregadadomestica` e `@fenatrad.br` do Instagram.

## Contexto

**TCC**: "A construção de imagens acerca de trabalhadoras domésticas a partir do Instagram: um olhar a partir da história do tempo presente"

**Aluna**: Bianca Souza
**Orientador**: Eric Brasil Nepomuceno

## Estrutura

```
coleta_instagram/
├── INSTALACAO.md          # Instruções de instalação e coleta
├── coletar_com_login.py   # Script de coleta com login
├── gerar_relatorio.py     # Script de geração de relatório
├── requirements.txt       # Dependências Python
├── dados/                 # Dados coletados (NÃO versionar)
│   ├── euempregadadomestica/
│   │   ├── profile_metadata.json
│   │   ├── posts_metadata.json
│   │   └── *.jpg (imagens dos posts)
│   └── fenatrad.br/
│       ├── profile_metadata.json
│       ├── posts_metadata.json
│       └── *.jpg (imagens dos posts)
└── relatorio_descritivo.md  # Gerado automaticamente
```

## Como usar

### 1. Instalar dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install instaloader
```

### 2. Fazer login (uma vez só)

```bash
python coletar_metadata.py --login SEU_USERNAME
```

### 3. Coletar metadata (sem imagens)

```bash
python coletar_metadata.py SEU_USERNAME euempregadadomestica fenatrad.br
```

### 4. Gerar relatório

```bash
python gerar_relatorio.py
```

## Dados coletados por post

- shortcode, mediaid
- data UTC
- caption (legenda)
- hashtags e menções na legenda
- número de likes
- tipo (foto/vídeo/carrossel)
- views (se vídeo)
- localização
- URL da mídia (referência, sem download)

## Dados do perfil

- username, nome completo, bio
- número de seguidores e seguindo
- total de posts
- conta verificada / business
- URL externa

## Notas éticas

- Os dados são públicos (perfis públicos)
- A coleta é para pesquisa acadêmica (TCC)
- Recomenda-se anonimização para publicização dos resultados
- Não redistribuir dados brutos sem consentimento