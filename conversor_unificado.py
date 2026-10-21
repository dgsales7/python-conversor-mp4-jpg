import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

VIDEO_EXT = {'.ts', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.mpeg', '.mpg', '.m4v', '.mp4'}
IMAGE_EXT = {'.png', '.webp', '.bmp', '.tif', '.tiff', '.gif', '.heic', '.heif', '.avif', '.jfif', '.jpeg', '.jpg', '.ico'}


class App:
    def __init__(self, root):
        self.root = root
        root.title('Conversor de Arquivos | MP4 e JPG')
        root.geometry('760x590')
        root.minsize(650, 550)
        self.kind = tk.StringVar(value='video')
        self.source = tk.StringVar()
        self.target = tk.StringVar()
        self.quality = tk.IntVar(value=95)
        self.video_mode = tk.StringVar(value='auto')
        self.busy = False
        self.setup()

    def setup(self):
        frame = ttk.Frame(self.root, padding=22)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='CONVERSOR DE ARQUIVOS', font=('Segoe UI', 19, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Converta vídeos para MP4 ou imagens para JPG').pack(anchor='w', pady=(0, 15))
        choice = ttk.LabelFrame(frame, text='O que deseja converter?', padding=12)
        choice.pack(fill='x')
        ttk.Radiobutton(choice, text='Vídeos → MP4', variable=self.kind, value='video', command=self.update_mode).pack(side='left', padx=16)
        ttk.Radiobutton(choice, text='Imagens → JPG', variable=self.kind, value='image', command=self.update_mode).pack(side='left', padx=16)
        for label, variable in [('PASTA DE ORIGEM', self.source), ('PASTA DE DESTINO', self.target)]:
            ttk.Label(frame, text=label, font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(14, 4))
            row = ttk.Frame(frame)
            row.pack(fill='x')
            ttk.Entry(row, textvariable=variable).pack(side='left', fill='x', expand=True)
            ttk.Button(row, text='Procurar...', command=lambda v=variable: self.browse(v)).pack(side='left', padx=(8, 0))
        self.options = ttk.LabelFrame(frame, text='Configurações', padding=10)
        self.options.pack(fill='x', pady=(16, 10))
        self.update_mode()
        self.progress = ttk.Progressbar(frame, maximum=100, mode='determinate')
        self.progress.pack(fill='x', pady=(10, 8))
        self.status = ttk.Label(frame, text='Aguardando seleção das pastas...')
        self.status.pack(anchor='w')
        self.start_button = ttk.Button(frame, text='INICIAR CONVERSÃO', command=self.start)
        self.start_button.pack(pady=18, ipadx=25, ipady=8)

    def update_mode(self):
        if self.busy:
            return
        for widget in self.options.winfo_children():
            widget.destroy()
        if self.kind.get() == 'video':
            ttk.Radiobutton(self.options, text='Automático: copiar sem perda quando possível', variable=self.video_mode, value='auto').pack(anchor='w')
            ttk.Radiobutton(self.options, text='Alta qualidade: H.264 / AAC (CRF 17)', variable=self.video_mode, value='quality').pack(anchor='w')
        else:
            ttk.Label(self.options, text='Qualidade da imagem JPG:', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            label = ttk.Label(self.options, text=f'Qualidade selecionada: {self.quality.get()}%')
            label.pack(anchor='w')
            tk.Scale(self.options, from_=80, to=100, orient='horizontal', variable=self.quality,
                     resolution=1, length=500, showvalue=True,
                     command=lambda value: label.configure(text=f'Qualidade selecionada: {int(float(value))}%')).pack(fill='x', pady=5)
            ttk.Label(self.options, text='JPG não preserva transparência nem animação.').pack(anchor='w')

    def browse(self, variable):
        if self.busy:
            return
        folder = filedialog.askdirectory()
        if folder:
            variable.set(folder)

    def set_progress(self, label, percent):
        self.root.after(0, lambda: (self.status.configure(text=label), self.progress.configure(value=percent)))

    def start(self):
        if self.busy:
            return
        source, target = Path(self.source.get()), Path(self.target.get())
        if not source.is_dir() or not target.is_dir():
            messagebox.showerror('Pastas inválidas', 'Selecione pastas de origem e destino existentes.')
            return
        source, target = source.resolve(), target.resolve()
        if source == target or source in target.parents:
            messagebox.showerror('Destino inválido', 'Escolha uma pasta de destino fora da pasta de origem.')
            return
        kind = self.kind.get()
        if kind == 'video' and not shutil.which('ffmpeg'):
            messagebox.showerror('FFmpeg ausente', 'Instale o FFmpeg e configure-o no PATH do Windows.')
            return
        extensions = VIDEO_EXT if kind == 'video' else IMAGE_EXT
        files = sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in extensions)
        if not files:
            messagebox.showinfo('Sem arquivos', 'Nenhum arquivo compatível encontrado.')
            return
        self.busy = True
        self.start_button.configure(state='disabled')
        self.progress.configure(value=0)
        args = (files, source, target, kind, self.video_mode.get(), self.quality.get())
        threading.Thread(target=self.run, args=args, daemon=True).start()

    @staticmethod
    def video_convert(source, dest, mode):
        base = ['ffmpeg', '-hide_banner', '-nostdin', '-loglevel', 'error', '-i', str(source), '-map', '0:v:0', '-map', '0:a?']
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        if mode == 'auto':
            result = subprocess.run(base + ['-c', 'copy', '-movflags', '+faststart', str(dest)], capture_output=True, creationflags=flags)
            if result.returncode == 0:
                return
            dest.unlink(missing_ok=True)
        result = subprocess.run(base + ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(dest)], capture_output=True, creationflags=flags)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode(errors='replace')[-400:])

    @staticmethod
    def image_convert(source, dest, quality):
        with Image.open(source) as original:
            original.seek(0)
            img = ImageOps.exif_transpose(original)
            icc = img.info.get('icc_profile')
            if img.mode in ('RGBA', 'LA') or 'transparency' in img.info:
                rgba = img.convert('RGBA')
                img = Image.new('RGB', rgba.size, 'white')
                img.paste(rgba, mask=rgba.getchannel('A'))
            else:
                img = img.convert('RGB')
            kwargs = {'format': 'JPEG', 'quality': quality, 'subsampling': 0, 'optimize': True}
            if icc:
                kwargs['icc_profile'] = icc
            img.save(dest, **kwargs)

    def run(self, files, source, target, kind, mode, quality):
        ok, errors = 0, []
        total = len(files)
        for index, file in enumerate(files, 1):
            self.set_progress(f'Convertendo {index}/{total}: {file.name}', (index - 1) / total * 100)
            outdir = target / file.relative_to(source).parent
            extension = '.mp4' if kind == 'video' else '.jpg'
            dest = None
            try:
                outdir.mkdir(parents=True, exist_ok=True)
                dest = outdir / (file.stem + extension)
                suffix = 1
                while dest.exists():
                    dest = outdir / f'{file.stem}_{suffix}{extension}'
                    suffix += 1
                if kind == 'video':
                    self.video_convert(file, dest, mode)
                else:
                    self.image_convert(file, dest, quality)
                ok += 1
            except Exception as exc:
                if dest is not None:
                    dest.unlink(missing_ok=True)
                errors.append(f'{file.name}: {str(exc)[:120]}')
            self.set_progress(f'Processados {index}/{total}', index / total * 100)

        def done():
            self.busy = False
            self.start_button.configure(state='normal')
            self.status.configure(text=f'Concluído: {ok}/{total} arquivos')
            details = '\n'.join(errors[:5])
            messagebox.showinfo('Resultado', f'Convertidos: {ok}\nFalhas: {len(errors)}\nDestino: {target}' + (f'\n\nErros:\n{details}' if errors else ''))
        self.root.after(0, done)


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
