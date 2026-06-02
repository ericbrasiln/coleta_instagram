#!/usr/bin/env python3
"""
Coleta de METADATA de perfis do Instagram via Instaloader.
SEM download de imagens — apenas métricas e textos.
REQUER LOGIN — rodar no computador local com IP residencial.

Uso:
  1. Login:     python coletar_metadata.py --login SEU_USERNAME
  2. Coletar:  python coletar_metadata.py SEU_USERNAME euempregadadomestica fenatrad.br
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


def coletar_perfil(username: str, login_user: str):
    out_dir = Path("dados") / username
    out_dir.mkdir(parents=True, exist_ok=True)

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=True,
        save_metadata=True,
        compress_json=False,
        post_metadata_txt_pattern="",
    )

    try:
        L.load_session_from_file(login_user)
        print(f"Sessão carregada para @{login_user}")
    except FileNotFoundError:
        print(f"ERRO: Nenhuma sessão encontrada para @{login_user}")
        print("Rode primeiro: python coletar_metadata.py --login SEU_USERNAME")
        sys.exit(1)

    print(f"\n[{datetime.now().isoformat()}] Coletando metadata: @{username}")

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

    # Metadata do perfil
    profile_data = {
        "username": profile.username,
        "full_name": profile.full_name,
        "biography": profile.biography,
        "followers": profile.followers,
        "followees": profile.followees,
        "mediacount": profile.mediacount,
        "is_business_account": profile.is_business_account,
        "business_category_name": profile.business_category_name,
        "is_verified": profile.is_verified,
        "is_private": profile.is_private,
        "external_url": profile.external_url,
        "has_highlight_reels": profile.has_highlight_reels,
        "userid": profile.userid,
        "profile_pic_url": profile.profile_pic_url,
        "collected_at": datetime.now().isoformat(),
    }

    profile_json = out_dir / "profile_metadata.json"
    with open(profile_json, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

    print(f"  Nome: {profile.full_name}")
    print(f"  Seguidores: {profile.followers}")
    print(f"  Seguindo: {profile.followees}")
    print(f"  Posts: {profile.mediacount}")

    # Coletar metadata dos posts (sem baixar mídia)
    posts_data = []
    total = profile.mediacount
    print(f"  Coletando metadata de {total} posts...")

    for i, post in enumerate(profile.get_posts()):
        post_info = {
            "shortcode": post.shortcode,
            "mediaid": post.mediaid,
            "date_utc": post.date_utc.isoformat(),
            "caption": post.caption,
            "caption_hashtags": post.caption_hashtags,
            "caption_mentions": post.caption_mentions,
            "likes": post.likes,
            "is_video": post.is_video,
            "video_view_count": post.video_view_count if post.is_video else None,
            "video_duration": post.video_duration if post.is_video else None,
            "typename": post.typename,
            "owner_username": post.owner_username,
            "url": post.url,
            "location": str(post.location) if post.location else None,
            "tagged_users": post.tagged_users,
            "is_sponsored": post.is_sponsored,
            "is_pinned": post.is_pinned,
            "title": post.title,
            "accessibility_caption": post.accessibility_caption,
        }
        posts_data.append(post_info)

        # Rate limiting (sem download = mais leve, mas ainda precisa de cuidado)
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{total}]...")
            time.sleep(10)  # pausa curta
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{total}] Pausa longa...")
            time.sleep(60)  # pausa longa

    # Salvar posts
    posts_json = out_dir / "posts_metadata.json"
    with open(posts_json, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)
    print(f"  Metadata de {len(posts_data)} posts salva em {posts_json}")

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

        for i, perfil in enumerate(perfis):
            coletar_perfil(perfil, login_user)
            if i < len(perfis) - 1:
                print(f"\nPausa de 180s antes do próximo perfil...")
                time.sleep(180)
    else:
        print("Uso:")
        print("  Login:    python coletar_metadata.py --login SEU_USERNAME")
        print("  Coletar:  python coletar_metadata.py SEU_USERNAME euempregadadomestica fenatrad.br")
        sys.exit(1)