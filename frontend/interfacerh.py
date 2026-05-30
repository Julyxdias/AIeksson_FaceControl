import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# Configurações do banco de dados
DB_HOST = "****************"
DB_PORT = ****
DB_USER = "****************"
DB_PASSWORD = "***************"
DB_NAME = "**********************"

class RHApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("Reconhecimeto Facial Python/fox.ico")
        self.title("Sistema de Gestão de RH - Colaboradores")
        self.geometry("1100x750")  # Aumenta largura e altura para melhor espaçamento
        self.minsize(1000, 700)    # Tamanho mínimo para evitar problemas de layout

        # Configurações de redimensionamento da janela principal
        self.grid_rowconfigure(0, weight=0) # Frame superior com altura fixa
        self.grid_rowconfigure(1, weight=3) # Treeview ocupa mais espaço vertical
        self.grid_rowconfigure(2, weight=1) # Frame de entrada/botões
        self.grid_columnconfigure(0, weight=1)

        self._sort_column = "c.nome"  # Coluna de ordenação padrão para colaboradores (prefixado)
        self._sort_direction = "ASC" # Direção de ordenação padrão

        # --- Estilização ---
        self.style = ttk.Style(self)
        self.style.theme_use("clam") # 'clam' é um bom ponto de partida moderno

        # Customizando estilos gerais
        self.style.configure("TFrame", background="#f0f0f0") # Fundo cinza claro para frames
        self.style.configure("TLabel", font=("Segoe UI", 10), background="#f0f0f0")
        self.style.configure("TEntry", padding=6, font=("Segoe UI", 10))
        self.style.configure("TCombobox", padding=6, font=("Segoe UI", 10)) # Estilo para combobox
        self.style.configure("TButton",
                               font=("Segoe UI", 10, "bold"),
                               padding=8,
                               background="#4CAF50", # Um tom de verde agradável
                               foreground="white",
                               relief="flat", # Aparência plana para botões
                               borderwidth=0)
        self.style.map("TButton",
                       background=[('active', '#45a049')], # Verde mais escuro ao passar o mouse
                       foreground=[('pressed', 'white'), ('active', 'white')])

        # Estilos do Treeview
        self.style.configure("Treeview",
                               font=("Segoe UI", 10),
                               rowheight=28, # Altura da linha ligeiramente aumentada
                               background="white",
                               foreground="black",
                               fieldbackground="white",
                               borderwidth=1,
                               relief="solid") # Adiciona uma borda sutil
        self.style.map("Treeview", background=[('selected', '#a8d1ff')]) # Azul claro na seleção

        self.style.configure("Treeview.Heading",
                               font=("Segoe UI", 11, "bold"),
                               background="#007acc", # Cabeçalho azul original
                               foreground="white",
                               relief="flat")
        self.style.map("Treeview.Heading",
                       background=[('active', '#005f99')])

        # --- Frames de Layout Principal ---
        # Frame superior para título ou logo
        top_frame = ttk.Frame(self, padding="15 10")
        top_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(top_frame, text="Gestão de Colaboradores",
                  font=("Segoe UI", 18, "bold"), background="#f0f0f0").pack(pady=5)
        
        # Frame para o Treeview (lista de dados)
        tree_frame = ttk.Frame(self, padding="10 0 10 10")
        tree_frame.grid(row=1, column=0, sticky="nsew")

        # Frame para campos de entrada e botões de ação
        input_button_frame = ttk.Frame(self, padding="10 10 10 15")
        input_button_frame.grid(row=2, column=0, sticky="ew")
        input_button_frame.grid_columnconfigure(0, weight=1) # Frame de campos
        input_button_frame.grid_columnconfigure(1, weight=0) # Frame de botões

        # --- Barra de Busca ---
        search_frame = ttk.Frame(input_button_frame, padding="5")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1) # Faz a entrada de busca expansível

        ttk.Label(search_frame, text="Buscar:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filtrar_dados) # Filtra ao soltar a tecla
        
        ttk.Button(search_frame, text="Limpar Busca", command=lambda: [self.search_entry.delete(0, tk.END), self.carregar_colaboradores()], style="TButton").grid(row=0, column=2, padx=5)

        # --- Configuração do Treeview ---
        self.tree = ttk.Treeview(tree_frame, show="headings") # Colunas são definidas dinamicamente
        
        self.tree.pack(fill="both", expand=True)

        # Barra de rolagem para o Treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.tag_configure('oddrow', background='#e8f2ff') # Azul mais claro para linhas ímpares
        self.tree.tag_configure('evenrow', background='white')

        # Vincula evento de seleção do Treeview e clique no cabeçalho para ordenação
        self.tree.bind("<<TreeviewSelect>>", self.preencher_campos)
        self.tree.bind("<Button-1>", self.on_treeview_heading_click)

        # --- Layout dos Campos de Entrada ---
        fields_frame = ttk.Frame(input_button_frame, padding="10")
        fields_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        fields_frame.grid_columnconfigure(1, weight=1) # Faz a coluna de entrada expansível

        # Rótulos e Entradas
        labels = ["Matrícula:", "Nome:", "Cargo:", "Escala:", "Horário Contratual:", "Departamento:", "Empresa:", "ID Empresa:"]
        self.entry_matricula = ttk.Entry(fields_frame)
        self.entry_nome = ttk.Entry(fields_frame)
        self.entry_cargo = ttk.Entry(fields_frame)
        self.entry_escala = ttk.Entry(fields_frame)
        self.entry_horariocontratual = ttk.Entry(fields_frame)

        # Combobox para Departamento
        self.departamento_names = [] # Para armazenar os nomes para a combobox
        self.departamento_map = {} # Para mapear nome para ID: {nome: id}
        self.departamento_empresa_map = {} # Para mapear ID do departamento para ID da empresa: {id_departamento: id_empresa}
        self.combo_departamento = ttk.Combobox(fields_frame, state="readonly")

        # Combobox para Empresa
        self.empresa_names = [] # Para armazenar os nomes para a combobox
        self.empresa_map = {} # Para mapear nome para ID: {nome: id}
        # Mapeia ID da empresa para seu nome fantasia (para uso em on_departamento_selected)
        self.empresa_id_to_name_map = {} 
        self.combo_empresa = ttk.Combobox(fields_frame, state="readonly") # A empresa será preenchida automaticamente

        # Novo: Campo de entrada para ID Empresa (somente leitura)
        self.entry_idempresa = ttk.Entry(fields_frame, state='readonly') # Campo somente leitura

        self.entry_widgets = [
            self.entry_matricula, self.entry_nome, self.entry_cargo,
            self.entry_escala, self.entry_horariocontratual,
            self.combo_departamento, self.combo_empresa, self.entry_idempresa # Adicionado comboboxes e entry_idempresa
        ]

        for i, label_text in enumerate(labels):
            ttk.Label(fields_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            if i < 5: # As 5 primeiras são Entries padrão
                self.entry_widgets[i].grid(row=i, column=1, sticky="ew", padx=5, pady=3)
            elif i == 5: # Combobox de Departamento
                self.combo_departamento.grid(row=i, column=1, sticky="ew", padx=5, pady=3)
                self.combo_departamento.bind("<<ComboboxSelected>>", self.on_departamento_selected)
            elif i == 6: # Combobox de Empresa
                self.combo_empresa.grid(row=i, column=1, sticky="ew", padx=5, pady=3)
                self.combo_empresa.bind("<<ComboboxSelected>>", self.on_empresa_selected)  # <-- Adiciona esta linha
            elif i == 7: # Campo de ID Empresa
                self.entry_idempresa.grid(row=i, column=1, sticky="ew", padx=5, pady=3)

        # --- Layout dos Botões ---
        button_actions_frame = ttk.Frame(input_button_frame, padding="10")
        button_actions_frame.grid(row=1, column=1, sticky="nswe", padx=5, pady=5)

        # Define botões e seus comandos com um estilo consistente
        buttons_data = [
            ("Adicionar", self.adicionar_colaborador, "#4CAF50"), # Verde para Adicionar
            ("Editar", self.editar_colaborador, "#2196F3"),      # Azul para Editar
            ("Excluir", self.excluir_colaborador, "#f44336"),     # Vermelho para Excluir
            ("Atualizar Lista", self.carregar_colaboradores, "#FFC107"), # Âmbar para Atualizar
            ("Ver Backup de Ponto", self.carregar_backup_ponto, "#9C27B0"), # Roxo para Backup
            ("Voltar para Colaboradores", self.carregar_colaboradores_default, "#00BCD4") # Ciano para Voltar
        ]

        # Cria botões com estilos distintos
        for text, command, color in buttons_data:
            btn_style_name = f"Custom.{color}.TButton"
            self.style.configure(btn_style_name,
                                 background=color,
                                 foreground="white",
                                 font=("Segoe UI", 10, "bold"),
                                 padding=8,
                                 relief="flat",
                                 borderwidth=0)
            self.style.map(btn_style_name,
                           background=[('active', self.darken_color(color, 20))], # Escurece ao passar o mouse
                           foreground=[('pressed', 'white'), ('active', 'white')])
            
            btn = ttk.Button(button_actions_frame, text=text, command=command, style=btn_style_name)
            btn.pack(fill="x", pady=5)

        # Configuração inicial
        self.conectar_banco()
        self.load_departamentos() # Carrega departamentos para a combobox
        self.load_empresas() # Carrega empresas para a combobox
        self.carregar_colaboradores() # Carrega a visão padrão inicialmente

    def darken_color(self, hex_color, factor):
        """Escurece uma cor hexadecimal por um dado fator (0-100)."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darker_rgb = tuple(max(0, c - int(c * factor / 100)) for c in rgb)
        return '#%02x%02x%02x' % darker_rgb
    def on_empresa_selected(self, event):
        """Filtra os departamentos e ID da empresa com base na empresa selecionada."""
        empresa_nome = self.combo_empresa.get()
        empresa_id = self.empresa_map.get(empresa_nome)

        if empresa_id:
            # Preenche o ID da empresa
            self.entry_idempresa.config(state='normal')
            self.entry_idempresa.delete(0, tk.END)
            self.entry_idempresa.insert(0, str(empresa_id))
            self.entry_idempresa.config(state='readonly')

            # Atualiza os departamentos que pertencem a essa empresa
            departamentos_filtrados = [
                nome for nome, id_dep in self.departamento_map.items()
                if self.departamento_empresa_map.get(id_dep) == empresa_id
            ]
            self.combo_departamento['values'] = departamentos_filtrados
            self.combo_departamento.set("")  # Limpa a seleção atual
        else:
            self.combo_departamento['values'] = []
            self.entry_idempresa.config(state='normal')
            self.entry_idempresa.delete(0, tk.END)
            self.entry_idempresa.config(state='readonly')


    def conectar_banco(self):
        """Tenta conectar ao banco de dados MySQL."""
        try:
            self.conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4'
            )
            messagebox.showinfo("Conexão", "Conectado ao banco de dados com sucesso!")
        except mysql.connector.Error as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados:\n{e}")
            self.destroy() # Fecha o aplicativo se a conexão falhar

    def load_departamentos(self):
        """Carrega os nomes dos departamentos e seus IDs para a combobox."""
        try:
            cursor = self.conn.cursor()
            # SELECT: idEmpresa (como está no seu banco de dados para a FK em Departamento)
            cursor.execute("SELECT IdDepartamento, nome_departamento, idEmpresa FROM Departamento ORDER BY nome_departamento")
            rows = cursor.fetchall()
            self.departamento_names = []
            self.departamento_map = {} # {nome: id}
            self.departamento_empresa_map = {} # {id_departamento: id_empresa}

            for dept_id, dept_name, emp_id in rows:
                self.departamento_names.append(dept_name)
                self.departamento_map[dept_name] = dept_id
                self.departamento_empresa_map[dept_id] = emp_id

            self.combo_departamento['values'] = self.departamento_names
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro ao Carregar Departamentos", f"Não foi possível carregar os departamentos:\n{e}")

    def load_empresas(self):
        """Carrega os nomes das empresas e seus IDs para a combobox."""
        try:
            cursor = self.conn.cursor()
            # AGORA O SELECT BUSCA 'empresa' (tudo minúsculo) da BDEmpresaInterno
            cursor.execute("SELECT empresa, nome_fantasia FROM BDEmpresaInterno ORDER BY nome_fantasia")
            rows = cursor.fetchall()
            self.empresa_names = []
            self.empresa_map = {} # {nome: id}
            # Mapeia ID da empresa para seu nome fantasia
            self.empresa_id_to_name_map = {row[0]: row[1] for row in rows} 

            for emp_id, emp_name in rows:
                self.empresa_names.append(emp_name)
                self.empresa_map[emp_name] = emp_id

            self.combo_empresa['values'] = self.empresa_names
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro ao Carregar Empresas", f"Não foi possível carregar as empresas:\n{e}")

    def on_departamento_selected(self, event):
        """Atualiza a combobox de empresa e o campo idEmpresa com base no departamento selecionado."""
        selected_dept_name = self.combo_departamento.get()
        selected_dept_id = self.departamento_map.get(selected_dept_name)

        # Habilita o campo idEmpresa para escrita temporária
        self.entry_idempresa.config(state='normal') 
        self.entry_idempresa.delete(0, tk.END)

        if selected_dept_id is not None:
            associated_emp_id = self.departamento_empresa_map.get(selected_dept_id)
            if associated_emp_id is not None:
                # Preenche a combobox de empresa com o nome
                emp_name = self.empresa_id_to_name_map.get(associated_emp_id)
                self.combo_empresa.set(emp_name)
                # Preenche o campo idEmpresa com o ID numérico
                self.entry_idempresa.insert(0, str(associated_emp_id))
            else:
                self.combo_empresa.set("") # Limpa se nenhuma empresa for encontrada para este departamento
        else:
            self.combo_empresa.set("") # Limpa se nenhum departamento for selecionado ou ID não encontrado
        
        # Desabilita o campo idEmpresa novamente
        self.entry_idempresa.config(state='readonly')


    def on_treeview_heading_click(self, event):
        """Lida com cliques nos cabeçalhos das colunas do Treeview para ordenação."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column_id = self.tree.identify_column(event.x) # Retorna #1, #2, etc.
            column_name = self.tree.heading(column_id, "text") # Obtém o texto exibido no cabeçalho

            # Mapeia nomes de exibição para nomes de colunas reais do banco de dados (prefixados para JOINs)
            # Os prefixos (c., d., e.) são importantes quando há joins para evitar ambiguidades
            column_map_colaboradores = {
                "Matrícula": "c.matricula",
                "Nome Completo": "c.nome",
                "Cargo": "c.cargo",
                "Escala": "c.escala",
                "Horário Contratual": "c.horariocontratual",
                "Departamento": "d.nome_departamento",
                "Empresa": "e.nome_fantasia",
                "ID Empresa": "e.empresa" # CORRIGIDO: Agora aponta para 'e.empresa' (tudo minúsculo)
            }
            column_map_backup_ponto = {
                "Matrícula": "matricula",
                "Nome do Colaborador": "nome_colaborador",
                "Data Registro": "data_registro",
                "Entrada": "horario_entrada",
                "Saída": "horario_saida",
                "Departamento": "nome_departamento"
            }
            
            # Determina qual mapeamento usar com base nas colunas atuais do Treeview
            if "Data Registro" in self.tree["columns"]: # Verifica se é a visão de BackupPontoCompleto
                db_column = column_map_backup_ponto.get(column_name)
            else: # Assume visão de Colaboradores
                db_column = column_map_colaboradores.get(column_name)

            if db_column:
                # Alterna a direção se a mesma coluna for clicada novamente
                if self._sort_column == db_column:
                    self._sort_direction = "DESC" if self._sort_direction == "ASC" else "ASC"
                else:
                    self._sort_column = db_column
                    self._sort_direction = "ASC"
                
                self.filtrar_dados() # Recarrega os dados com a nova ordem de classificação

    def carregar_backup_ponto(self):
        """Carrega e exibe dados da view BackupPontoCompleto."""
        try:
            # Atualiza as colunas do Treeview para BackupPontoCompleto
            colunas = ("Matrícula", "Nome do Colaborador", "Data Registro", "Entrada", "Saída", "Departamento")
            self.tree["columns"] = colunas
            for col_name in colunas:
                self.tree.heading(col_name, text=col_name, anchor="w")
                if col_name in ["Matrícula", "Entrada", "Saída"]:
                    self.tree.column(col_name, width=100, minwidth=60, stretch=False)
                else:
                    self.tree.column(col_name, width=150, minwidth=100)

            # Define a ordenação padrão para a visão de backup
            self._sort_column = "data_registro"
            self._sort_direction = "DESC"

            self.filtrar_dados() # Usa o filtro para carregar com as novas colunas e ordenação
            self.limpar_campos() # Limpa os campos ao trocar de visão

        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar backup de ponto:\n{e}")

    def carregar_colaboradores_default(self):
        """Redefine as colunas do Treeview para as colunas de Colaborador e recarrega."""
        # Redefine as colunas do Treeview para as colunas de Colaborador
        colunas_colaborador = ("matricula", "nome", "cargo", "escala", "horariocontratual", "departamento", "empresa", "idempresa_view")
        self.tree["columns"] = colunas_colaborador
        self.tree.heading("matricula", text="Matrícula", anchor="w")
        self.tree.column("matricula", width=80, minwidth=60, stretch=False)
        self.tree.heading("nome", text="Nome Completo", anchor="w")
        self.tree.column("nome", width=180, minwidth=150)
        self.tree.heading("cargo", text="Cargo", anchor="w")
        self.tree.column("cargo", width=120, minwidth=100)
        self.tree.heading("escala", text="Escala", anchor="w")
        self.tree.column("escala", width=100, minwidth=80)
        self.tree.heading("horariocontratual", text="Horário Contratual", anchor="w")
        self.tree.column("horariocontratual", width=120, minwidth=100)
        self.tree.heading("departamento", text="Departamento", anchor="w")
        self.tree.column("departamento", width=150, minwidth=100)
        self.tree.heading("empresa", text="Empresa", anchor="w")
        self.tree.column("empresa", width=150, minwidth=100)
        self.tree.heading("idempresa_view", text="ID Empresa", anchor="w") # Nova coluna de ID Empresa
        self.tree.column("idempresa_view", width=80, minwidth=50, stretch=False) # Largura menor para ID
        
        # Define a ordenação padrão para a visão de colaboradores
        self._sort_column = "c.nome" # Mantém prefixo para o JOIN
        self._sort_direction = "ASC"
        
        self.filtrar_dados() # Usa o filtro para carregar com as novas colunas e ordenação
        self.limpar_campos() # Limpa os campos ao mudar de visão

    def carregar_colaboradores(self):
        """Carrega e exibe todos os colaboradores (visão padrão)."""
        self.carregar_colaboradores_default()

    def filtrar_dados(self, event=None):
        """Filtra e ordena os dados no Treeview com base no termo de busca e na ordem de classificação atual."""
        search_term = self.search_entry.get().strip()
        
        # Limpa o Treeview primeiro
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            cursor = self.conn.cursor()
            
            # Determina qual tabela/view consultar com base nas colunas atuais do Treeview
            is_backup_ponto_view = "Data Registro" in self.tree["columns"]

            if is_backup_ponto_view:
                query = f"""
                    SELECT matricula, nome_colaborador, data_registro, horario_entrada, horario_saida, nome_departamento
                    FROM BackupPontoCompleto
                    WHERE matricula LIKE %s OR nome_colaborador LIKE %s OR nome_departamento LIKE %s
                    ORDER BY {self._sort_column} {self._sort_direction}
                """
                params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
                
            else: # Visão de Colaboradores (SQL com JOINs e seleção de e.empresa)
                query = f"""
                    SELECT
                        c.matricula,
                        c.nome,
                        c.cargo,
                        c.escala,
                        c.horariocontratual,
                        d.nome_departamento,
                        e.nome_fantasia,
                        e.empresa -- CORRIGIDO: Seleciona a PK 'empresa' da BDEmpresaInterno
                    FROM
                        Colaborador c
                    LEFT JOIN
                        Departamento d ON c.idDepartamento = d.IdDepartamento
                    LEFT JOIN
                        BDEmpresaInterno e ON d.idEmpresa = e.empresa -- CORRIGIDO: O JOIN usa 'e.empresa'
                    WHERE
                        c.matricula LIKE %s OR c.nome LIKE %s OR c.cargo LIKE %s OR c.escala LIKE %s
                        OR d.nome_departamento LIKE %s OR e.nome_fantasia LIKE %s OR e.empresa LIKE %s -- CORRIGIDO: Busca por 'e.empresa'
                    ORDER BY {self._sort_column} {self._sort_direction}
                """
                params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%",
                          f"%{search_term}%", f"%{search_term}%", f"%{search_term}%") # Parâmetros para todos os campos de busca
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows):
                tag = 'oddrow' if i % 2 else 'evenrow'
                self.tree.insert("", "end", values=row, tags=(tag,))
            
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro de Busca/Carregamento", f"Erro ao filtrar ou carregar dados:\n{e}")

    def adicionar_colaborador(self):
        """Adiciona um novo colaborador ao banco de dados."""
        matricula = self.entry_matricula.get().strip()
        nome = self.entry_nome.get().strip()
        cargo = self.entry_cargo.get().strip()
        escala = self.entry_escala.get().strip()
        horariocontratual = self.entry_horariocontratual.get().strip()
        departamento_name = self.combo_departamento.get().strip() # Obtém o nome do departamento selecionado

        # Obtém o ID para o departamento selecionado
        id_departamento = self.departamento_map.get(departamento_name)

        if not matricula or not nome:
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha a **Matrícula** e o **Nome** do colaborador.")
            return

        if not departamento_name or id_departamento is None:
            messagebox.showwarning("Departamento Obrigatório", "Por favor, selecione um **Departamento** válido.")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT matricula FROM Colaborador WHERE matricula = %s", (matricula,))
            if cursor.fetchone():
                messagebox.showwarning("Aviso", "Já existe um colaborador com esta **Matrícula**.")
            else:
                cursor.execute(
                    "INSERT INTO Colaborador (matricula, nome, cargo, escala, horariocontratual, idDepartamento) VALUES (%s, %s, %s, %s, %s, %s)",
                    (matricula, nome, cargo, escala, horariocontratual, id_departamento)
                )
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Colaborador adicionado com sucesso!")
                self.carregar_colaboradores()
                self.limpar_campos()
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o colaborador:\n{e}")

    def excluir_colaborador(self):
        """Exclui um colaborador selecionado do banco de dados."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Seleção Necessária", "Selecione um colaborador na lista para excluí-lo.")
            return

        # Garante que estamos na visão de Colaborador antes de tentar excluir
        if "Data Registro" in self.tree["columns"]:
            messagebox.showwarning("Operação Não Permitida", "Exclusão não disponível na visualização de Backup de Ponto. Volte para a lista de Colaboradores.")
            return

        matricula_to_delete = self.tree.item(selected_item[0])["values"][0]

        confirm = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o colaborador com Matrícula **{matricula_to_delete}**?")
        if not confirm:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Colaborador WHERE matricula = %s", (matricula_to_delete,))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Colaborador excluído com sucesso!")
            self.carregar_colaboradores()
            self.limpar_campos()
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o colaborador:\n{e}")

    def editar_colaborador(self):
        """Edita os detalhes do colaborador selecionado no banco de dados."""
        matricula = self.entry_matricula.get().strip()
        nome = self.entry_nome.get().strip()
        cargo = self.entry_cargo.get().strip()
        escala = self.entry_escala.get().strip()
        horariocontratual = self.entry_horariocontratual.get().strip()
        departamento_name = self.combo_departamento.get().strip() # Obtém o nome do departamento selecionado
        id_departamento = self.departamento_map.get(departamento_name) # Obtém o ID

        if not matricula:
            messagebox.showwarning("Matrícula Obrigatória", "A **Matrícula** é necessária para editar um colaborador. Por favor, selecione um colaborador na lista ou insira a matrícula.")
            return

        # Garante que estamos na visão de Colaborador antes de tentar editar
        if "Data Registro" in self.tree["columns"]:
            messagebox.showwarning("Operação Não Permitida", "Edição não disponível na visualização de Backup de Ponto. Volte para a lista de Colaboradores.")
            return

        try:
            cursor = self.conn.cursor()
            update_fields = []
            params = []

            # Adiciona campos para atualizar apenas se não estiverem vazios
            if nome:
                update_fields.append("nome = %s")
                params.append(nome)
            if cargo:
                update_fields.append("cargo = %s")
                params.append(cargo)
            if escala:
                update_fields.append("escala = %s")
                params.append(escala)
            if horariocontratual:
                update_fields.append("horariocontratual = %s")
                params.append(horariocontratual)
            # Adiciona departamento para atualizar
            if departamento_name and id_departamento is not None:
                update_fields.append("idDepartamento = %s")
                params.append(id_departamento)
            elif departamento_name == "" and self.combo_departamento.current() == -1: # Se a combobox foi explicitamente limpa
                update_fields.append("idDepartamento = %s")
                params.append(None) # Define como NULL se limpo

            if not update_fields:
                messagebox.showwarning("Nenhuma Alteração", "Nenhum campo para atualizar foi preenchido.")
                cursor.close()
                return

            params.append(matricula)
            sql = f"UPDATE Colaborador SET {', '.join(update_fields)} WHERE matricula = %s"
            
            cursor.execute(sql, tuple(params))
            self.conn.commit()
            
            if cursor.rowcount == 0:
                messagebox.showwarning("Aviso", f"Nenhum colaborador encontrado com a matrícula {matricula} para editar.")
            else:
                messagebox.showinfo("Sucesso", "Colaborador atualizado com sucesso!")
            
            self.carregar_colaboradores()
            self.limpar_campos()
            cursor.close()
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao editar o colaborador:\n{e}")

    def preencher_campos(self, event):
        """Preenche os campos de entrada quando um item do Treeview é selecionado."""
        selected_item = self.tree.selection()
        if not selected_item:
            self.limpar_campos() # Limpa os campos se nada for selecionado
            return
        
        try:
            values = self.tree.item(selected_item[0])["values"]
            
            # A lista de colunas "self.tree['columns']" pode ser usada para uma verificação mais robusta,
            # mas a quantidade de valores costuma ser suficiente para distinguir as duas visões.
            if "matricula" in self.tree["columns"] and len(values) >= 8: # Visão de Colaborador agora com 8 colunas
                self.entry_matricula.delete(0, tk.END)
                self.entry_matricula.insert(0, values[0])
                self.entry_nome.delete(0, tk.END)
                self.entry_nome.insert(0, values[1])
                self.entry_cargo.delete(0, tk.END)
                self.entry_cargo.insert(0, values[2] if values[2] else "")
                self.entry_escala.delete(0, tk.END)
                self.entry_escala.insert(0, values[3] if values[3] else "")
                self.entry_horariocontratual.delete(0, tk.END)
                self.entry_horariocontratual.insert(0, values[4] if values[4] else "")

                # Define a Combobox para Departamento
                departamento_name = values[5] if values[5] else ""
                self.combo_departamento.set(departamento_name)

                # Define a Combobox para Empresa
                empresa_name = values[6] if values[6] else ""
                self.combo_empresa.set(empresa_name)

                # Define o campo de ID Empresa (habilita temporariamente para escrita)
                self.entry_idempresa.config(state='normal')
                self.entry_idempresa.delete(0, tk.END)
                self.entry_idempresa.insert(0, values[7] if values[7] else "") # Insere o ID Empresa
                self.entry_idempresa.config(state='readonly')
            else: # Provavelmente a visão de BackupPontoCompleto ou outra, limpa os campos
                self.limpar_campos()
        except IndexError:
            # Captura erros se o número de colunas não corresponder ao esperado
            self.limpar_campos() 

    def limpar_campos(self):
        """Limpa todos os campos de entrada."""
        for entry in self.entry_widgets:
            if isinstance(entry, ttk.Entry):
                # Para entry_idempresa, precisamos habilitar antes de limpar
                if entry == self.entry_idempresa:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    entry.config(state='readonly') # Desabilita novamente
                else:
                    entry.delete(0, tk.END)
            elif isinstance(entry, ttk.Combobox):
                entry.set("") # Limpa a seleção da combobox

if __name__ == "__main__":
    app = RHApp()
    app.mainloop()
