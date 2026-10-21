
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

FORMATOS = {
    ".png", ".webp", ".bmp", ".tif", ".tiff",
    ".gif", ".heic", ".heif", ".avif",
    ".jfif", ".jpeg", ".jpg", ".ico"
}


class ConversorImagens:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imagens para JPG")
        self.root.geometry("730x530")
        self.root.resizable(False, False)

        self.origem = tk.StringVar()
        self.destino = tk.StringVar()
        self.qualidade = tk.IntVar(value=95)
        self.executando = False

        tk.Label(
            root,
            text="CONVERSOR DE IMAGENS PARA JPG",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        tk.Label(
            root,
            text="PNG • WEBP • HEIC • AVIF • BMP • TIFF • GIF",
            font=("Arial", 10)
        ).pack(pady=(0, 15))

        self.criar_seletor("PASTA DE ORIGEM", self.origem)
        self.criar_seletor("PASTA DE DESTINO", self.destino)

        tk.Label(
            root,
            text="Qualidade do JPG",
            font=("Arial", 11, "bold")
        ).pack(pady=(20, 5))

        self.label_qualidade = tk.Label(root, text="95%")
        self.label_qualidade.pack()

        tk.Scale(
            root,
            from_=80,
            to=100,
            orient="horizontal",
            variable=self.qualidade,
            length=400,
            command=self.atualizar_qualidade
        ).pack()

        self.progresso = ttk.Progressbar(
            root,
            length=600,
            maximum=100,
            mode="determinate"
        )
        self.progresso.pack(pady=20)

        self.status = tk.Label(
            root,
            text="Aguardando seleção das pastas..."
        )
        self.status.pack()

        self.botao = tk.Button(
            root,
            text="INICIAR CONVERSÃO",
            font=("Arial", 12, "bold"),
            bg="#16803c",
            fg="white",
            width=28,
            command=self.iniciar
        )
        self.botao.pack(pady=20)

    def criar_seletor(self, titulo, variavel):
        tk.Label(
            self.root,
            text=titulo,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=45, pady=(8, 3))

        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=45)

        tk.Entry(
            frame,
            textvariable=variavel,
            width=65
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Button(
            frame,
            text="Procurar",
            command=lambda: self.selecionar(variavel)
        ).pack(side="left", padx=5)

    def selecionar(self, variavel):
        pasta = filedialog.askdirectory()
        if pasta:
            variavel.set(pasta)

    def atualizar_qualidade(self, valor):
        self.label_qualidade.config(
            text=f"{int(float(valor))}%"
        )

    def atualizar(self, texto, percentual=None):
        def aplicar():
            self.status.config(text=texto)
            if percentual is not None:
                self.progresso["value"] = percentual

        self.root.after(0, aplicar)

    def iniciar(self):
        if self.executando:
            return

        origem = Path(self.origem.get())
        destino = Path(self.destino.get())

        if not origem.is_dir():
            messagebox.showerror(
                "Erro",
                "Selecione uma pasta de origem válida."
            )
            return

        if not destino.is_dir():
            messagebox.showerror(
                "Erro",
                "Selecione uma pasta de destino válida."
            )
            return

        origem = origem.resolve()
        destino = destino.resolve()

        if origem == destino:
            messagebox.showerror(
                "Erro",
                "Escolha pastas diferentes."
            )
            return

        if origem in destino.parents:
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
                "Aviso",
                "Nenhuma imagem compatível encontrada."
            )
            return

        self.executando = True
        self.botao.config(state="disabled")
        self.progresso["value"] = 0

        qualidade = self.qualidade.get()

        threading.Thread(
            target=self.converter,
            args=(arquivos, origem, destino, qualidade),
            daemon=True
        ).start()

    def converter(self, arquivos, origem, destino, qualidade):
        total = len(arquivos)
        sucesso = 0
        falhas = []

        for indice, arquivo in enumerate(arquivos, 1):
            relativo = arquivo.relative_to(origem)
            pasta_saida = destino / relativo.parent

            try:
                pasta_saida.mkdir(parents=True, exist_ok=True)

                saida = pasta_saida / f"{arquivo.stem}.jpg"

                contador = 1
                while saida.exists():
                    saida = pasta_saida / (
                        f"{arquivo.stem}_{contador}.jpg"
                    )
                    contador += 1

                self.atualizar(
                    f"Convertendo {indice}/{total}: {arquivo.name}",
                    (indice - 1) / total * 100
                )

                with Image.open(arquivo) as imagem:
                    imagem.seek(0)

                    # Corrige orientação de fotos de celulares.
                    imagem = ImageOps.exif_transpose(imagem)

                    # Preserva informações de perfil de cores.
                    icc = imagem.info.get("icc_profile")

                    # JPG não suporta transparência.
                    # Áreas transparentes ficam brancas.
                    if imagem.mode in ("RGBA", "LA") or (
                        "transparency" in imagem.info
                    ):
                        imagem = imagem.convert("RGBA")

                        fundo = Image.new(
                            "RGB",
                            imagem.size,
                            (255, 255, 255)
                        )
                        fundo.paste(imagem, mask=imagem.getchannel("A"))
                        imagem = fundo
                    else:
                        imagem = imagem.convert("RGB")

                    parametros = {
                        "format": "JPEG",
                        "quality": qualidade,
                        "subsampling": 0,
                        "optimize": True
                    }

                    if icc:
                        parametros["icc_profile"] = icc

                    imagem.save(saida, **parametros)

                sucesso += 1

            except Exception as erro:
                falhas.append(f"{arquivo.name}: {erro}")

            self.atualizar(
                f"Processados {indice}/{total}",
                indice / total * 100
            )

        def finalizar():
            self.executando = False
            self.botao.config(state="normal")

            self.status.config(
                text=f"Concluído: {sucesso}/{total} imagens"
            )

            mensagem = (
                f"Imagens convertidas: {sucesso}\n"
                f"Falhas: {len(falhas)}\n\n"
                f"Destino:\n{destino}"
            )

            if falhas:
                mensagem += "\n\nErros:\n"
                mensagem += "\n".join(falhas[:5])

            messagebox.showinfo(
                "Conversão finalizada",
                mensagem
            )

        self.root.after(0, finalizar)


if __name__ == "__main__":
    janela = tk.Tk()
    ConversorImagens(janela)
    janela.mainloop()
