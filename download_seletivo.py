#!/usr/bin/env python3
"""
Download seletivo de mídia + metadata de posts específicos do Instagram.
Recebe uma lista de shortcodes (URLs ou códigos) e baixa apenas esses posts.

Uso:
  # Login (se ainda não tiver sessão):
  python download_seletivo.py --login SEU_USERNAME

  # Download de posts específicos:
  python download_seletivo.py SEU_USERNAME shortcodes.txt

  # Ou passando shortcodes direto:
  python download_seletivo.py SEU_USERNAME --shortcodes ABC123 DEF456 GHI789

Formato do arquivo shortcodes.txt (um por linha):
  # Qualquer um desses formatos funciona:
  ABC123def
  https://www.instagram.com/p/ABC123def/
  https://www.instagram.com/reel/ABC123def/
"""

import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

import instaloader
from instaloader.instaloadercontext import InstaloaderContext

# Monkey patch para bug do doc_id (issue #2695)
_STALE_DOC_ID = "25980296051578533"
_FIXED_DOC_ID = "27937681195819736"
_EXTRA_VARS = {
    "__relay_internal__pv__PolarisWebSchoolsEnabledrelayprovider": False,
    "enable_integrity_filters": True,
}
_original_doc_id_query = InstaloaderContext.doc_id_graphql_query


def _patched_doc_id_query(self, doc_id, variables, referer=None):
    if doc_id == _STALE_DOC_ID:
        doc_id = _FIXED_DOC_ID
        variables = {**variables, **_EXTRA_VARS}
    return _original_doc_id_query(self, doc_id, variables, referer)


InstaloaderContext.doc_id_graphql_query = _patched_doc_id_query


def extrair_shortcode(texto):
    """Extrai shortcode de URL ou código puro."""
    texto = texto.strip()
    if not texto or texto.startswith("#"):
        return None
    # URL: instagram.com/p/ABC123/ ou instagram.com/reel/ABC123/
    if "instagram.com" in texto:
        parts = texto.split("/")
        for i, part in enumerate(parts):
            if part in ("p", "reel", "tv") and i + 1 < len(parts):
                code = parts[i + 1]
                # Remover query strings
                if "?" in code:
                    code = code.split("?")[0]
                return code
    # Shortcode puro
    return texto


def fazer_login(username: str):
    L = instaloader.Instaloader()
    L.interactive_login(username)
    L.save_session_to_file()
    print(f"Sessão salva para @{username}")
    L.context.close()


