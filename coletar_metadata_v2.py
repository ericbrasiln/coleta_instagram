#!/usr/bin/env python3
"""
Coleta de METADATA de perfis do Instagram via Instaloader.
Versão 2 — com tratamento de erros para mudanças na API do Instagram.
SEM download de imagens — apenas métricas e textos.

Uso:
  1. Login:     python coletar_metadata_v2.py --login SEU_USERNAME
  2. Coletar:  python coletar_metadata_v2.py SEU_USERNAME euempregadadomestica fenatrad.br
"""

import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

import instaloader


def fazer_login(username: str):
    L = instaloader.Instaloader()
    L.interactive_login(username)
    L.save_session_to_file()
    print(f"Sessão salva para @{username}")
    L.context.close()


def safe_get(obj, attr, default=None):
    """Get attribute safely, returning default on any error."""
    try:
        val = getattr(obj, attr)
        return val if val is not None else default
    except Exception:
        return default


def coletar_perfil(username: str, login_user: str):
    out_dir = Path("dados") / username
    out_dir.mkdir(parents=True, exist_ok=True)

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,   # desabilitado para ser mais leve
        save_metadata=True,
        compress_json=False,
        post_metadata_txt_pattern="",
    )

    try:
        L.load_session_from_file(login_user)
        print(f"Sessão carregada para @{login_user}")
    except FileNotFoundError:
        print(f"ERRO: Nenhuma sessão encontrada para @{login_user}")
        print("Rode primeiro: python coletar_metadata_v2.py --login SEU_USERNAME")
        sys.exit(1)

    print(f"\n[{datetime.now().isoformat()}] Coletando metadata: @{username}")

    # Tentativa de obter o profile
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"ERRO: Perfil @{username} não existe.")
        L.context.close()
        return None
    except instaloader.exceptions.LoginRequiredException:
        print(f"ERRO: Perfil @{username} requer login.")
        L.context.close()
        return None
    except Exception as e:
        print(f"ERRO ao acessar @{username}: {type(e).__name__}: {e}")
        L.context.close()
        return None

    # Metadata do perfil — acessar cada campo com segurança
    profile_data = {
        "username": safe_get(profile, "username", username),
        "full_name": safe_get(profile, "full_name"),
        "biography": safe_get(profile, "biography"),
        "followers": safe_get(profile, "followers"),
        "followees": safe_get(profile, "followees"),
        "mediacount": safe_get(profile, "mediacount"),
        "is_business_account": safe_get(profile, "is_business_account"),
        "business_category_name": safe_get(profile, "business_category_name"),
        "is_verified": safe_get(profile, "is_verified"),
        "is_private": safe_get(profile, "is_private"),
        "external_url": safe_get(profile, "external_url"),
        "has_highlight_reels": safe_get(profile, "has_highlight_reels"),
        "userid": safe_get(profile, "userid"),
        "profile_pic_url": safe_get(profile, "profile_pic_url"),
        "collected_at": datetime.now().isoformat(),
    }

    # Se biography falhou, tentar pelo _node (dados brutos)
    if profile_data["biography"] is None:
        try:
            node = profile._node
            profile_data["biography"] = node.get("biography", None)
        except Exception:
            pass

    profile_json = out_dir / "profile_metadata.json"
    with open(profile_json, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

    print(f"  Nome: {profile_data.get('full_name', 'N/A')}")
    print(f"  Seguidores: {profile_data.get('followers', 'N/A')}")
    print(f"  Seguindo: {profile_data.get('followees', 'N/A')}")
    print(f"  Posts: {profile_data.get('mediacount', 'N/A')}")

    # Coletar metadata dos posts
    posts_data = []
    total = profile_data.get("mediacount", 0)
    print(f"  Coletando metadata de posts...")

    try:
        posts_iter = profile.get_posts()
    except Exception as e:
        print(f"  ERRO ao obter iterador de posts: {type(e).__name__}: {e}")
        print(f"  Tentando abordagem alternativa...")
        # Fallback: tentar obter posts via get_profile_posts
        try:
            posts_iter = L.context.get_posts(username)
        except Exception as e2:
            print(f"  ERRO na abordagem alternativa: {e2}")
            L.context.close()
            return {"profile": profile_data, "posts_count": 0}

    error_count = 0
    max_consecutive_errors = 10

    for i, post in enumerate(posts_iter):
        try:
            post_info = {
                "shortcode": safe_get(post, "shortcode"),
                "mediaid": safe_get(post, "mediaid"),
                "date_utc": safe_get(post, "date_utc").isoformat() if safe_get(post, "date_utc") else None,
                "caption": safe_get(post, "caption"),
                "caption_hashtags": safe_get(post, "caption_hashtags", []),
                "caption_mentions": safe_get(post, "caption_mentions", []),
                "likes": safe_get(post, "likes"),
                "is_video": safe_get(post, "is_video"),
                "video_view_count": safe_get(post, "video_view_count") if safe_get(post, "is_video") else None,
                "video_duration": safe_get(post, "video_duration") if safe_get(post, "is_video") else None,
                "typename": safe_get(post, "typename"),
                "owner_username": safe_get(post, "owner_username"),
                "url": safe_get(post, "url"),
                "location": str(safe_get(post, "location")) if safe_get(post, "location") else None,
                "tagged_users": safe_get(post, "tagged_users", []),
                "is_sponsored": safe_get(post, "is_sponsored"),
                "is_pinned": safe_get(post, "is_pinned"),
                "title": safe_get(post, "title"),
                "accessibility_caption": safe_get(post, "accessibility_caption"),
            }
            posts_data.append(post_info)
            error_count = 0  # reset on success

        except Exception as e:
            error_count += 1
            print(f"  Warn: erro no post {i+1}: {type(e).__name__}: {e}")
            if error_count >= max_consecutive_errors:
                print(f"  Muitos erros consecutivos. Parando.")
                break
            time.sleep(5)
            continue

        # Progresso
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}] posts processados...")
            time.sleep(10)  # pausa entre batches
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}] Pausa longa (60s)...")
            time.sleep(60)

    # Salvar posts
    posts_json = out_dir / "posts_metadata.json"
    with open(posts_json, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)
    print(f"\n  Concluído: {len(posts_data)} posts coletados para @{username}")
    print(f"  Arquivos: {profile_json.name}, {posts_json.name}")

    L.context.close()
    return {"profile": profile_data, "posts_count": len(posts_data)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta de metadata do Instagram (sem imagens)")
    parser.add_argument("--login", help="Fazer login e salvar sessão")
    parser.add_argument("args", nargs="*", help="[login_user] perfil1 [perfil2 ...]")

    args = parser.parse_args()

    if args.login:
        fazer_login(args.login)
    elif len(args.args) >= 2:
        login_user = args.args[0]
        perfis = args.args[1:]

        resultados = {}
        for i, perfil in enumerate(perfis):
            result = coletar_perfil(perfil, login_user)
            if result:
                resultados[perfil] = result
            if i < len(perfis) - 1:
                print(f"\nPausa de 120s antes do próximo perfil...")
                time.sleep(120)

        # Resumo final
        print("\n" + "=" * 50)
        print("RESUMO DA COLETA")
        print("=" * 50)
        for perfil, info in resultados.items():
            p = info.get("profile", {})
            print(f"\n@{perfil}")
            print(f"  Seguidores: {p.get('followers', 'N/A')}")
            print(f"  Posts coletados: {info.get('posts_count', 'N/A')}")
    else:
        print("Uso:")
        print("  Login:    python coletar_metadata_v2.py --login SEU_USERNAME")
        print("  Coletar:  python coletar_metadata_v2.py SEU_USERNAME euempregadadomestica fenatrad.br")
        sys.exit(1)