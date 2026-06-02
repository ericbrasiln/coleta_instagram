#!/usr/bin/env python3
"""
Gera relatório descritivo a partir dos dados coletados via Instaloader.
Lê os JSONs de metadata e gera um relatório em Markdown.

Uso: python gerar_relatorio.py

Espera a seguinte estrutura:
  dados/euempregadadomestica/profile_metadata.json
  dados/euempregadadomestica/posts_metadata.json
  dados/fenatrad.br/profile_metadata.json
  dados/fenatrad.br/posts_metadata.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

PERFIS = ["euempregadadomestica", "fenatrad.br"]
DATA_DIR = Path("dados")


def carregar_perfil(username):
    """Carrega metadata do perfil."""
    path = DATA_DIR / username / "profile_metadata.json"
    if not path.exists():
        print(f"AVISO: {path} não encontrado. Pulando @{username}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def carregar_posts(username):
    """Carrega metadata dos posts."""
    path = DATA_DIR / username / "posts_metadata.json"
    if not path.exists():
        print(f"AVISO: {path} não encontrado. Pulando posts de @{username}")
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def analisar_posts(posts):
    """Analisa lista de posts e retorna estatísticas."""
    if not posts:
        return {}

    # Contadores
    tipos = Counter(p["typename"] for p in posts)
    videos = [p for p in posts if p.get("is_video")]
    fotos = [p for p in posts if not p.get("is_video")]
    patrocinados = [p for p in posts if p.get("is_sponsored")]

    # Likes
    likes_list = [p["likes"] for p in posts if p.get("likes") is not None]
    avg_likes = sum(likes_list) / len(likes_list) if likes_list else 0
    max_likes = max(likes_list) if likes_list else 0
    min_likes = min(likes_list) if likes_list else 0
    total_likes = sum(likes_list)

    # Views ( vídeos)
    video_views = [p["video_view_count"] for p in videos if p.get("video_view_count")]

    # Hashtags
    all_hashtags = []
    for p in posts:
        if p.get("caption_hashtags"):
            all_hashtags.extend(p["caption_hashtags"])
    hashtag_counts = Counter(all_hashtags)

    # Menções
    all_mentions = []
    for p in posts:
        if p.get("caption_mentions"):
            all_mentions.extend(p["caption_mentions"])
    mention_counts = Counter(all_mentions)

    # Período
    datas = sorted([p["date_utc"][:10] for p in posts if p.get("date_utc")])
    primeiro_post = datas[0] if datas else None
    ultimo_post = datas[-1] if datas else None

    # Posts por mês
    posts_por_mes = Counter()
    for p in posts:
        if p.get("date_utc"):
            mes = p["date_utc"][:7]  # YYYY-MM
            posts_por_mes[mes] += 1

    # Posts por dia da semana
    dias_semana = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    posts_por_dia = Counter()
    for p in posts:
        if p.get("date_utc"):
            from datetime import datetime as dt
            d = dt.fromisoformat(p["date_utc"].replace("Z", "+00:00"))
            posts_por_dia[d.weekday()] += 1

    # Posts com legenda vs sem legenda
    com_legenda = sum(1 for p in posts if p.get("caption"))
    sem_legenda = len(posts) - com_legenda

    # Comprimento das legendas
    legendas = [p["caption"] for p in posts if p.get("caption")]
    comp_legendas = [len(l) for l in legendas]
    avg_legenda = sum(comp_legendas) / len(comp_legendas) if comp_legendas else 0

    # Top posts por likes
    top5_likes = sorted(posts, key=lambda p: p.get("likes", 0), reverse=True)[:5]

    return {
        "total_posts": len(posts),
        "tipos": dict(tipos),
        "n_fotos": len(fotos),
        "n_videos": len(videos),
        "n_patrocinados": len(patrocinados),
        "likes_total": total_likes,
        "likes_media": round(avg_likes, 1),
        "likes_max": max_likes,
        "likes_min": min_likes,
        "video_views_total": sum(video_views) if video_views else 0,
        "video_views_media": round(sum(video_views) / len(video_views), 1) if video_views else 0,
        "video_views_max": max(video_views) if video_views else 0,
        "hashtags_total": len(all_hashtags),
        "hashtags_unicos": len(set(all_hashtags)),
        "top_hashtags": hashtag_counts.most_common(20),
        "top_menções": mention_counts.most_common(10),
        "primeiro_post": primeiro_post,
        "ultimo_post": ultimo_post,
        "posts_por_mes": dict(sorted(posts_por_mes.items())),
        "posts_por_dia_semana": {dias_semana[k]: v for k, v in sorted(posts_por_dia.items())},
        "com_legenda": com_legenda,
        "sem_legenda": sem_legenda,
        "avg_comprimento_legenda": round(avg_legenda, 0),
        "top5_likes": top5_likes,
    }


def gerar_relatorio():
    """Gera relatório descritivo consolidado."""
    linhas = []
    linhas.append(f"# Relatório Descritivo — Coleta Instagram")
    linhas.append(f"\nGerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    linhas.append(f"\n---")
    linhas.append(f"\n## Contexto")
    linhas.append(f"\nTCC: **A construção de imagens acerca de trabalhadoras domésticas a partir do Instagram: um olhar a partir da história do tempo presente**")
    linhas.append(f"\nOrientadora: Eric Brasil Nepomuceno (UNIRIO? UNILAB?)")
    linhas.append(f"Aluna: Bianca Souza")
    linhas.append(f"\nPerfis analisados: `@euempregadadomestica` e `@fenatrad.br`")
    linhas.append(f"\n---")

    for username in PERFIS:
        linhas.append(f"\n## @{username}")

        profile = carregar_perfil(username)
        if profile:
            linhas.append(f"\n### Dados do Perfil")
            linhas.append(f"- **Nome**: {profile.get('full_name', 'N/A')}")
            linhas.append(f"- **Biografia**: {profile.get('biography', 'N/A')}")
            linhas.append(f"- **Seguidores**: {profile.get('followers', 'N/A'):,}" if isinstance(profile.get('followers'), int) else f"- **Seguidores**: {profile.get('followers', 'N/A')}")
            linhas.append(f"- **Seguindo**: {profile.get('followees', 'N/A'):,}" if isinstance(profile.get('followees'), int) else f"- **Seguindo**: {profile.get('followees', 'N/A')}")
            linhas.append(f"- **Total de posts**: {profile.get('mediacount', 'N/A')}")
            linhas.append(f"- **Verificado**: {'Sim' if profile.get('is_verified') else 'Não'}")
            linhas.append(f"- **Conta business**: {'Sim' if profile.get('is_business_account') else 'Não'}")
            if profile.get('business_category_name'):
                linhas.append(f"- **Categoria business**: {profile['business_category_name']}")
            if profile.get('external_url'):
                linhas.append(f"- **URL externa**: {profile['external_url']}")
            linhas.append(f"- **ID**: {profile.get('userid', 'N/A')}")

        posts = carregar_posts(username)
        if posts:
            stats = analisar_posts(posts)
            linhas.append(f"\n### Estatísticas dos Posts")
            linhas.append(f"- **Total de posts coletados**: {stats['total_posts']}")
            linhas.append(f"- **Fotos**: {stats['n_fotos']}")
            linhas.append(f"- **Vídeos/Reels**: {stats['n_videos']}")
            linhas.append(f"- **Tipos de conteúdo**: {stats['tipos']}")
            linhas.append(f"- **Posts patrocinados**: {stats['n_patrocinados']}")
            linhas.append(f"- **Período**: {stats['primeiro_post']} a {stats['ultimo_post']}")
            linhas.append(f"- **Posts com legenda**: {stats['com_legenda']} / sem legenda: {stats['sem_legenda']}")
            linhas.append(f"- **Comprimento médio das legendas**: {stats['avg_comprimento_legenda']:.0f} caracteres")

            linhas.append(f"\n### Engajamento")
            linhas.append(f"- **Total de likes**: {stats['likes_total']:,}")
            linhas.append(f"- **Média de likes por post**: {stats['likes_media']:,}")
            linhas.append(f"- **Máximo de likes**: {stats['likes_max']:,}")
            linhas.append(f"- **Mínimo de likes**: {stats['likes_min']:,}")
            if stats['n_videos'] > 0:
                linhas.append(f"- **Total de views em vídeos**: {stats['video_views_total']:,}")
                linhas.append(f"- **Média de views por vídeo**: {stats['video_views_media']:,}")
                linhas.append(f"- **Máximo de views**: {stats['video_views_max']:,}")

            linhas.append(f"\n### Top 5 Posts por Likes")
            for i, p in enumerate(stats['top5_likes'], 1):
                legenda = (p.get('caption') or '')[:80].replace('\n', ' ')
                linhas.append(f"{i}. **{p.get('date_utc', '')[:10]}** — {p.get('likes', 0):,} likes")
                linhas.append(f"   - `instagram.com/p/{p.get('shortcode')}`")
                linhas.append(f"   - \"{legenda}{'...' if len(p.get('caption') or '') > 80 else ''}\"")

            linhas.append(f"\n### Hashtags mais usadas (top 20)")
            if stats['top_hashtags']:
                for tag, count in stats['top_hashtags']:
                    linhas.append(f"- `#{tag}`: {count} vezes")
            else:
                linhas.append("- Nenhuma hashtag encontrada")

            linhas.append(f"\n### Menções mais frequentes (top 10)")
            if stats['top_menções']:
                for menção, count in stats['top_menções']:
                    linhas.append(f"- `@{menção}`: {count} vezes")

            linhas.append(f"\n### Posts por Mês")
            for mes, count in sorted(stats['posts_por_mes'].items()):
                linhas.append(f"- **{mes}**: {count} posts")

            linhas.append(f"\n### Posts por Dia da Semana")
            for dia, count in stats['posts_por_dia_semana'].items():
                linhas.append(f"- **{dia}**: {count} posts")

        linhas.append(f"\n---")

    # Salvar
    relatorio_path = Path("relatorio_descritivo.md")
    with open(relatorio_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"Relatório salvo em: {relatorio_path}")
    return relatorio_path


if __name__ == "__main__":
    gerar_relatorio()