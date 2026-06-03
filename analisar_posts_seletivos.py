#!/usr/bin/env python3
"""
Análise detalhada dos posts selecionados para o TCC da Bianca.

Para cada post:
  - Metadados completos (likes, data, tipo, hashtags, menções)
  - Legendas tratadas (limpeza, normalização)
  - Se vídeo/Reel: transcrição via Whisper + descrição do conteúdo
  - Classificação por tipo de conteúdo (imagem, carrossel, vídeo)
  - Sumário analítico

Uso:
  python analisar_posts_seletivos.py

Requer: dados de metadata geral + mídia baixada via download_seletivo.py
"""

import json
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

# Perfis e shortcodes
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
MEDIA_DIR = Path("media_seletivo")


def carregar_posts_metadata(profile_name):
    """Carrega metadata geral dos posts de um perfil."""
    path = DATA_DIR / profile_name / "posts_metadata.json"
    if not path.exists():
        print(f"AVISO: {path} não encontrado")
        return {}
    with open(path, encoding="utf-8") as f:
        posts = json.load(f)
    return {p["shortcode"]: p for p in posts if p.get("shortcode")}


def carregar_profile(profile_name):
    """Carrega metadata do perfil."""
    path = DATA_DIR / profile_name / "profile_metadata.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def carregar_posts_seletivos():
    """Carrega metadata dos posts baixados seletivamente."""
    path = MEDIA_DIR / "posts_seletivos_metadata.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        posts = json.load(f)
    return {p["shortcode"]: p for p in posts if p.get("shortcode")}


def transcrever_audio(video_path, model_size="base"):
    """Transcreve áudio de um vídeo usando Whisper."""
    import whisper
    
    print(f"  Transcrevendo {video_path.name} com Whisper ({model_size})...")
    model = whisper.load_model(model_size)
    result = model.transcribe(str(video_path), language="pt", fp16=False)
    
    return {
        "text": result["text"].strip(),
        "segments": [
            {
                "start": s["start"],
                "end": s["end"],
                "text": s["text"].strip(),
            }
            for s in result.get("segments", [])
        ],
        "language": result.get("language", "pt"),
        "model": model_size,
    }


def encontrar_video(shortcode, profile_name):
    """Encontra arquivo de vídeo baixado para um shortcode."""
    # Buscar no diretório do perfil
    profile_dir = MEDIA_DIR / profile_name
    if not profile_dir.exists():
        return None
    
    # Padrões do instaloader: UTC_date_shortcode.mp4 ou similar
    for ext in [".mp4", ".MP4"]:
        candidates = list(profile_dir.glob(f"*{shortcode}*{ext}"))
        if candidates:
            return candidates[0]
    
    # Buscar recursivamente
    for ext in [".mp4", ".MP4"]:
        candidates = list(MEDIA_DIR.rglob(f"*{shortcode}*{ext}"))
        if candidates:
            return candidates[0]
    
    return None


def encontrar_imagem(shortcode, profile_name):
    """Encontra arquivo de imagem baixado para um shortcode."""
    profile_dir = MEDIA_DIR / profile_name
    if not profile_dir.exists():
        return None
    
    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG"]:
        candidates = list(profile_dir.glob(f"*{shortcode}*{ext}"))
        if candidates:
            return candidates[0]
    
    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG"]:
        candidates = list(MEDIA_DIR.rglob(f"*{shortcode}*{ext}"))
        if candidates:
            return candidates[0]
    
    return None


def limpar_caption(caption):
    """Limpa formatação de caption do Instagram."""
    if not caption:
        return ""
    # Remover múltiplos espaços
    text = re.sub(r"\s+", " ", caption.strip())
    return text


def extrair_temas(caption, hashtags):
    """Extrai temas principais de caption + hashtags."""
    temas = set()
    # Mapeamento de hashtags para temas
    tema_map = {
        "racismo": "racismo",
        "racismoambiental": "racismo ambiental",
        "feminismonegro": "feminismo negro",
        "trabalhodoméstico": "trabalho doméstico",
        "trabalhodomestico": "trabalho doméstico",
        "trabalhadorasdomésticas": "trabalhadoras domésticas",
        "trabalhadorasdomesticas": "trabalhadoras domésticas",
        "dereitos": "direitos",
        "direitosdastrabalhadoras": "direitos das trabalhadoras",
        "direitoshumanos": "direitos humanos",
        "direitostrabalhistas": "direitos trabalhistas",
        "fenatrad": "FENATRAD",
        "pretarara": "Preta Rara",
        "pesadona": "pesadona",
        "beembonita": "Bem Bonita",
        "sonialivre": "Lei Sônia Maria",
        "essenciaissãonossosdireitos": "essenciais são nossos direitos",
        "trabalhodigno": "trabalho digno",
        "domestica": "doméstica",
        "doméstica": "doméstica",
        "diarista": "diarista",
        "libertemrafaelbraga": "Libertem Rafael Braga",
    }
    
    for tag in (hashtags or []):
        tag_clean = tag.lower().replace("#", "").replace("-", "").replace("_", "").replace("ó", "o").replace("á", "a").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ú", "u").replace("ã", "a").replace("ç", "c")
        if tag_clean in tema_map:
            temas.add(tema_map[tag_clean])
    
    # Temas do caption
    caption_lower = (caption or "").lower()
    if "racismo" in caption_lower or "racista" in caption_lower:
        temas.add("racismo")
    if "trabalho doméstico" in caption_lower or "trabalhadora doméstica" in caption_lower:
        temas.add("trabalho doméstico")
    if "direito" in caption_lower:
        temas.add("direitos")
    if "violência" in caption_lower or "violencia" in caption_lower:
        temas.add("violência")
    if "feminicídio" in caption_lower or "feminicidio" in caption_lower:
        temas.add("feminicídio")
    if "assédio" in caption_lower or "assedio" in caption_lower:
        temas.add("assédio")
    if "lei" in caption_lower:
        temas.add("legislação")
    if "união" in caption_lower or "sindicato" in caption_lower or "federação" in caption_lower:
        temas.add("organização sindical")
    if "mei" in caption_lower or "microempreendedor" in caption_lower:
        temas.add("MEI/precarização")
    
    return sorted(temas)


