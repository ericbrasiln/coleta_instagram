#!/usr/bin/env python3
"""
Análise detalhada dos posts selecionados para o TCC da Bianca.
Versão 3 — apenas @euempregadadomestica e @fenatrad.br (10 posts).

Uso: python analisar_posts_v3.py
"""

import json
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

PERFIS_SHORTCODES = {
    "euempregadadomestica": [
        "C-smDZ3PnPG",
        "Cgu1LrWLl87",
        "Cf74KMeNa_7",
        "CQgO4mRneko",
        "CLnUqiAHqXZ",
        "DDKHjJqOWiY",
    ],
    "fenatrad.br": [
        "DV_orCHkYFT",
        "DUn-CpRkT_N",
        "DTifRIIERYb",
        "DSLiLOXkV5z",
    ],
}

DATA_DIR = Path("dados")


def carregar_consolidado():
    path = DATA_DIR / "posts_selecionados_consolidado.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def carregar_profile(profile_name):
    path = DATA_DIR / profile_name / "profile_metadata.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def encontrar_video(shortcode):
    for ext in [".mp4", ".MP4"]:
        for p in DATA_DIR.rglob(f"*{shortcode}*{ext}"):
            return p
    return None


def transcrever_audio(video_path, model_size="base"):
    import whisper
    print(f"  Transcrevendo {video_path.name} (modelo: {model_size})...")
    model = whisper.load_model(model_size)
    result = model.transcribe(str(video_path), language="pt", fp16=False)
    return {
        "text": result["text"].strip(),
        "segments": [
            {"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip()}
            for s in result.get("segments", [])
        ],
        "language": result.get("language", "pt"),
        "model": model_size,
    }


def limpar_caption(caption):
    if not caption:
        return ""
    return re.sub(r"\s+", " ", caption.strip())


def extrair_temas(caption, hashtags):
    temas = set()
    caption_lower = (caption or "").lower()
    mapeamento = {
        "racismo": "racismo", "racista": "racismo", "racismoambiental": "racismo ambiental",
        "feminismonegro": "feminismo negro", "feminicídio": "feminicídio", "feminicidio": "feminicídio",
        "trabalhodoméstico": "trabalho doméstico", "trabalhodomestico": "trabalho doméstico",
        "trabalhadorasdomésticas": "trabalhadoras domésticas", "trabalhadorasdomesticas": "trabalhadoras domésticas",
        "direitos": "direitos", "direitosdastrabalhadoras": "direitos das trabalhadoras",
        "direitoshumanos": "direitos humanos", "direitostrabalhistas": "direitos trabalhistas",
        "fenatrad": "FENATRAD", "pretarara": "Preta Rara", "pesadona": "pesadona",
        "beembonita": "Bem Bonita", "sonialivre": "Lei Sônia Maria",
        "essenciaissãonossosdireitos": "essenciais são nossos direitos",
        "trabalhodigno": "trabalho digno", "domestica": "doméstica", "doméstica": "doméstica",
        "diarista": "diarista", "libertemrafaelbraga": "Libertem Rafael Braga",
        "violência": "violência", "violencia": "violência",
        "assédio": "assédio", "assedio": "assédio",
        "mei": "MEI/precarização", "microempreendedor": "MEI/precarização",
        "lei": "legislação", "câmara": "legislação", "senado": "legislação",
        "sindicato": "organização sindical", "federação": "organização sindical",
    }
    for tag in (hashtags or []):
        tag_clean = tag.lower().replace("#", "").replace("_", "").replace("-", "")
        sem_acento = tag_clean.replace("ó", "o").replace("á", "a").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ú", "u").replace("ã", "a").replace("ç", "c")
        if sem_acento in mapeamento:
            temas.add(mapeamento[sem_acento])
    for palavra, tema in mapeamento.items():
        if palavra in caption_lower and len(palavra) > 3:
            temas.add(tema)
    return sorted(temas)


def formatar_duracao(segundos):
    if segundos is None:
        return None
    m = int(segundos // 60)
    s = int(segundos % 60)
    return f"{m}:{s:02d}"


def gerar_analise():
    linhas = []
    posts = carregar_consolidado()

    linhas.append("# Análise Detalhada dos Posts Selecionados")
    linhas.append(f"\nGerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    linhas.append(f"\nTCC: **A construção de imagens acerca de trabalhadoras domésticas a partir do Instagram: um olhar a partir da história do tempo presente**")
    linhas.append(f"\nOrientador: Eric Brasil Nepomuceno (UNILAB)")
    linhas.append(f"Aluna: Bianca Souza")
    linhas.append(f"\nPerfis: `@euempregadadomestica` (6 posts) e `@fenatrad.br` (4 posts)")
    linhas.append(f"Total: **10 posts**")
    linhas.append(f"\n---")

    for profile_name in PERFIS_SHORTCODES:
        shortcodes = PERFIS_SHORTCODES[profile_name]
        profile = carregar_profile(profile_name)

        linhas.append(f"\n## @{profile_name}")
        if profile:
            seg = profile.get('followers', 'N/A')
            linhas.append(f"\n**Perfil**: {profile.get('full_name', 'N/A')}")
            linhas.append(f"- Seguidores: {f'{seg:,}' if isinstance(seg, int) else seg}")
            linhas.append(f"- Bio: {profile.get('biography', 'N/A')}")
            if profile.get('external_url'):
                linhas.append(f"- URL: {profile['external_url']}")

        linhas.append(f"\n### Posts Selecionados ({len(shortcodes)} posts)")

        for i, shortcode in enumerate(shortcodes, 1):
            post = next((p for p in posts if p.get("shortcode") == shortcode), None)
            if not post or post.get("source") == "missing":
                linhas.append(f"\n#### {i}. `{shortcode}` — DADOS NÃO DISPONÍVEIS")
                linhas.append(f"Post ainda não baixado. Rode `download_seletivo.py` primeiro.")
                continue

            data_str = ""
            if post.get("date_utc"):
                try:
                    ts = int(post["date_utc"])
                    data_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    data_str = str(post["date_utc"])[:10]

            is_video = post.get("is_video", False)
            typename = post.get("typename", "")
            tipo = "Vídeo/Reel" if is_video else ("Carrossel" if typename == "GraphSidecar" else "Imagem")

            likes = post.get("likes", 0) or 0
            caption = post.get("caption", "") or ""
            caption_clean = limpar_caption(caption)
            hashtags = post.get("caption_hashtags", [])
            mentions = post.get("caption_mentions", [])
            video_views = post.get("video_view_count")
            video_duration = post.get("video_duration")
            location = post.get("location")
            tagged = post.get("tagged_users", [])
            comments_count = post.get("comments_count", 0)
            comments = post.get("comments", [])
            temas = extrair_temas(caption, hashtags)

            linhas.append(f"\n#### {i}. `{shortcode}` — {data_str}")
            linhas.append(f"")
            linhas.append(f"- **Tipo**: {tipo}")
            linhas.append(f"- **Likes**: {likes:,}")
            if video_views is not None:
                linhas.append(f"- **Views**: {video_views:,}")
            if video_duration is not None:
                linhas.append(f"- **Duração**: {formatar_duracao(video_duration)}")
            if comments_count:
                linhas.append(f"- **Comentários**: {comments_count:,}")
            if location:
                linhas.append(f"- **Localização**: {location}")
            if tagged:
                linhas.append(f"- **Marcados**: {', '.join(tagged)}")
            linhas.append(f"- **URL**: https://instagram.com/p/{shortcode}")
            if temas:
                linhas.append(f"- **Temas**: {', '.join(temas)}")

            if caption_clean:
                if len(caption_clean) > 600:
                    linhas.append(f"- **Legenda** (truncada): \"{caption_clean[:600]}...\"")
                else:
                    linhas.append(f"- **Legenda**: \"{caption_clean}\"")
                linhas.append(f"- **Comprimento**: {len(caption_clean)} caracteres")

            if hashtags:
                linhas.append(f"- **Hashtags** ({len(hashtags)}): {' '.join(hashtags[:25])}")
            if mentions:
                linhas.append(f"- **Menções**: {', '.join(mentions)}")

            caption_lower = caption.lower()
            if any(w in caption_lower for w in ["denúncia", "denuncia", "alerta", "gatilho", "violência", "violencia", "assédio", "assedio", "abus", "estupr", "mort", "assassin", "escravidão", "escrav"]):
                linhas.append(f"- **⚠️ Conteúdo sensível**: denúncia / alerta / violência")

            # Transcrição
            if is_video:
                video_file = encontrar_video(shortcode)
                if video_file and video_file.exists():
                    linhas.append(f"- **Arquivo de vídeo**: `{video_file.name}`")
                    try:
                        transcricao = transcrever_audio(video_file)
                        if transcricao["text"]:
                            linhas.append(f"- **Transcrição**: \"{transcricao['text']}\"")
                            if len(transcricao.get("segments", [])) > 1:
                                linhas.append(f"  - Transcrição segmentada:")
                                for seg in transcricao["segments"][:30]:
                                    linhas.append(f"    - [{seg['start']}s – {seg['end']}s] {seg['text']}")
                        linhas.append(f"  - Modelo: {transcricao.get('model', 'N/A')} | Idioma: {transcricao.get('language', 'N/A')}")
                    except Exception as e:
                        linhas.append(f"- **Transcrição**: ERRO — {type(e).__name__}: {e}")
                else:
                    linhas.append(f"- **Transcrição**: vídeo não baixado")

            if comments and len(comments) > 0:
                linhas.append(f"- **Amostra de comentários** ({len(comments)}):")
                for c in comments[:5]:
                    owner = c.get("owner", c.get("username", "?"))
                    text = c.get("text", "")[:100]
                    linhas.append(f"  - @{owner}: \"{text}{'...' if len(c.get('text','')) > 100 else ''}\"")

            linhas.append(f"")

    # Análise comparativa
    linhas.append(f"\n---")
    linhas.append(f"\n## Análise Comparativa")

    total_posts = len([p for p in posts if p.get("source") != "missing" and p.get("profile") in PERFIS_SHORTCODES])
    total_likes = 0
    tipos = Counter()
    all_temas = []
    all_hashtags = []
    total_comments = 0

    for p in posts:
        if p.get("source") == "missing" or p.get("profile") not in PERFIS_SHORTCODES:
            continue
        if p.get("is_video"):
            tipos["Vídeo/Reel"] += 1
        elif p.get("typename") == "GraphSidecar":
            tipos["Carrossel"] += 1
        else:
            tipos["Imagem"] += 1
        total_likes += p.get("likes", 0) or 0
        total_comments += p.get("comments_count", 0) or 0
        all_temas.extend(extrair_temas(p.get("caption", ""), p.get("caption_hashtags", [])))
        all_hashtags.extend(p.get("caption_hashtags", []))

    linhas.append(f"\n### Visão Geral dos 10 Posts Selecionados")
    linhas.append(f"- **Total analisado**: {total_posts} posts")
    for tipo, count in tipos.items():
        linhas.append(f"- **{tipo}**: {count}")
    linhas.append(f"- **Total de likes**: {total_likes:,}")
    linhas.append(f"- **Média de likes**: {total_likes // max(total_posts, 1):,}")
    linhas.append(f"- **Total de comentários (amostra)**: {total_comments:,}")
    linhas.append(f"- **Temas mais recorrentes**: {', '.join([t for t, _ in Counter(all_temas).most_common(10)])}")
    linhas.append(f"- **Hashtags mais usadas**: {', '.join([f'#{h}' for h, _ in Counter(all_hashtags).most_common(15)])}")

    # Notas
    linhas.append(f"\n---")
    linhas.append(f"\n## Notas Metodológicas")
    linhas.append(f"\n- **Coleta**: Instaloader 4.15.1 com patch do doc_id GraphQL (issue #2695)")
    linhas.append(f"- **Download seletivo**: Instaloader com `download_pictures`, `download_videos`, `download_comments`")
    linhas.append(f"- **Data da coleta**: 02-03/06/2026")
    linhas.append(f"- **Transcrição de vídeos**: OpenAI Whisper (modelo base, língua portuguesa)")
    linhas.append(f"- **Perfis**: @euempregadadomestica (6 posts) e @fenatrad.br (4 posts)")
    linhas.append(f"- **Limitações**: Comentários coletados quando disponíveis via API. Likes/views são instantâneos da data de coleta.")

    analise_path = Path("analise_posts_selecionados.md")
    with open(analise_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"Análise salva em: {analise_path}")
    return analise_path


if __name__ == "__main__":
    gerar_analise()