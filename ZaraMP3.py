#!/usr/bin/env python3
"""
YouTube → MP3 Downloader
========================
Como usar:
  1. Instale as dependências (só na primeira vez):
       pip install yt-dlp

  2. Rode o script:
       python youtube-mp3.py

  3. Cole o link do YouTube quando pedir

Funciona no Windows, Mac e Linux.
"""

import subprocess, sys, os, re

# ── Instala/atualiza yt-dlp automaticamente ──────────────────────────
def instalar_ytdlp():
    print("Instalando/atualizando yt-dlp...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                           '--upgrade', 'yt-dlp', '--quiet'])
    print("✅ yt-dlp pronto!\n")

try:
    import yt_dlp
except ImportError:
    instalar_ytdlp()
    import yt_dlp

# ── Helpers ──────────────────────────────────────────────────────────
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║                                                  ║")
    print("║        ███████╗ █████╗ ██████╗  █████╗          ║")
    print("║          ███╔═╝██╔══██╗██╔══██╗██╔══██╗         ║")
    print("║         ███╔╝ ███████║██████╔╝███████║          ║")
    print("║        ███╔╝  ██╔══██║██╔══██╗██╔══██║          ║")
    print("║       ███████╗██║  ██║██║  ██║██║  ██║          ║")
    print("║       ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝         ║")
    print("║                                                  ║")
    print("║          M  P  3     D o w n l o a d e r        ║")
    print("║                                                  ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║                                                  ║")
    print("║     Seja bem-vindo ao  Z A R A  M P 3  !        ║")
    print("║     Seu downloader de musicas favoritas  🎵      ║")
    print("║                                                  ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

def tem_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'],
                       capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def instalar_ffmpeg_windows():
    """Tenta instalar ffmpeg via winget (Windows 10/11)"""
    print("\n⚙️  Tentando instalar ffmpeg automaticamente via winget...")
    try:
        subprocess.run(
            ['winget', 'install', 'Gyan.FFmpeg', '--silent', '--accept-source-agreements'],
            check=True
        )
        print("✅ ffmpeg instalado! Reinicie o script.\n")
        return True
    except Exception:
        return False

def verificar_ffmpeg():
    if tem_ffmpeg():
        return True
    print("\n⚠️  ffmpeg NÃO encontrado!")
    print("   O ffmpeg é necessário para converter para MP3.\n")
    if os.name == 'nt':
        tentar = input("   Tentar instalar automaticamente? (s/n): ").strip().lower()
        if tentar == 's':
            if instalar_ffmpeg_windows():
                return False  # precisa reiniciar
    print("\n   Instale manualmente:")
    print("   Windows → https://www.gyan.dev/ffmpeg/builds/")
    print("             Baixe 'ffmpeg-release-essentials.zip'")
    print("             Extraia e adicione a pasta 'bin' ao PATH")
    print("   Mac     → brew install ffmpeg")
    print("   Linux   → sudo apt install ffmpeg\n")
    input("   Pressione Enter para tentar sem ffmpeg (pode não funcionar)...")
    return False

def escolher_qualidade():
    print("\nQualidade do MP3:")
    print("  1. 320 kbps (melhor qualidade)")
    print("  2. 256 kbps")
    print("  3. 192 kbps")
    print("  4. 128 kbps (padrão, boa qualidade)")
    print("  5.  96 kbps (arquivo menor)")
    print()
    opcao = input("Escolha [1-5] (Enter = 128kbps): ").strip()
    qualidades = {'1':'320','2':'256','3':'192','4':'128','5':'96','':'128'}
    return qualidades.get(opcao, '128')

def progresso(d):
    if d['status'] == 'downloading':
        pct = d.get('_percent_str', '?%').strip()
        vel = d.get('_speed_str', '?').strip()
        eta = d.get('_eta_str', '?').strip()
        print(f"\r   {pct} | {vel} | ETA {eta}    ", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\r   ✅ Áudio baixado! Convertendo para MP3...      ", flush=True)

def montar_opts(pasta, qualidade, playlist=False):
    template = '%(playlist_index)s - %(title)s.%(ext)s' if playlist else '%(title)s.%(ext)s'
    opts = {
        # Usa o extrator nativo sem precisar de JS runtime
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # android não precisa de JS
            }
        },
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': os.path.join(pasta, template),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': qualidade,
        }],
        # Headers que imitam app Android — evita 403
        'http_headers': {
            'User-Agent': (
                'com.google.android.youtube/17.36.4 '
                '(Linux; U; Android 12; GB) gzip'
            ),
        },
        'quiet': False,
        'no_warnings': True,
        'progress_hooks': [progresso],
        'ignoreerrors': playlist,
        # Tenta novamente até 3x em caso de erro de rede
        'retries': 3,
        'fragment_retries': 3,
    }
    # Se não tiver ffmpeg, baixa o melhor áudio disponível sem converter
    if not tem_ffmpeg():
        opts.pop('postprocessors')
        opts['outtmpl'] = os.path.join(pasta, template.replace('.%(ext)s', '_SEM_FFMPEG.%(ext)s'))
        print("\n⚠️  Sem ffmpeg: o arquivo será baixado no formato original (webm/m4a), não MP3.")
    return opts