def gerar_analise():
    """Gera análise detalhada dos posts selecionados."""
    linhas = []
    
    linhas.append("# Análise Detalhada dos Posts Selecionados")
    linhas.append(f"\nGerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    linhas.append(f"\nTCC: **A construção de imagens acerca de trabalhadoras domésticas a partir do Instagram**")
    linhas.append(f"Aluna: Bianca Souza | Orientador: Eric Brasil Nepomuceno (UNILAB)")
    linhas.append(f"\n---")
    
    # Carregar dados
    todos_posts = {}
    posts_seletivos = carregar_posts_seletivos()
    
    for profile_name, shortcodes in PERFIS_SHORTCODES.items():
        profile = carregar_profile(profile_name)
        posts_geral = carregar_posts_metadata(profile_name)
        
        linhas.append(f"\n## @{profile_name}")
        if profile:
            linhas.append(f"\n**Perfil**: {profile.get('full_name', 'N/A')}")
            linhas.append(f"- Seguidores: {profile.get('followers', 'N/A')}")
            linhas.append(f"- Bio: {profile.get('biography', 'N/A')}")
            linhas.append(f"- URL: {profile.get('external_url', 'N/A')}")
        
        linhas.append(f"\n### Posts Selecionados ({len(shortcodes)} posts)")
        
        for i, shortcode in enumerate(shortcodes, 1):
            # Buscar metadata do post
            post_data = posts_geral.get(shortcode) or posts_seletivos.get(shortcode)
            
            if not post_data:
                linhas.append(f"\n#### {i}. `{shortcode}` — METADATA NÃO ENCONTRADA")
                linhas.append(f"Post ainda não baixado. Rode `download_seletivo.py` primeiro.")
                continue
            
            # Dados básicos
            data_str = post_data.get("date_utc", "")[:10] if post_data.get("date_utc") else "N/A"
            tipo = "Vídeo/Reel" if post_data.get("is_video") else ("Carrossel" if post_data.get("typename") == "GraphSidecar" else "Imagem")
            likes = post_data.get("likes", 0)
            caption = post_data.get("caption", "")
            caption_clean = limpar_caption(caption)
            hashtags = post_data.get("caption_hashtags", [])
            mentions = post_data.get("caption_mentions", [])
            video_views = post_data.get("video_view_count")
            video_duration = post_data.get("video_duration")
            location = post_data.get("location")
            tagged = post_data.get("tagged_users", [])
            is_sponsored = post_data.get("is_sponsored", False)
            
            # Temas
            temas = extrair_temas(caption, hashtags)
            
            linhas.append(f"\n#### {i}. `{shortcode}` — {data_str}")
            linhas.append(f"")
            linhas.append(f"- **Tipo**: {tipo}")
            linhas.append(f"- **Likes**: {likes:,}")
            if video_views is not None:
                linhas.append(f"- **Views**: {video_views:,}")
            if video_duration is not None:
                dur_min = int(video_duration // 60)
                dur_seg = int(video_duration % 60)
                linhas.append(f"- **Duração**: {dur_min}:{dur_seg:02d}")
            if location:
                linhas.append(f"- **Localização**: {location}")
            if is_sponsored:
                linhas.append(f"- **Patrocinado**: Sim")
            if tagged:
                linhas.append(f"- **Marcados**: {', '.join(tagged)}")
            
            # URL
            linhas.append(f"- **URL**: https://instagram.com/p/{shortcode}")
            
            # Temas identificados
            if temas:
                linhas.append(f"- **Temas**: {', '.join(temas)}")
            
            # Legenda
            if caption_clean:
                # Truncar legenda muito longa para o relatório
                if len(caption_clean) > 500:
                    linhas.append(f"- **Legenda** (truncada): \"{caption_clean[:500]}...\"")
                else:
                    linhas.append(f"- **Legenda**: \"{caption_clean}\"")
                linhas.append(f"- **Comprimento da legenda**: {len(caption_clean)} caracteres")
            else:
                linhas.append(f"- **Legenda**: (sem legenda)")
            
            # Hashtags
            if hashtags:
                linhas.append(f"- **Hashtags** ({len(hashtags)}): {' '.join(hashtags[:20])}")
                if len(hashtags) > 20:
                    linhas.append(f"  - ... e mais {len(hashtags) - 20} hashtags")
            
            # Menções
            if mentions:
                linhas.append(f"- **Menções**: {', '.join(mentions)}")
            
            # Transcrição de vídeo
            if post_data.get("is_video"):
                video_file = encontrar_video(shortcode, profile_name)
                if video_file and video_file.exists():
                    linhas.append(f"- **Arquivo de vídeo**: `{video_file.name}`")
                    try:
                        transcricao = transcrever_audio(video_file)
                        if transcricao["text"]:
                            linhas.append(f"- **Transcrição**: \"{transcricao['text']}\"")
                            if transcricao.get("segments") and len(transcricao["segments"]) > 1:
                                linhas.append(f"  - Segmentos: {len(transcricao['segments'])}")
                                linhas.append(f"  - Transcrição segmentada:")
                                for seg in transcricao["segments"]:
                                    linhas.append(f"    - [{seg['start']:.1f}s – {seg['end']:.1f}s] {seg['text']}")
                            linhas.append(f"  - Idioma detectado: {transcricao.get('language', 'N/A')}")
                            linhas.append(f"  - Modelo Whisper: {transcricao.get('model', 'N/A')}")
                    except Exception as e:
                        linhas.append(f"- **Transcrição**: ERRO — {type(e).__name__}: {e}")
                        linhas.append(f"  Para transcrever manualmente: `python -c \"import whisper; m=whisper.load_model('base'); r=m.transcribe('{video_file}', language='pt'); print(r['text'])\"`")
                else:
                    linhas.append(f"- **Transcrição**: vídeo não baixado. Rode `download_seletivo.py` primeiro.")
            
            # Classificação de conteúdo
            if any(word in (caption or "").lower() for word in ["denúncia", "denuncia", "alerta", "gatilho", "violência", "violencia", "assédio", "assedio"]):
                linhas.append(f"- **Classificação de conteúdo**: ⚠️ Conteúdo sensível (denúncia/alerta)")
            
            # Contexto do post (posição no perfil)
            # Buscar no metadata geral quantos posts existem antes/depois
            
            linhas.append(f"")
    
    # --- Seção: Análise Comparativa ---
    linhas.append(f"\n---")
    linhas.append(f"\n## Análise Comparativa")
    
    # Contar tipos
    total_videos = 0
    total_imagens = 0
    total_carrosseis = 0
    total_likes = 0
    all_temas = []
    all_hashtags = []
    
    for profile_name, shortcodes in PERFIS_SHORTCODES.items():
        posts_geral = carregar_posts_metadata(profile_name)
        for sc in shortcodes:
            p = posts_geral.get(sc, {})
            if not p:
                continue
            if p.get("is_video"):
                total_videos += 1
            elif p.get("typename") == "GraphSidecar":
                total_carrosseis += 1
            else:
                total_imagens += 1
            total_likes += p.get("likes", 0)
            all_temas.extend(extrair_temas(p.get("caption"), p.get("caption_hashtags")))
            all_hashtags.extend(p.get("caption_hashtags", []))
    
    linhas.append(f"\n### Visão Geral dos 10 Posts Selecionados")
    linhas.append(f"- **Total**: {len(PERFIS_SHORTCODES['euempregadadomestica']) + len(PERFIS_SHORTCODES['fenatrad.br'])} posts")
    linhas.append(f"- **Imagens**: {total_imagens}, **Carrosseis**: {total_carrosseis}, **Vídeos/Reels**: {total_videos}")
    linhas.append(f"- **Total de likes**: {total_likes:,}")
    linhas.append(f"- **Temas recorrentes**: {', '.join(Counter(all_temas).most_common(10).keys()) if all_temas else 'N/A'}")
    linhas.append(f"- **Hashtags mais usadas**: {', '.join([f'#{h}' for h, _ in Counter(all_hashtags).most_common(10)]) if all_hashtags else 'N/A'}")
    
    # Notas metodológicas
    linhas.append(f"\n---")
    linhas.append(f"\n## Notas Metodológicas")
    linhas.append(f"\n- **Coleta**: Instaloader 4.15.1 com patch do doc_id GraphQL (issue #2695)")
    linhas.append(f"- **Data da coleta**: 02-03/06/2026")
    linhas.append(f"- **Transcrição de vídeos**: OpenAI Whisper (modelo base, língua portuguesa)")
    linhas.append(f"- **Limitações**: Comentários não foram coletados (requer login + rate limit severo). Dados de views podem estar incompletos para vídeos mais antigos.")
    
    # Salvar
    analise_path = Path("analise_posts_selecionados.md")
    with open(analise_path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    
    print(f"Análise salva em: {analise_path}")
    return analise_path


if __name__ == "__main__":
    gerar_analise()