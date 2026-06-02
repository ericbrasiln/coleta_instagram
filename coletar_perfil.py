#!/usr/bin/env python3
"""
Coleta de dados de perfis do Instagram via Instaloader.
Sem login — apenas posts públicos (metadata JSON + imagens).
Uso: python coletar_perfil.py <perfil1> <perfil2> ...
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

import instaloader


def coletar_perfil(username: str):
    """Coleta dados de um perfil Instagram público."""
    out_dir = Path("dados") / username
    out_dir.mkdir(parents=True, exist_ok=True)

    L = instaloader.Instaloader(
        download_videos=False,          # sem vídeos para economizar
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,         # requer login
        save_metadata=True,              # salva JSON com metadata
        compress_json=False,             # JSON legível
        post_metadata_txt_pattern="",    # não cria .txt extra
    )

    # Direcionar saída para o diretório do perfil
    L.dirname_pattern = str(out_dir) + "/{target}"
    L.filename_pattern = out_dir.name + "/{date_utc}_UTC"

    print(f"[{datetime.now().isoformat()}] Iniciando coleta: {username}")
    print(f"  Destino: {out_dir}")

    try:
        profile = instaloader.Profile.from_username(L.context, username)

        # Salvar metadata do perfil
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
        print(f"  Perfil salvo: {profile.username}")
        print(f"  Bio: {profile.biography[:80]}...")
        print(f"  Seguidores: {profile.followers}")
        print(f"  Seguindo: {profile.followees}")
        print(f"  Posts: {profile.mediacount}")

    except instaloader.exceptions.ProfileNotExistsException:
        print(f"  ERRO: Perfil @{username} não existe.")
        return None
    except instaloader.exceptions.LoginRequiredException:
        print(f"  ERRO: Perfil @{username} requer login para acessar.")
        return None

    # Coletar posts
    posts_data = []
    total = profile.mediacount
    print(f"  Coletando {total} posts...")

    for i, post in enumerate(profile.get_posts()):
        post_info = {
            "shortcode": post.shortcode,
            "mediaid": post.mediaid,
            "date_utc": post.date_utc.isoformat(),
            "date_local": post.date_local.isoformat() if post.date_local else None,
            "caption": post.caption,
            "caption_hashtags": post.caption_hashtags,
            "caption_mentions": post.caption_mentions,
            "likes": post.likes,
            "is_video": post.is_video,
            "video_view_count": post.video_view_count if post.is_video else None,
            "video_duration": post.video_duration if post.is_video else None,
            "typename": post.typename,
            "owner_username": post.owner_username,
            "owner_id": post.owner_id,
            "url": post.url,
            "location": str(post.location) if post.location else None,
            "tagged_users": post.tagged_users,
            "is_sponsored": post.is_sponsored,
            "is_pinned": post.is_pinned,
            "accessibility_caption": post.accessibility_caption,
        }
        posts_data.append(post_info)

        # Download da imagem (não de vídeo)
        if not post.is_video:
            try:
                L.download_pic(
                    username=post.owner_username,
                    url=post.url,
                    date_utc=post.date_utc,
                    filename_suffix=None,
                )
            except Exception as e:
                print(f"    Warn: erro ao baixar imagem {post.shortcode}: {e}")

        # Rate limiting: pausa a cada 30 posts
        if (i + 1) % 30 == 0:
            wait = 60
            print(f"  [{i+1}/{total}] Pausa de {wait}s para evitar rate limit...")
            time.sleep(wait)
        elif (i + 1) % 10 == 0:
            # Pausa curta a cada 10 posts
            time.sleep(5)

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{total}] posts processados...")

    # Salvar metadata dos posts
    posts_json = out_dir / "posts_metadata.json"
    with open(posts_json, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)
    print(f"  Metadata de {len(posts_data)} posts salva em {posts_json}")

    return profile_data, posts_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python coletar_perfil.py <perfil1> [perfil2] ...")
        sys.exit(1)

    resultados = {}
    for perfil in sys.argv[1:]:
        result = coletar_perfil(perfil)
        if result:
            resultados[perfil] = {
                "profile": result[0],
                "posts_count": len(result[1]),
            }
        # Pausa entre perfis
        if perfil != sys.argv[-1]:
            print("\nPausa de 120s entre perfis...")
            time.sleep(120)

    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DA COLETA")
    print("=" * 50)
    for perfil, info in resultados.items():
        print(f"\n@{perfil}")
        print(f"  Followers: {info['profile']['followers']}")
        print(f"  Posts coletados: {info['posts_count']}")