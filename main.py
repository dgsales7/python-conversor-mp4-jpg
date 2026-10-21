
import subprocess
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

FORMATOS = {
    ".ts", ".mkv", ".avi", ".mov", ".webm",
    ".flv", ".wmv", ".mpeg", ".mpg", ".m4v"
}


class Conversor:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Vídeos MP4")
        self.root.geometry("720x480")

        self.origem = tk.StringVar()
        self.destino = tk.StringVar()
        self.modo = tk.StringVar(value="rapido")
        self.executando = False

        tk.Label(
            root,
            text="CONVERSOR DE VÍDEOS PARA MP4",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        self.criar_seletor("PASTA DE ORIGEM", self.origem)
        self.criar_seletor("PASTA DE DESTINO", self.destino)

        tk.Label(
            root, text="Modo de conversão:",
            font=("Arial", 11, "bold")
        ).pack(pady=(15, 5))

        tk.Radiobutton(
            root,
            text="Rápido (sem perda quando compatível)",
            variable=self.modo,
            value="rapido"
        ).pack()

        tk.Radiobutton(
            root,
            text="Alta qualidade (H.264, CRF 17)",
            variable=self.modo,
            value="qualidade"
        ).pack()

        self.progresso = ttk.Progressbar(
            root, length=600, maximum=100
        )
        self.progresso.pack(pady=20)

        self.status = tk.Label(
            root, text="Aguardando seleção das pastas..."
        )
        self.status.pack()

        self.botao = tk.Button(
            root,
            text="INICIAR CONVERSÃO",
            font=("Arial", 12, "bold"),
            bg="#16803c",
            fg="white",
            width=25,
            command=self.iniciar
        )
        self.botao.pack(pady=20)

    def criar_seletor(self, titulo, variavel):
        tk.Label(
            self.root, text=titulo,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=45, pady=(8, 3))

        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=45)

        tk.Entry(
            frame, textvariable=variavel,
            width=65
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            frame,
            text="Procurar",
            command=lambda: self.selecionar(variavel)
        ).pack(side="left", padx=5)

    def selecionar(self, variavel):
        pasta = filedialog.askdirectory()
        if pasta:
            variavel.set(pasta)

    def atualizar(self, texto, percentual=None):
        def aplicar():
            self.status.config(text=texto)
            if percentual is not None:
                self.progresso["value"] = percentual
        self.root.after(0, aplicar)

    def iniciar(self):
        if self.executando:
            return

        if not shutil.which("ffmpeg"):
            messagebox.showerror(
                "Erro", "FFmpeg não encontrado no PATH."
            )
            return

        origem = Path(self.origem.get())
        destino = Path(self.destino.get())

        if not origem.is_dir():
            messagebox.showerror(
                "Erro", "Selecione uma pasta de origem válida."
            )
            return

        if not destino.is_dir():
            messagebox.showerror(
                "Erro", "Selecione uma pasta de destino válida."
            )
            return

        if origem.resolve() == destino.resolve():
            messagebox.showerror(
                "Erro", "Escolha pastas diferentes."
            )
            return

        # Evita que a pasta de saída seja processada
        # como parte da pasta de origem.
        if origem.resolve() in destino.resolve().parents:
            messagebox.showerror(
                "Erro",
                "A pasta de destino deve ficar fora da origem."
            )
            return

        arquivos = [
            p for p in origem.rglob("*")
            if p.is_file() and p.suffix.lower() in FORMATOS
        ]

        if not arquivos:
            messagebox.showwarning(
                "Aviso", "Nenhum vídeo compatível encontrado."
            )
            return

        self.executando = True
        self.botao.config(state="disabled")
        self.progresso["value"] = 0

        threading.Thread(
            target=self.converter,
            args=(arquivos, origem, destino, self.modo.get()),
            daemon=True
        ).start()

    def executar(self, comando):
        return subprocess.run(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            creationflags=getattr(
                subprocess, "CREATE_NO_WINDOW", 0
            )
        )

    def converter(self, arquivos, origem, destino, modo):
        total = len(arquivos)
        sucesso = 0
        falhas = []

        for i, arquivo in enumerate(arquivos, 1):
            relativo = arquivo.relative_to(origem)
            pasta_saida = destino / relativo.parent
            pasta_saida.mkdir(parents=True, exist_ok=True)

            saida = pasta_saida / (arquivo.stem + ".mp4")

            contador = 1
            while saida.exists():
                saida = pasta_saida / (
                    f"{arquivo.stem}_{contador}.mp4"
                )
                contador += 1

            self.atualizar(
                f"Convertendo {i}/{total}: {arquivo.name}",
                (i - 1) / total * 100
            )

            base = [
                "ffmpeg", "-hide_banner",
                "-nostdin", "-y", "-i", str(arquivo),
                "-map", "0:v:0", "-map", "0:a?"
            ]

            resultado = None

            if modo == "rapido":
                resultado = self.executar(
                    base + [
                        "-c", "copy",
                        "-movflags", "+faststart",
                        str(saida)
                    ]
                )

                if resultado.returncode != 0:
                    saida.unlink(missing_ok=True)

            if resultado is None or resultado.returncode != 0:
                resultado = self.executar(
                    base + [
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-crf", "17",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-movflags", "+faststart",
                        str(saida)
                    ]
                )

            if resultado.returncode == 0:
                sucesso += 1
            else:
                falhas.append(arquivo.name)
                saida.unlink(missing_ok=True)

            self.atualizar(
                f"Processados {i}/{total}",
                i / total * 100
            )

        def finalizar():
            self.executando = False
            self.botao.config(state="normal")

            self.status.config(
                text=f"Finalizado: {sucesso}/{total} vídeos"
            )

            texto = (
                f"Convertidos: {sucesso}\n"
                f"Falhas: {len(falhas)}\n\n"
                f"Salvos em:\n{destino}"
            )

            if falhas:
                texto += "\n\nArquivos com erro:\n"
                texto += "\n".join(falhas[:10])

            messagebox.showinfo("Conversão finalizada", texto)

        self.root.after(0, finalizar)


if __name__ == "__main__":
    root = tk.Tk()
    Conversor(root)
    root.mainloop()