def baixar(url, qualidade='128', pasta=None):
    if not pasta:
        pasta = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(pasta, exist_ok=True)

    print(f"\n⏳ Iniciando download...")
    print(f"   Qualidade: {qualidade} kbps")
    print(f"   Pasta: {pasta}\n")

    opts = montar_opts(pasta, qualidade)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'arquivo')
            t = titulo[:42]
            p = pasta[:42]
            print("\n")
            print("╔══════════════════════════════════════════════════╗")
            print("║                                                  ║")
            print("║   🎵   ARQUIVO BAIXADO COM SUCESSO!   🎵         ║")
            print("║                                                  ║")
            print(f"║   Titulo : {t:<42}  ║")
            print(f"║   Pasta  : {p:<42}  ║")
            print("║                                                  ║")
            print("║          Aproveite sua musica!  🎧               ║")
            print("║                                                  ║")
            print("╚══════════════════════════════════════════════════╝")
            print()
            return True
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        print(f"\n❌ Erro: {msg}")
        # Dicas específicas para erros comuns
        if '403' in msg or 'Forbidden' in msg:
            print("\n💡 Dica: Tente atualizar o yt-dlp:")
            print("   pip install --upgrade yt-dlp")
        elif 'Private video' in msg:
            print("\n💡 Este vídeo é privado — não é possível baixar.")
        elif 'not available' in msg:
            print("\n💡 Vídeo indisponível no Brasil. Tente outro.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False

def baixar_playlist(url, qualidade, pasta):
    print("\n📋 Baixando playlist completa...\n")
    opts = montar_opts(pasta, qualidade, playlist=True)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        print("\n✅ Playlist concluída!")
    except Exception as e:
        print(f"\n❌ Erro na playlist: {e}")

# ── Main ─────────────────────────────────────────────────────────────
def main():
    limpar_tela()
    banner()

    # Atualiza yt-dlp silenciosamente (importante para evitar 403)
    print("🔄 Verificando atualizações do yt-dlp...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade',
             'yt-dlp', '--quiet'],
            capture_output=True
        )
        print("✅ yt-dlp atualizado!\n")
    except Exception:
        print("   (não foi possível atualizar — continuando)\n")

    verificar_ffmpeg()

    while True:
        print("\nCole o link do YouTube (ou 'sair' para fechar):")
        url = input("🔗 URL: ").strip()

        if url.lower() in ('sair', 'exit', 'quit', 'q', ''):
            if url.lower() in ('sair', 'exit', 'quit', 'q'):
                print("\nAté logo! 👋\n")
                break
            continue

        # Limpa espaços e caracteres inválidos
        url = re.sub(r'\s+', '', url)

        if 'youtube.com' not in url and 'youtu.be' not in url:
            print("❌ Link inválido. Use um link do YouTube.\n")
            continue

        qualidade = escolher_qualidade()

        print(f"\nPasta de destino (Enter = Downloads):")
        pasta = input("📁 Pasta: ").strip().strip('"').strip("'")
        if not pasta:
            pasta = os.path.join(os.path.expanduser('~'), 'Downloads')

        # Detecta playlist
        if 'list=' in url:
            print()
            escolha = input("Playlist detectada. Baixar tudo? (s/n): ").strip().lower()
            if escolha == 's':
                baixar_playlist(url, qualidade, pasta)
            else:
                # Remove parâmetro de playlist, baixa só o vídeo
                url = re.sub(r'&list=[^&]+', '', url)
                url = re.sub(r'\?list=[^&]+&?', '?', url)
                baixar(url, qualidade, pasta)
        else:
            baixar(url, qualidade, pasta)

        print()
        continuar = input("Baixar outro? (s/n): ").strip().lower()
        if continuar != 's':
            print("\nAté logo! 👋\n")
            break

        limpar_tela()
        banner()

if __name__ == '__main__':
    main()

