import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import requests
import unicodedata
import threading
import time
import random
import re
import pygame
import os

# CONFIGURAÇÃO OLLAMA
MODELO = "gemma3:4b"
URL_OLLAMA = "http://127.0.0.1:11434/api/chat"

class JogoFrases:
    def __init__(self, root):
        self.root = root
        self.root.title("VALTÉCA - AdivinheLetras")
        self.root.geometry("1100x580")
        self.root.configure(bg="#0a0a2a")
        self.root.resizable(False, False)
        
        # Centralizar
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (580 // 2)
        self.root.geometry(f'1100x580+{x}+{y}')

        self.jogadores = []
        self.jogador_atual_idx = 0
        self.dados_jogadores = {}
        self.tempo_inicio = 0
        self.tempo_total_inicio = 0
        self.rodada_ativa = False
        self.ollama_online = True
        self.jogo_em_andamento = False
        self.tempo_limite = 180
        self.jogo_finalizado = False
        self.piscando = False
        self.modo_um_jogador = False
        self.ultimo_palpite = 0
        self.inatividade_contador = 0
        self.musica_atual = 0
        self.musica_tocando = False
        self.som_ativado = True  # Controle de som
        
        # Inicializar pygame mixer
        pygame.mixer.init()
        
        # Carregar sons
        self.sons = {}
        self.carregar_sons()
        
        # Banco de frases criativas por tema (fallback)
        self.frases_criativas = {
            "esperança": [
                "A esperança é a luz que ilumina os caminhos mais escuros da vida",
                "Mesmo nas tempestades mais fortes, a esperança é o porto seguro",
                "A esperança floresce onde menos se espera, como flor no deserto",
                "Sonhos alimentados pela esperança nunca morrem, apenas adormecem",
                "A esperança é a ponte entre o impossível e o realizado"
            ],
            "vida": [
                "A vida é como um livro, cada dia é uma nova página em branco",
                "Viver é a arte de transformar desafios em oportunidades",
                "A vida ganha cor quando pintada com sonhos e determinação",
                "Cada segundo da vida é um presente que merece ser celebrado",
                "A verdadeira aventura da vida é descobrir quem realmente somos"
            ],
            "amor": [
                "O amor verdadeiro é a força que move montanhas e cura feridas",
                "Amar é entregar-se sem medo e receber de coração aberto",
                "No jardim da vida, o amor é a flor mais perfumada",
                "O amor transforma o comum em extraordinário",
                "Amar é escrever histórias bonitas no livro da existência"
            ],
            "amizade": [
                "Amigos são a família que escolhemos para caminhar juntos",
                "Uma amizade verdadeira vale mais que todo ouro do mundo",
                "Nos momentos difíceis, a amizade é o ombro amigo que acolhe",
                "Amigos transformam a jornada da vida em uma aventura inesquecível",
                "A amizade é o abraço que aquece a alma nos dias frios"
            ],
            "felicidade": [
                "A felicidade mora nos pequenos momentos que aquecem o coração",
                "Ser feliz é encontrar beleza nas coisas simples da vida",
                "A verdadeira felicidade está em compartilhar sorrisos genuínos",
                "Felicidade não é destino, é a forma como escolhemos caminhar",
                "Os momentos de felicidade são estrelas que iluminam nossa memória"
            ],
            "sonhos": [
                "Sonhos são as sementes que regamos com esperança e determinação",
                "Nunca desista dos seus sonhos, eles são a bússola da sua alma",
                "Os maiores realizadores foram aqueles que ousaram sonhar alto",
                "Sonhar é o primeiro passo para transformar o impossível em realidade",
                "Acredite nos seus sonhos, pois eles são o mapa do seu destino"
            ],
            "coragem": [
                "Coragem não é ausência de medo, é agir apesar dele",
                "Os heróis são aqueles que encontram força onde parece não haver",
                "A coragem mora no coração daqueles que não desistem",
                "Ter coragem é dar um passo de cada vez em direção ao desconhecido",
                "A maior coragem é ser verdadeiro consigo mesmo"
            ]
        }
        
        self.setup_ui()
        self.verificar_ollama()
        self.mostrar_configuracao_inicial()

    def carregar_sons(self):
        """Carrega todos os arquivos de som"""
        arquivos_som = {
            'abertura': 'abertura.mp3',
            'tecla': 'tecla.mp3',
            'erro': 'erro.mp3',
            'vitoria': 'vitoria.mp3',
            'passagem_vez': 'passagem_da_vez.mp3',
            'fim_jogo': 'fim_de_jogo.mp3',
            'dica': 'dica.mp3',
            'geracao_frase': 'geracao_de_frase.mp3',
            'musica_1': 'musica_ambiente_1.mp3',
            'musica_2': 'musica_ambiente_2.mp3',
            'musica_3': 'musica_ambiente_3.mp3',
            'musica_4': 'musica_ambiente_4.mp3'
        }
        
        for nome, arquivo in arquivos_som.items():
            try:
                if os.path.exists(arquivo):
                    self.sons[nome] = pygame.mixer.Sound(arquivo)
                else:
                    print(f"Arquivo não encontrado: {arquivo}")
                    self.sons[nome] = None
            except Exception as e:
                print(f"Erro ao carregar {arquivo}: {e}")
                self.sons[nome] = None

    def tocar_som(self, nome_som):
        """Toca um som específico se o som estiver ativado"""
        if self.som_ativado and nome_som in self.sons and self.sons[nome_som]:
            try:
                self.sons[nome_som].play()
            except:
                pass

    def iniciar_musica_ambiente(self):
        """Inicia a música ambiente em loop"""
        if not self.som_ativado or self.musica_tocando:
            return
        
        def tocar_musica():
            while self.jogo_em_andamento and not self.jogo_finalizado and self.som_ativado:
                # Alternar entre as 4 músicas
                for i in range(1, 5):
                    if not self.jogo_em_andamento or self.jogo_finalizado or not self.som_ativado:
                        break
                    nome_musica = f'musica_{i}'
                    if nome_musica in self.sons and self.sons[nome_musica]:
                        self.sons[nome_musica].play()
                        # Aguardar a música terminar
                        time.sleep(self.sons[nome_musica].get_length())
        
        self.musica_tocando = True
        threading.Thread(target=tocar_musica, daemon=True).start()

    def parar_musica_ambiente(self):
        """Para a música ambiente"""
        self.musica_tocando = False
        if self.som_ativado:
            pygame.mixer.stop()

    def alternar_som(self):
        """Alterna entre som ativado e desativado"""
        self.som_ativado = not self.som_ativado
        
        if self.som_ativado:
            self.btn_som.config(text="🔊 SOM", bg="#27ae60")
            # Reiniciar música ambiente se o jogo estiver em andamento
            if self.jogo_em_andamento and not self.jogo_finalizado:
                self.iniciar_musica_ambiente()
        else:
            self.btn_som.config(text="🔇 MUDO", bg="#e74c3c")
            self.parar_musica_ambiente()

    def verificar_ollama(self):
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.ollama_online = True
            else:
                self.ollama_online = False
        except:
            self.ollama_online = False

    def obter_frase_motivacional(self):
        if not self.ollama_online:
            frases_motivacionais = [
                "A educação é a chave para abrir as portas do futuro.",
                "O conhecimento transforma vidas e expande horizontes.",
                "Aprender é um tesouro que ninguém pode roubar.",
                "A educação liberta a mente e alimenta a alma.",
                "Cada dia é uma oportunidade para aprender algo novo."
            ]
            return random.choice(frases_motivacionais)
        
        corpo = {
            "model": MODELO,
            "messages": [{"role": "user", "content": "Crie uma frase motivacional curta e inspiradora sobre educação. Seja criativo e original. Apenas a frase."}],
            "stream": False
        }
        try:
            res = requests.post(URL_OLLAMA, json=corpo, timeout=15)
            if res.status_code == 200:
                frase = res.json()['message']['content'].strip()
                frase = frase.replace('"', '')
                return frase[:150]
            else:
                return random.choice(frases_motivacionais)
        except:
            return random.choice(frases_motivacionais)

    def remover_acentos(self, texto):
        nfkd = unicodedata.normalize('NFKD', texto)
        return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper()

    def validar_tema(self, tema):
        tema = tema.strip().lower()
        if not tema:
            return False, "O tema não pode estar vazio!"
        
        if re.match(r'^[a-zA-Záàâãéèêíïóôõöúçñ\s]+$', tema):
            return True, tema
        else:
            return False, "O tema deve conter apenas letras e espaços (números e símbolos não são permitidos)!"

    def obter_frase_ia(self, tema):
        tema_lower = tema.lower()
        
        if self.ollama_online:
            prompt = f"""Crie uma frase original, poética e criativa sobre "{tema}".

REGRAS OBRIGATÓRIAS:
- A frase deve ter entre 10 e 15 palavras (conte as palavras!)
- NÃO use frases como "O tema X é interessante" ou frases genéricas
- Seja criativo, use metáforas, inspiração e fuja do óbvio
- A frase deve ser completa e fazer sentido

Apenas a frase, sem aspas, sem explicações, sem repetir o tema."""
            
            corpo = {
                "model": MODELO,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9
                }
            }
            try:
                res = requests.post(URL_OLLAMA, json=corpo, timeout=30)
                if res.status_code == 200:
                    frase = res.json()['message']['content'].strip()
                    frase = frase.replace('"', '').replace('!', '').replace('?', '')
                    
                    num_palavras = len(frase.split())
                    
                    if num_palavras < 10 or num_palavras > 15 or "tema" in frase.lower() or "interessante" in frase.lower():
                        return self.obter_frase_do_banco(tema_lower)
                    return frase
                else:
                    return self.obter_frase_do_banco(tema_lower)
            except:
                return self.obter_frase_do_banco(tema_lower)
        else:
            return self.obter_frase_do_banco(tema_lower)

    def obter_frase_do_banco(self, tema):
        for chave, frases in self.frases_criativas.items():
            if chave in tema or tema in chave:
                return random.choice(frases)
        
        frases_genericas_criativas = [
            f"No universo de {tema}, cada descoberta revela novos horizontes",
            f"A beleza de {tema} está nos detalhes que poucos conseguem enxergar",
            f"{tema.capitalize()} é como um rio que flui constante em direção ao desconhecido",
            f"Explorar {tema} é como navegar por um oceano de possibilidades infinitas",
            f"Em cada canto de {tema}, há uma história esperando para ser contada",
            f"A magia de {tema} transforma o comum em extraordinário",
            f"{tema.capitalize()} nos ensina que o impossível é apenas questão de perspectiva",
            f"Como um artista, {tema} pinta cores vibrantes na tela da realidade",
            f"Em {tema}, encontramos respostas que nem sabíamos que procurávamos",
            f"A jornada por {tema} revela tesouros escondidos em cada esquina"
        ]
        
        return random.choice(frases_genericas_criativas).replace("{tema}", tema.capitalize())

    def setup_ui(self):
        top_frame = tk.Frame(self.root, bg="#0a0a2a")
        top_frame.pack(pady=3, fill="x")
        
        titulo_frame = tk.Frame(top_frame, bg="#0a0a2a")
        titulo_frame.pack(side="left", expand=True)
        tk.Label(titulo_frame, text="🎮 VALTÉCA", font=("Impact", 26), bg="#0a0a2a", fg="#ffd966").pack()
        tk.Label(titulo_frame, text="AdivinheLetras", font=("Arial", 11, "bold"), bg="#0a0a2a", fg="#ff6b6b").pack()
        
        relogios_frame = tk.Frame(top_frame, bg="#0a0a2a")
        relogios_frame.pack(side="right", padx=15)
        
        tk.Label(relogios_frame, text="⏱️ RODADA", font=("Arial", 7, "bold"), 
                bg="#0a0a2a", fg="#95a5a6").pack()
        self.lbl_timer = tk.Label(relogios_frame, text="03:00", font=("Consolas", 14, "bold"), 
                                  bg="#0a0a2a", fg="#ff6b6b")
        self.lbl_timer.pack()
        
        tk.Label(relogios_frame, text="⏲️ TOTAL", font=("Arial", 7, "bold"), 
                bg="#0a0a2a", fg="#95a5a6").pack()
        self.lbl_tempo_total = tk.Label(relogios_frame, text="00:00:00", font=("Consolas", 9, "bold"), 
                                        bg="#0a0a2a", fg="#f1c40f")
        self.lbl_tempo_total.pack()
        
        ranking_frame = tk.Frame(self.root, bg="#2c3e50", bd=2, relief="ridge")
        ranking_frame.pack(pady=3, fill="x", padx=40)
        
        self.lbl_ranking_titulo = tk.Label(ranking_frame, text="🏆 STATUS DOS JOGADORES", font=("Arial", 9, "bold"), 
                bg="#2c3e50", fg="#ffd966")
        self.lbl_ranking_titulo.pack(pady=2)
        
        ranking_scroll_frame = tk.Frame(ranking_frame, bg="#2c3e50")
        ranking_scroll_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        canvas_ranking = tk.Canvas(ranking_scroll_frame, bg="#2c3e50", highlightthickness=0, height=85)
        scrollbar_ranking = ttk.Scrollbar(ranking_scroll_frame, orient="vertical", command=canvas_ranking.yview)
        self.scrollable_ranking = tk.Frame(canvas_ranking, bg="#2c3e50")
        
        self.scrollable_ranking.bind("<Configure>", lambda e: canvas_ranking.configure(scrollregion=canvas_ranking.bbox("all")))
        canvas_ranking.create_window((0, 0), window=self.scrollable_ranking, anchor="nw")
        canvas_ranking.configure(yscrollcommand=scrollbar_ranking.set)
        
        canvas_ranking.pack(side="left", fill="both", expand=True)
        scrollbar_ranking.pack(side="right", fill="y")
        
        self.lbl_ranking = tk.Label(self.scrollable_ranking, text="AGUARDANDO JOGADORES", 
                                   font=("Arial", 8), bg="#2c3e50", fg="#f1c40f", justify="left")
        self.lbl_ranking.pack()
        
        self.lbl_jogador_atual = tk.Label(self.root, text="", font=("Arial", 12, "bold"), 
                                          bg="#0a0a2a", fg="#ffd966")
        self.lbl_jogador_atual.pack(pady=2)
        
        self.lbl_tema_atual = tk.Label(self.root, text="", font=("Arial", 10, "italic"), 
                                       bg="#0a0a2a", fg="#5dade2")
        self.lbl_tema_atual.pack(pady=1)
        
        self.lbl_frase = tk.Label(self.root, text="✨ CONFIGURE O JOGO ✨", font=("Courier New", 11, "bold"), 
                                 bg="#1a1a2e", fg="#ffffff", wraplength=1000, padx=8, pady=8, relief="sunken", bd=2)
        self.lbl_frase.pack(pady=4, fill="x", padx=30)
        
        self.frame_teclado = tk.Frame(self.root, bg="#0a0a2a")
        self.frame_teclado.pack(pady=3)
        
        self.botoes_letras = {}
        linhas_teclado = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row, linha in enumerate(linhas_teclado):
            frame_linha = tk.Frame(self.frame_teclado, bg="#0a0a2a")
            frame_linha.pack(pady=1)
            for letra in linha:
                btn = tk.Button(frame_linha, text=letra, width=3, height=1, font=("Arial", 9, "bold"),
                                bg="#3498db", fg="white", relief="raised", bd=2,
                                state="disabled", command=lambda l=letra: self.dar_palpite(l))
                btn.pack(side="left", padx=1, pady=1)
                self.botoes_letras[letra] = btn
        
        btn_controle_frame = tk.Frame(self.root, bg="#0a0a2a")
        btn_controle_frame.pack(pady=4)
        
        self.btn_som = tk.Button(btn_controle_frame, text="🔊 SOM", command=self.alternar_som,
                                 bg="#27ae60", fg="white", font=("Arial", 8, "bold"), padx=12, pady=2)
        self.btn_som.pack(side="left", padx=4)
        
        self.btn_dica = tk.Button(btn_controle_frame, text="💡 DICA (+10s)", command=self.usar_dica,
                                  bg="#9b59b6", fg="white", font=("Arial", 8, "bold"), padx=12, pady=2,
                                  state="disabled")
        self.btn_dica.pack(side="left", padx=4)
        
        self.btn_desistir = tk.Button(btn_controle_frame, text="🚪 DESISTIR", command=self.desistir_jogador,
                                      bg="#e74c3c", fg="white", font=("Arial", 8, "bold"), padx=12, pady=2,
                                      state="disabled")
        self.btn_desistir.pack(side="left", padx=4)
        
        self.btn_reiniciar = tk.Button(btn_controle_frame, text="🔄 REINICIAR", command=self.reiniciar_jogo,
                                       bg="#f39c12", fg="white", font=("Arial", 8, "bold"), padx=12, pady=2)
        self.btn_reiniciar.pack(side="left", padx=4)
        
        self.btn_sair = tk.Button(btn_controle_frame, text="❌ SAIR", command=self.sair_jogo,
                                  bg="#e74c3c", fg="white", font=("Arial", 8, "bold"), padx=12, pady=2)
        self.btn_sair.pack(side="left", padx=4)
        
        msg_frame = tk.Frame(self.root, bg="#1a1a2e", bd=2, relief="ridge")
        msg_frame.pack(pady=3, fill="x", padx=40)
        
        tk.Label(msg_frame, text="📢 MENSAGEM", font=("Arial", 7, "bold"), 
                bg="#1a1a2e", fg="#ffd966").pack(pady=1)
        
        self.lbl_mensagem = tk.Label(msg_frame, text="Bem-vindo ao VALTÉCA! Configure o jogo para começar.", 
                                    font=("Arial", 7), bg="#1a1a2e", fg="#95a5a6", wraplength=1000)
        self.lbl_mensagem.pack(pady=1)

    def mostrar_configuracao_inicial(self):
        self.win_qtd = tk.Toplevel(self.root)
        self.win_qtd.title("Configurar Jogo")
        self.win_qtd.geometry("400x280")
        self.win_qtd.configure(bg="#2c3e50")
        self.win_qtd.grab_set()
        
        self.win_qtd.update_idletasks()
        x = (self.win_qtd.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.win_qtd.winfo_screenheight() // 2) - (280 // 2)
        self.win_qtd.geometry(f'400x280+{x}+{y}')
        
        tk.Label(self.win_qtd, text="⚙️ CONFIGURAÇÃO", font=("Arial", 18, "bold"), 
                bg="#2c3e50", fg="#ffd966").pack(pady=20)
        
        tk.Label(self.win_qtd, text="NÚMERO DE JOGADORES (1-10):", bg="#2c3e50", fg="white", 
                font=("Arial", 12, "bold")).pack(pady=15)
        
        self.spin_qtd = ttk.Spinbox(self.win_qtd, from_=1, to=10, width=10, font=("Arial", 14))
        self.spin_qtd.set(2)
        self.spin_qtd.pack(pady=10)
        
        tk.Button(self.win_qtd, text="▶ PRÓXIMO", command=self.configurar_nomes, 
                  bg="#27ae60", fg="white", font=("Arial", 12, "bold"), padx=40, pady=8).pack(pady=25)

    def configurar_nomes(self):
        qtd = int(self.spin_qtd.get())
        self.modo_um_jogador = (qtd == 1)
        self.win_qtd.destroy()
        
        self.win_nomes = tk.Toplevel(self.root)
        self.win_nomes.title("Nomes dos Jogadores")
        self.win_nomes.geometry("550x500")
        self.win_nomes.configure(bg="#2c3e50")
        self.win_nomes.grab_set()
        
        self.win_nomes.update_idletasks()
        x = (self.win_nomes.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.win_nomes.winfo_screenheight() // 2) - (500 // 2)
        self.win_nomes.geometry(f'550x500+{x}+{y}')
        
        main_frame = tk.Frame(self.win_nomes, bg="#2c3e50")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Label(main_frame, text="👥 NOMES DOS JOGADORES", font=("Arial", 12, "bold"), 
                bg="#2c3e50", fg="#ffd966").pack(pady=5)
        
        frame_lista = tk.Frame(main_frame, bg="#2c3e50")
        frame_lista.pack(pady=5, fill="both", expand=True)
        
        canvas = tk.Canvas(frame_lista, bg="#2c3e50", highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#2c3e50")
        
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.entradas_nomes = []
        for i in range(qtd):
            frame = tk.Frame(self.scrollable_frame, bg="#2c3e50", pady=2)
            frame.pack(fill="x")
            tk.Label(frame, text=f"Jogador {i+1}:", bg="#2c3e50", fg="white", 
                    font=("Arial", 8, "bold"), width=8).pack(side="left")
            en = tk.Entry(frame, font=("Arial", 8), width=22, bg="#ecf0f1", fg="#2c3e50")
            en.insert(0, f"Jogador{i+1}")
            en.pack(side="left", padx=5)
            if i == 0:
                en.focus_set()
                en.select_range(0, tk.END)
            self.entradas_nomes.append(en)
        
        frame_teclado = tk.Frame(main_frame, bg="#34495e", bd=2, relief="ridge")
        frame_teclado.pack(pady=5, fill="x")
        
        tk.Label(frame_teclado, text="TECLADO VIRTUAL", font=("Arial", 7, "bold"), 
                bg="#34495e", fg="#ffd966").pack(pady=2)
        
        teclado = "QWERTYUIOPASDFGHJKLZXCVBNM"
        frame_linha = tk.Frame(frame_teclado, bg="#34495e")
        frame_linha.pack(pady=1)
        
        for i, letra in enumerate(teclado):
            btn = tk.Button(frame_linha, text=letra, width=2, height=1, font=("Arial", 7, "bold"),
                           bg="#5dade2", fg="white", relief="raised",
                           command=lambda l=letra: self.inserir_letra_nome(l))
            btn.pack(side="left", padx=1, pady=1)
            if (i + 1) % 10 == 0 and i + 1 < len(teclado):
                frame_linha = tk.Frame(frame_teclado, bg="#34495e")
                frame_linha.pack(pady=1)
        
        frame_ctrl = tk.Frame(frame_teclado, bg="#34495e")
        frame_ctrl.pack(pady=2)
        
        tk.Button(frame_ctrl, text="⌫ BACKSPACE", command=self.apagar_letra_nome,
                 bg="#e67e22", fg="white", font=("Arial", 7, "bold"), padx=6).pack(side="left", padx=3)
        
        tk.Button(frame_ctrl, text="␣ ESPAÇO", command=self.inserir_espaco_nome,
                 bg="#3498db", fg="white", font=("Arial", 7, "bold"), padx=6).pack(side="left", padx=3)
        
        btn_frame = tk.Frame(main_frame, bg="#2c3e50")
        btn_frame.pack(pady=6)
        
        tk.Button(btn_frame, text="✅ INICIAR JOGO", command=self.iniciar_jogo, 
                  bg="#27ae60", fg="white", font=("Arial", 9, "bold"), padx=15, pady=4).pack(side="left", padx=4)
        
        tk.Button(btn_frame, text="🔙 VOLTAR", command=self.voltar_configuracao,
                  bg="#e67e22", fg="white", font=("Arial", 9, "bold"), padx=15, pady=4).pack(side="left", padx=4)
        
        tk.Button(btn_frame, text="❌ CANCELAR", command=self.cancelar_configuracao,
                  bg="#e74c3c", fg="white", font=("Arial", 9, "bold"), padx=15, pady=4).pack(side="left", padx=4)
        
        tk.Label(main_frame, text="💡 Clique no campo do nome para digitar", 
                font=("Arial", 6), bg="#2c3e50", fg="#95a5a6").pack(pady=2)

    def voltar_configuracao(self):
        self.win_nomes.destroy()
        self.mostrar_configuracao_inicial()

    def cancelar_configuracao(self):
        self.win_nomes.destroy()
        if messagebox.askyesno("Sair", "❓ Deseja sair do VALTÉCA?"):
            self.root.quit()

    def inserir_letra_nome(self, letra):
        for en in self.entradas_nomes:
            if en.focus_get() == en:
                en.insert(tk.INSERT, letra)
                break

    def apagar_letra_nome(self):
        for en in self.entradas_nomes:
            if en.focus_get() == en:
                texto = en.get()
                if texto:
                    en.delete(len(texto)-1, tk.END)
                break

    def inserir_espaco_nome(self):
        for en in self.entradas_nomes:
            if en.focus_get() == en:
                en.insert(tk.INSERT, " ")
                break

    def iniciar_jogo(self):
        self.jogadores = []
        for en in self.entradas_nomes:
            nome = en.get().strip()
            if not nome:
                messagebox.showwarning("Atenção", "Todos os jogadores devem ter um nome!")
                return
            self.jogadores.append(nome)
        
        if len(self.jogadores) != len(set(self.jogadores)):
            messagebox.showwarning("Atenção", "Nomes duplicados não são permitidos!")
            return
        
        self.win_nomes.destroy()
        
        for nome in self.jogadores:
            self.dados_jogadores[nome] = {
                'tempo': None,
                'frase': '',
                'frase_limpa': '',
                'letras_descobertas': set(),
                'completou': False,
                'tema': '',
                'frase_original': ''
            }
        
        self.jogador_atual_idx = 0
        self.jogo_em_andamento = True
        self.jogo_finalizado = False
        self.tempo_total_inicio = time.time()
        self.inatividade_contador = 0
        
        # Tocar som de abertura e iniciar música ambiente (se som ativado)
        self.tocar_som('abertura')
        self.iniciar_musica_ambiente()
        
        # Configurar interface
        if self.modo_um_jogador:
            self.btn_desistir.config(state="disabled")
            self.btn_dica.config(state="normal")
            self.lbl_timer.config(text="00:00")
        else:
            self.btn_desistir.config(state="normal")
            self.btn_dica.config(state="normal")
            self.lbl_timer.config(text="03:00")
        
        self.atualizar_ranking()
        self.mostrar_mensagem_motivacional()
        self.atualizar_tempo_total()
        self.iniciar_rodada_jogador()

    def atualizar_tempo_total(self):
        if self.jogo_em_andamento and not self.jogo_finalizado:
            decorrido = time.time() - self.tempo_total_inicio
            horas = int(decorrido // 3600)
            minutos = int((decorrido % 3600) // 60)
            segundos = int(decorrido % 60)
            self.lbl_tempo_total.config(text=f"{horas:02d}:{minutos:02d}:{segundos:02d}")
            self.root.after(1000, self.atualizar_tempo_total)

    def mostrar_mensagem_motivacional(self):
        threading.Thread(target=self.buscar_mensagem_motivacional, daemon=True).start()

    def buscar_mensagem_motivacional(self):
        frase = self.obter_frase_motivacional()
        self.root.after(0, lambda: self.lbl_mensagem.config(text=frase, fg="#ffd966"))

    def iniciar_rodada_jogador(self):
        todos_completaram = all(self.dados_jogadores[nome]['completou'] for nome in self.jogadores)
        if todos_completaram:
            self.finalizar_jogo()
            return
        
        if not self.modo_um_jogador:
            while self.jogador_atual_idx < len(self.jogadores):
                nome = self.jogadores[self.jogador_atual_idx]
                if not self.dados_jogadores[nome]['completou']:
                    self.jogador_atual = nome
                    break
                self.jogador_atual_idx += 1
            
            if self.jogador_atual_idx >= len(self.jogadores):
                self.jogador_atual_idx = 0
                self.iniciar_rodada_jogador()
                return
        else:
            self.jogador_atual = self.jogadores[0]
        
        dados = self.dados_jogadores[self.jogador_atual]
        
        self.lbl_jogador_atual.config(text=f"🎯 JOGANDO AGORA: {self.jogador_atual} 🎯", fg="#ffd966")
        if dados['tema']:
            self.lbl_tema_atual.config(text=f"📌 TEMA: {dados['tema'].upper()}", fg="#5dade2")
        else:
            self.lbl_tema_atual.config(text="📌 AGUARDANDO TEMA...", fg="#5dade2")
        
        self.iniciar_pisca_nome()
        
        if dados['frase'] == '':
            self.abrir_teclado_tema()
        else:
            self.retomar_rodada()

    def abrir_teclado_tema(self):
        nome = self.jogador_atual
        
        self.win_tema = tk.Toplevel(self.root)
        self.win_tema.title(f"{nome} - Escolha o Tema")
        self.win_tema.geometry("500x450")
        self.win_tema.configure(bg="#2c3e50")
        self.win_tema.grab_set()
        
        self.win_tema.update_idletasks()
        x = (self.win_tema.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.win_tema.winfo_screenheight() // 2) - (450 // 2)
        self.win_tema.geometry(f'500x450+{x}+{y}')
        
        tk.Label(self.win_tema, text=f"🎯 {nome} - DIGITE O TEMA", font=("Arial", 12, "bold"), 
                bg="#2c3e50", fg="#ffd966").pack(pady=6)
        
        tk.Label(self.win_tema, text="Exemplos: esperança, amor, amizade, aventura, sonhos, liberdade...", 
                font=("Arial", 8), bg="#2c3e50", fg="#95a5a6").pack()
        
        self.entry_tema = tk.Entry(self.win_tema, font=("Arial", 12), width=30, bg="#ecf0f1", fg="#2c3e50")
        self.entry_tema.pack(pady=8)
        self.entry_tema.focus_set()
        
        frame_teclado_tema = tk.Frame(self.win_tema, bg="#34495e", bd=2, relief="ridge")
        frame_teclado_tema.pack(pady=6, padx=20, fill="x")
        
        tk.Label(frame_teclado_tema, text="TECLADO VIRTUAL", font=("Arial", 8, "bold"), 
                bg="#34495e", fg="#ffd966").pack(pady=2)
        
        linhas_teclado_tema = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for linha in linhas_teclado_tema:
            frame_linha = tk.Frame(frame_teclado_tema, bg="#34495e")
            frame_linha.pack(pady=1)
            for letra in linha:
                btn = tk.Button(frame_linha, text=letra, width=3, height=1, font=("Arial", 8, "bold"),
                               bg="#5dade2", fg="white", relief="raised",
                               command=lambda l=letra: self.inserir_letra_tema(l))
                btn.pack(side="left", padx=1)
        
        frame_ctrl = tk.Frame(frame_teclado_tema, bg="#34495e")
        frame_ctrl.pack(pady=2)
        
        tk.Button(frame_ctrl, text="⌫ BACKSPACE", command=self.apagar_letra_tema,
                 bg="#e67e22", fg="white", font=("Arial", 8, "bold"), padx=8).pack(side="left", padx=3)
        
        tk.Button(frame_ctrl, text="␣ ESPAÇO", command=self.inserir_espaco_tema,
                 bg="#3498db", fg="white", font=("Arial", 8, "bold"), padx=8).pack(side="left", padx=3)
        
        btn_frame = tk.Frame(self.win_tema, bg="#2c3e50")
        btn_frame.pack(pady=8)
        
        tk.Button(btn_frame, text="✅ CONFIRMAR TEMA", command=self.confirmar_tema,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), padx=15, pady=4).pack(side="left", padx=8)
        
        tk.Button(btn_frame, text="❌ CANCELAR", command=self.cancelar_tema,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), padx=15, pady=4).pack(side="left", padx=8)

    def inserir_letra_tema(self, letra):
        self.entry_tema.insert(tk.INSERT, letra.lower())

    def apagar_letra_tema(self):
        texto = self.entry_tema.get()
        if texto:
            self.entry_tema.delete(len(texto)-1, tk.END)

    def inserir_espaco_tema(self):
        self.entry_tema.insert(tk.INSERT, " ")

    def confirmar_tema(self):
        tema = self.entry_tema.get().strip()
        
        valido, mensagem = self.validar_tema(tema)
        
        if not valido:
            messagebox.showwarning("Tema Inválido", mensagem)
            return
        
        self.win_tema.destroy()
        
        nome = self.jogador_atual
        self.dados_jogadores[nome]['tema'] = tema
        self.lbl_tema_atual.config(text=f"📌 TEMA: {tema.upper()}", fg="#5dade2")
        self.mostrar_mensagem(f"🤖 Gerando frase sobre {tema.upper()}...")
        
        for btn in self.botoes_letras.values():
            btn.config(state="disabled", bg="#95a5a6")
        
        self.lbl_frase.config(text=f"🤖 GERANDO FRASE SOBRE: {tema.upper()}...\n⏳ AGUARDE...")
        
        threading.Thread(target=self.gerar_frase, args=(nome, tema), daemon=True).start()

    def cancelar_tema(self):
        self.win_tema.destroy()
        self.mostrar_mensagem("❌ Tema não escolhido! Reiniciando o jogo...")
        self.lbl_jogador_atual.config(text="❌ Jogo reiniciado por cancelamento!", fg="#e74c3c")
        self.root.after(2000, self.reiniciar_jogo)

    def gerar_frase(self, nome, tema):
        frase = self.obter_frase_ia(tema)
        self.dados_jogadores[nome]['frase_original'] = frase
        self.dados_jogadores[nome]['frase_limpa'] = self.remover_acentos(frase)
        self.dados_jogadores[nome]['frase'] = frase
        self.root.after(0, self.retomar_rodada)
        self.tocar_som('geracao_frase')

    def retomar_rodada(self):
        nome = self.jogador_atual
        dados = self.dados_jogadores[nome]
        
        self.rodada_ativa = True
        self.tempo_inicio = time.time()
        self.ultimo_palpite = time.time()
        
        if not self.modo_um_jogador:
            self.btn_desistir.config(state="normal")
            self.btn_dica.config(state="normal")
        
        # Resetar teclado
        for letra, btn in self.botoes_letras.items():
            if letra in dados['letras_descobertas']:
                btn.config(state="disabled", bg="#2ecc71", text="✓")
            else:
                btn.config(state="normal", bg="#3498db", fg="white", text=letra)
        
        self.atualizar_frase_display(nome)
        self.iniciar_temporizador_rodada()

    def iniciar_temporizador_rodada(self):
        if self.rodada_ativa and not self.jogo_finalizado:
            decorrido = time.time() - self.tempo_inicio
            
            if not self.modo_um_jogador:
                restante = max(0, self.tempo_limite - decorrido)
                minutos = int(restante // 60)
                segundos = int(restante % 60)
                self.lbl_timer.config(text=f"{minutos:02d}:{segundos:02d}")
                
                if restante <= 0:
                    self.tempo_esgotado()
                    return
            else:
                minutos = int(decorrido // 60)
                segundos = int(decorrido % 60)
                self.lbl_timer.config(text=f"{minutos:02d}:{segundos:02d}")
            
            self.root.after(1000, self.iniciar_temporizador_rodada)

    def tempo_esgotado(self):
        if self.rodada_ativa and not self.modo_um_jogador:
            nome = self.jogador_atual
            self.rodada_ativa = False
            self.mostrar_mensagem(f"⏰ Tempo esgotado! {nome} não completou a frase.")
            self.lbl_jogador_atual.config(text=f"⏰ TEMPO ESGOTADO - {nome} perdeu a vez!", fg="#e74c3c")
            
            self.jogador_atual_idx += 1
            self.atualizar_ranking()
            self.parar_pisca_nome()
            self.root.after(2000, self.iniciar_rodada_jogador)

    def usar_dica(self):
        if not self.rodada_ativa or self.jogo_finalizado:
            return
        
        nome = self.jogador_atual
        dados = self.dados_jogadores[nome]
        
        # Encontrar letras ainda não descobertas
        letras_restantes = []
        for letra in dados['frase_limpa']:
            if letra.isalpha() and letra not in dados['letras_descobertas']:
                if letra not in letras_restantes:
                    letras_restantes.append(letra)
        
        if not letras_restantes:
            self.mostrar_mensagem("⚠️ Não há mais letras para revelar!")
            return
        
        self.tocar_som('dica')
        
        # Escolher uma letra aleatória
        letra_dica = random.choice(letras_restantes)
        
        # Revelar a letra
        dados['letras_descobertas'].add(letra_dica)
        
        # Punir com +10 segundos (apenas no modo multi)
        if not self.modo_um_jogador:
            tempo_decorrido = time.time() - self.tempo_inicio
            self.tempo_inicio = time.time() - (tempo_decorrido + 10)
        
        # Atualizar teclado
        if letra_dica in self.botoes_letras:
            self.botoes_letras[letra_dica].config(state="disabled", bg="#2ecc71", text="✓")
        
        self.mostrar_mensagem(f"💡 Dica: A letra '{letra_dica}' foi revelada! (+10s)" if not self.modo_um_jogador else f"💡 Dica: A letra '{letra_dica}' foi revelada!")
        
        self.atualizar_frase_display(nome)

    def dar_palpite(self, letra):
        if not self.rodada_ativa or self.jogo_finalizado:
            return
        
        self.ultimo_palpite = time.time()
        self.inatividade_contador = 0
        self.tocar_som('tecla')
        
        nome = self.jogador_atual
        dados = self.dados_jogadores[nome]
        
        if letra in dados['letras_descobertas']:
            return
        
        dados['letras_descobertas'].add(letra)
        
        if letra in dados['frase_limpa']:
            self.botoes_letras[letra].config(state="disabled", bg="#2ecc71", text="✓")
            self.atualizar_frase_display(nome)
        else:
            self.botoes_letras[letra].config(state="disabled", bg="#e74c3c", text="✗")
            self.mostrar_mensagem(f"❌ {nome} errou a letra {letra}!")
            self.tocar_som('erro')
            
            if not self.modo_um_jogador:
                self.lbl_jogador_atual.config(text=f"❌ {nome} ERROU! Passando a vez...", fg="#e74c3c")
                self.rodada_ativa = False
                self.tocar_som('passagem_vez')
                self.jogador_atual_idx += 1
                self.atualizar_ranking()
                self.parar_pisca_nome()
                self.root.after(2000, self.iniciar_rodada_jogador)
            else:
                self.lbl_jogador_atual.config(text=f"❌ {nome} errou a letra {letra}! Continue tentando...", fg="#e74c3c")
                self.root.after(2000, lambda: self.lbl_jogador_atual.config(text=f"🎯 JOGANDO AGORA: {nome} 🎯", fg="#ffd966"))

    def atualizar_frase_display(self, nome):
        dados = self.dados_jogadores[nome]
        frase_original = dados['frase_original']
        letras_descobertas = dados['letras_descobertas']
        
        exibicao = ""
        faltam = False
        letras_faltando = []
        
        for letra in frase_original:
            letra_sem_acento = self.remover_acentos(letra) if letra.isalpha() else letra
            
            if letra == " ":
                exibicao += "  "
            elif not letra.isalpha():
                exibicao += letra + " "
            elif letra_sem_acento in letras_descobertas:
                exibicao += letra + " "
            else:
                exibicao += "_ "
                faltam = True
                if letra_sem_acento not in letras_faltando:
                    letras_faltando.append(letra_sem_acento)
        
        self.lbl_frase.config(text=exibicao)
        
        if faltam:
            self.lbl_tema_atual.config(text=f"📌 TEMA: {dados['tema'].upper()} | FALTAM: {', '.join(sorted(letras_faltando))}", fg="#e74c3c")
        else:
            self.lbl_tema_atual.config(text=f"📌 TEMA: {dados['tema'].upper()}", fg="#5dade2")
        
        if not faltam and self.rodada_ativa:
            self.completou_frase(nome)

    def completou_frase(self, nome):
        self.rodada_ativa = False
        tempo_decorrido = time.time() - self.tempo_inicio
        
        self.dados_jogadores[nome]['tempo'] = tempo_decorrido
        self.dados_jogadores[nome]['completou'] = True
        
        self.mostrar_mensagem(f"🏆 {nome} completou a frase em {self.formatar_tempo(tempo_decorrido)}!")
        self.lbl_jogador_atual.config(text=f"🏆 {nome} COMPLETOU A FRASE! 🏆", fg="#2ecc71")
        self.tocar_som('vitoria')
        
        self.atualizar_ranking()
        self.parar_pisca_nome()
        
        todos_completaram = all(self.dados_jogadores[nome]['completou'] for nome in self.jogadores)
        if todos_completaram:
            self.finalizar_jogo()
        else:
            if not self.modo_um_jogador:
                self.jogador_atual_idx += 1
            self.root.after(2000, self.iniciar_rodada_jogador)

    def desistir_jogador(self):
        if not self.rodada_ativa or self.modo_um_jogador:
            return
        
        nome = self.jogador_atual
        
        if messagebox.askyesno("Desistir", f"❓ {nome}, tem certeza que quer desistir?"):
            self.rodada_ativa = False
            self.dados_jogadores[nome]['completou'] = True
            self.dados_jogadores[nome]['tempo'] = None
            
            self.mostrar_mensagem(f"🚪 {nome} desistiu do jogo!")
            self.lbl_jogador_atual.config(text=f"🚪 {nome} DESISTIU!", fg="#e74c3c")
            self.tocar_som('passagem_vez')
            
            self.atualizar_ranking()
            self.parar_pisca_nome()
            self.jogador_atual_idx += 1
            self.root.after(2000, self.iniciar_rodada_jogador)

    def formatar_tempo(self, segundos):
        if segundos is None:
            return "--:--"
        minutos = int(segundos // 60)
        segs = int(segundos % 60)
        return f"{minutos:02d}:{segs:02d}"

    def atualizar_ranking(self, destacar=None):
        ranking_texto = ""
        
        for nome in self.jogadores:
            dados = self.dados_jogadores[nome]
            
            if destacar == nome and self.rodada_ativa:
                prefixo = "✨ "
                sufixo = " ✨"
            else:
                prefixo = ""
                sufixo = ""
            
            if dados['completou']:
                if dados['tempo'] is not None:
                    ranking_texto += f"{prefixo}✅ {nome}: {self.formatar_tempo(dados['tempo'])} - COMPLETOU{sufixo}\n"
                else:
                    ranking_texto += f"{prefixo}🚪 {nome}: DESISTIU{sufixo}\n"
            else:
                if dados['frase_original']:
                    total_letras = sum(1 for letra in self.remover_acentos(dados['frase_original']) if letra.isalpha())
                    letras_descobertas = len([l for l in dados['letras_descobertas'] if l in self.remover_acentos(dados['frase_original'])])
                    ranking_texto += f"{prefixo}⏳ {nome}: {letras_descobertas}/{total_letras} letras - Tema: {dados['tema'] if dados['tema'] else 'Aguardando'}{sufixo}\n"
                else:
                    ranking_texto += f"{prefixo}⏳ {nome}: AGUARDANDO TEMA{sufixo}\n"
        
        self.lbl_ranking.config(text=ranking_texto, justify="left", font=("Arial", 8))

    def iniciar_pisca_nome(self):
        if self.piscando:
            self.root.after_cancel(self.piscando)
        
        def piscar():
            if not self.rodada_ativa or self.jogo_finalizado:
                return
            self.atualizar_ranking(destacar=self.jogador_atual)
            self.piscando = self.root.after(500, piscar)
        
        self.piscando = self.root.after(0, piscar)

    def parar_pisca_nome(self):
        if self.piscando:
            self.root.after_cancel(self.piscando)
            self.piscando = False
            self.atualizar_ranking()

    def mostrar_mensagem(self, mensagem):
        self.lbl_mensagem.config(text=mensagem, fg="#ffd966")
        self.root.after(3000, self.mostrar_mensagem_motivacional)

    def finalizar_jogo(self):
        self.jogo_finalizado = True
        self.jogo_em_andamento = False
        self.rodada_ativa = False
        self.btn_desistir.config(state="disabled")
        self.btn_dica.config(state="disabled")
        self.parar_pisca_nome()
        self.lbl_jogador_atual.config(text="🏆 JOGO FINALIZADO! 🏆", fg="#ffd966")
        
        self.parar_musica_ambiente()
        self.tocar_som('fim_jogo')
        
        for btn in self.botoes_letras.values():
            btn.config(state="disabled", bg="#95a5a6")
        
        # Coletar resultados
        resultados = []
        for nome in self.jogadores:
            dados = self.dados_jogadores[nome]
            if dados['completou'] and dados['tempo'] is not None:
                resultados.append((nome, dados['tempo'], dados['frase_original'], dados['tema'], "COMPLETOU"))
            elif dados['completou'] and dados['tempo'] is None:
                resultados.append((nome, None, dados['frase_original'], dados['tema'], "DESISTIU"))
            else:
                resultados.append((nome, None, dados['frase_original'], dados['tema'], "INCOMPLETO"))
        
        # Ordenar por tempo (menor primeiro)
        resultados.sort(key=lambda x: x[1] if x[1] is not None else float('inf'))
        
        # Construir texto do resultado final
        resultado_texto = ""
        
        for i, (nome, tempo, frase, tema, status) in enumerate(resultados):
            if i == 0 and tempo is not None:
                medalha = "🥇"
            elif i == 1 and tempo is not None:
                medalha = "🥈"
            elif i == 2 and tempo is not None:
                medalha = "🥉"
            else:
                medalha = f"{i+1}º"
            
            if tempo is not None:
                tempo_str = self.formatar_tempo(tempo)
                linha_nome = f"{medalha} - {nome} ({tempo_str})"
            else:
                if status == "DESISTIU":
                    linha_nome = f"{medalha} - {nome} (DESISTIU)"
                else:
                    linha_nome = f"{medalha} - {nome} (NÃO COMPLETOU)"
            
            resultado_texto += f"{linha_nome}\n"
            resultado_texto += f"   Tema: {tema}\n"
            resultado_texto += f"   Frase: {frase}\n\n"
        
        # Limpar a área de ranking e mostrar o resultado final
        for widget in self.scrollable_ranking.winfo_children():
            widget.destroy()
        
        frame_resultado = tk.Frame(self.scrollable_ranking, bg="#2c3e50")
        frame_resultado.pack(fill="both", expand=True)
        
        texto_resultado = tk.Text(frame_resultado, wrap="word", font=("Courier New", 8), 
                                  bg="#ecf0f1", fg="#2c3e50", height=10, width=70)
        texto_resultado.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_resultado, orient="vertical", command=texto_resultado.yview)
        scrollbar.pack(side="right", fill="y")
        texto_resultado.configure(yscrollcommand=scrollbar.set)
        
        texto_resultado.insert("1.0", resultado_texto)
        texto_resultado.config(state="disabled")
        
        self.lbl_ranking_titulo.config(text="🏆 RESULTADO FINAL 🏆")

    def reiniciar_jogo(self):
        self.parar_musica_ambiente()
        self.root.destroy()
        root = tk.Tk()
        app = JogoFrases(root)
        root.mainloop()
    
    def sair_jogo(self):
        self.parar_musica_ambiente()
        if messagebox.askyesno("Sair", "❓ Tem certeza que deseja sair do VALTÉCA?"):
            self.root.quit()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = JogoFrases(root)
        root.mainloop()
    except Exception as e:
        import traceback
        messagebox.showerror("Erro VALTÉCA", f"{str(e)}\n\n{traceback.format_exc()}")