def download_seletivo(login_user: str, shortcodes: list, output_dir: str = "media_seletivo"):
    """Baixa mídia + metadata de uma lista de shortcodes."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=True,
        save_metadata=True,
        compress_json=False,
        post_metadata_txt_pattern="",
        dirname_pattern=str(out_path) + "/{profile}",
        filename_pattern="{date_utc}_UTC_{shortcode}",
    )

    try:
        L.load_session_from_file(login_user)
        print(f"Sessão carregada para @{login_user}")
    except FileNotFoundError:
        print(f"ERRO: Nenhuma sessão encontrada para @{login_user}")
        print("Rode primeiro: python download_seletivo.py --login SEU_USERNAME")
        sys.exit(1)

    # Metadata consolidada
    posts_data = []
    sucessos = 0
    falhas = []

    print(f"\nBaixando {len(shortcodes)} posts para '{output_dir}/'")
    print("=" * 50)

    for i, shortcode in enumerate(shortcodes):
        print(f"\n[{i+1}/{len(shortcodes)}] Baixando {shortcode}...")
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            # Metadata do post
            post_info = {
                "shortcode": shortcode,
                "mediaid": post.mediaid,
                "date_utc": post.date_utc.isoformat(),
                "caption": post.caption,
                "caption_hashtags": list(post.caption_hashtags) if post.caption_hashtags else [],
                "caption_mentions": list(post.caption_mentions) if post.caption_mentions else [],
                "likes": post.likes,
                "is_video": post.is_video,
                "video_view_count": post.video_view_count if post.is_video else None,
                "video_duration": post.video_duration if post.is_video else None,
                "typename": post.typename,
                "owner_username": post.owner_username,
                "owner_id": post.owner_id,
                "url": post.url,
                "location": str(post.location) if post.location else None,
                "tagged_users": list(post.tagged_users) if post.tagged_users else [],
                "is_sponsored": post.is_sponsored,
                "title": post.title,
                "accessibility_caption": post.accessibility_caption,
            }

            # Download da mídia
            L.download_post(post, target=post.owner_username)

            # Comments (se disponíveis)
            try:
                comments = []
                for comment in post.get_comments():
                    comments.append({
                        "id": comment.id,
                        "owner": comment.owner.username,
                        "text": comment.text,
                        "created_at": comment.created_at_utc.isoformat(),
                    })
                post_info["comments"] = comments
                post_info["comments_count"] = len(comments)
            except Exception as e:
                print(f"  Warn: não conseguiu baixar comments: {e}")
                post_info["comments"] = []
                post_info["comments_count"] = None

            posts_data.append(post_info)
            sucessos += 1
            print(f"  OK: @{post.owner_username} — {post.likes} likes — \"{(post.caption or '')[:60]}...\"")

        except Exception as e:
            falhas.append({"shortcode": shortcode, "erro": str(e)})
            print(f"  FALHA: {type(e).__name__}: {e}")

        # Rate limiting entre posts
        if i < len(shortcodes) - 1:
            time.sleep(5)

    # Salvar metadata consolidada
    metadata_json = out_path / "posts_seletivos_metadata.json"
    with open(metadata_json, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)

    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DO DOWNLOAD SELETIVO")
    print("=" * 50)
    print(f"Sucessos: {sucessos}/{len(shortcodes)}")
    print(f"Falhas: {len(falhas)}/{len(shortcodes)}")
    if falhas:
        print("\nShortcodes com falha:")
        for f in falhas:
            print(f"  {f['shortcode']}: {f['erro']}")
    print(f"\nMetadata salva em: {metadata_json}")
    print(f"Mídia salva em: {out_path}/<perfil>/")

    L.context.close()
    return posts_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download seletivo de mídia + metadata de posts do Instagram"
    )
    parser.add_argument("--login", help="Fazer login e salvar sessão")
    parser.add_argument("--shortcodes", nargs="+", help="Lista de shortcodes direto na linha de comando")
    parser.add_argument("--output", default="media_seletivo", help="Diretório de saída (default: media_seletivo)")
    parser.add_argument("login_user", nargs="?", help="Username do Instagram (sessão salva)")
    parser.add_argument("shortcodes_file", nargs="?", help="Arquivo com shortcodes (um por linha)")

    args = parser.parse_args()

    if args.login:
        fazer_login(args.login)
    elif args.shortcodes:
        # Shortcodes passados direto na linha de comando
        if not args.login_user:
            print("ERRO: Informe o username do Instagram")
            print("Uso: python download_seletivo.py USERNAME --shortcodes ABC123 DEF456")
            sys.exit(1)
        download_seletivo(args.login_user, args.shortcodes, args.output)
    elif args.shortcodes_file and args.login_user:
        # Ler shortcodes de arquivo
        arquivo = Path(args.shortcodes_file)
        if not arquivo.exists():
            print(f"ERRO: Arquivo não encontrado: {arquivo}")
            sys.exit(1)
        with open(arquivo, encoding="utf-8") as f:
            linhas = f.readlines()
        shortcodes = []
        for linha in linhas:
            code = extrair_shortcode(linha)
            if code:
                shortcodes.append(code)
        print(f"Lidos {len(shortcodes)} shortcodes de {arquivo}")
        download_seletivo(args.login_user, shortcodes, args.output)
    else:
        print("Uso:")
        print("  Login:          python download_seletivo.py --login USERNAME")
        print("  Via arquivo:   python download_seletivo.py USERNAME shortcodes.txt")
        print("  Via argumento: python download_seletivo.py USERNAME --shortcodes ABC123 DEF456")
        print()
        print("Formato do arquivo shortcodes.txt:")
        print("  # Um shortcode ou URL por linha")
        print("  ABC123def")
        print("  https://www.instagram.com/p/ABC123def/")
        print("  https://www.instagram.com/reel/ABC123def/")
        sys.exit(1)