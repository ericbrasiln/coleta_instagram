#!/usr/bin/env python3
"""
Consolida os JSONs do download seletivo (formato Instaloader)
em um formato padrão para análise.

Os JSONs do Instaloader têm estrutura: {"instaloader": {...}, "node": {...}}
com campos aninhados diferentes do nosso formato de metadata.

Uso: python consolidar_metadata.py
"""

import json
import glob
import os
from pathlib import Path
from datetime import datetime

DADOS_DIR = Path("dados")

# Perfis e shortcodes selecionados
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
    "sindomesticobahia": [
        "DUn-CpRkT_N",
    ],
    "conlactraho1": [
        "DSLiLOXkV5z",
    ],
}


def parse_instaloader_json(filepath):
    """Parseia JSON do Instaloader (formato com 'node' aninhado)."""
    with open(filepath, encoding="utf-8") as f:
        d = json.load(f)
    
    n = d.get("node", d)
    
    # Caption
    caption_text = ""
    caption_edges = n.get("edge_media_to_caption", {}).get("edges", [])
    if caption_edges:
        caption_text = caption_edges[0].get("node", {}).get("text", "")
    
    # Hashtags e menções da caption
    hashtags = [w for w in caption_text.split() if w.startswith("#")]
    mentions = [w for w in caption_text.split() if w.startswith("@")]
    
    # Comments
    comments_edges = n.get("edge_media_to_parent_comment", {}).get("edges", [])
    comments = []
    for ce in comments_edges:
        c = ce.get("node", {})
        comments.append({
            "id": c.get("id", ""),
            "owner": c.get("owner", {}).get("username", ""),
            "text": c.get("text", ""),
            "created_at": c.get("created_at", 0),
        })
    
    # Video info
    is_video = n.get("is_video", False)
    video_view_count = n.get("video_view_count", 0) if is_video else None
    video_duration = n.get("video_duration", None) if is_video else None
    
    # Location
    location = None
    loc = n.get("location")
    if loc and isinstance(loc, dict):
        location = loc.get("name", "")
    
    # Tagged users
    tagged = []
    tagged_edges = n.get("edge_media_to_tagged_user", {}).get("edges", [])
    for te in tagged_edges:
        tagged.append(te.get("node", {}).get("user", {}).get("username", ""))
    
    return {
        "shortcode": n.get("shortcode", ""),
        "mediaid": n.get("id", ""),
        "date_utc": n.get("taken_at_timestamp", ""),
        "typename": n.get("__typename", ""),
        "caption": caption_text,
        "caption_hashtags": hashtags,
        "caption_mentions": mentions,
        "likes": n.get("edge_media_preview_like", {}).get("count", 0),
        "is_video": is_video,
        "video_view_count": video_view_count,
        "video_duration": video_duration,
        "owner_username": n.get("owner", {}).get("username", ""),
        "owner_id": n.get("owner", {}).get("id", ""),
        "location": location,
        "tagged_users": tagged,
        "comments_count": n.get("edge_media_to_parent_comment", {}).get("count", 0),
        "comments": comments,
        "url": n.get("display_url", ""),
        "accessibility_caption": n.get("accessibility_caption"),
        "source": "download_seletivo",
    }


def load_comments_file(filepath):
    """Lê arquivo de comments separado do Instaloader."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        # Comments podem vir em formato de lista
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Formato com edges
            edges = data.get("edges", [])
            return [e.get("node", {}) for e in edges]
        return []
    except Exception:
        return []


def consolidate():
    """Consolida metadata de todas as fontes."""
    all_seletivos = []
    
    for profile_name, shortcodes in PERFIS_SHORTCODES.items():
        profile_dir = DADOS_DIR / profile_name / profile_name
        
        # Carregar metadata geral (se existe)
        geral_path = DADOS_DIR / profile_name / "posts_metadata.json"
        geral_data = {}
        if geral_path.exists():
            with open(geral_path, encoding="utf-8") as f:
                posts_geral = json.load(f)
                geral_data = {p["shortcode"]: p for p in posts_geral if p.get("shortcode")}
        
        # Carregar profile metadata (se existe)
        profile_meta_path = DADOS_DIR / profile_name / "profile_metadata.json"
        profile_meta = {}
        if profile_meta_path.exists():
            with open(profile_meta_path, encoding="utf-8") as f:
                profile_meta = json.load(f)
        
        for shortcode in shortcodes:
            post_info = None
            
            # 1. Tentar JSON individual do download seletivo
            json_files = sorted(glob.glob(str(DADOS_DIR / "**" / f"*{shortcode}*.json")))
            for jf in json_files:
                if "comments" in os.path.basename(jf):
                    continue
                try:
                    p = parse_instaloader_json(jf)
                    if p.get("shortcode") == shortcode:
                        # Adicionar comments se existir arquivo separado
                        comments_file = jf.replace(".json", "_comments.json")
                        comments = load_comments_file(comments_file)
                        if comments:
                            p["comments"] = comments
                        
                        # Verificar se existe vídeo/imagem baixado
                        base = jf.replace(".json", "")
                        video_file = base + ".mp4" if os.path.exists(base + ".mp4") else None
                        image_file = base + ".jpg" if os.path.exists(base + ".jpg") else None
                        p["has_video_file"] = video_file is not None
                        p["has_image_file"] = image_file is not None
                        p["video_file"] = video_file
                        p["image_file"] = image_file
                        
                        post_info = p
                        break
                except Exception as e:
                    print(f"  Erro lendo {jf}: {e}")
            
            # 2. Fallback: metadata geral
            if not post_info and shortcode in geral_data:
                post_info = dict(geral_data[shortcode])
                post_info["source"] = "metadata_geral"
                post_info["has_video_file"] = False
                post_info["has_image_file"] = False
                post_info["comments"] = []
            
            if post_info:
                post_info["profile"] = profile_name
                all_seletivos.append(post_info)
            else:
                print(f"  AVISO: shortcode {shortcode} de @{profile_name} não encontrado em nenhuma fonte")
                all_seletivos.append({
                    "shortcode": shortcode,
                    "profile": profile_name,
                    "source": "missing",
                })
    
    # Salvar consolidado
    out_path = DADOS_DIR / "posts_selecionados_consolidado.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_seletivos, f, ensure_ascii=False, indent=2)
    
    print(f"\nConsolidado salvo: {out_path}")
    print(f"Total de posts: {len(all_seletivos)}")
    
    # Resumo
    for p in all_seletivos:
        sc = p.get("shortcode", "?")
        profile = p.get("profile", "?")
        likes = p.get("likes", "?")
        tipo = "vídeo" if p.get("is_video") else ("carrossel" if p.get("typename") == "GraphSidecar" else "imagem")
        arquivo = ""
        if p.get("has_video_file"):
            arquivo = " [vídeo baixado]"
        elif p.get("has_image_file"):
            arquivo = " [imagem baixada]"
        print(f"  @{profile} {sc} | likes={likes} | {tipo}{arquivo}")
    
    return all_seletivos


if __name__ == "__main__":
    consolidate()