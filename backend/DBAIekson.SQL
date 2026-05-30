-- Criar tabela BDEmpresaInterno
CREATE TABLE BDEmpresaInterno (
    empresa INT NOT NULL, -- Chave Primária
    nome_fantasia VARCHAR(100) DEFAULT NULL, 
    cnpj VARCHAR(14) DEFAULT NULL,
    endereco TEXT DEFAULT NULL,
    data_aquisicao DATE DEFAULT NULL,
    plano_contratado VARCHAR(20) DEFAULT NULL,
    status_contrato VARCHAR(10) DEFAULT NULL,
    qtd_colaboradores INT DEFAULT NULL,
    qtd_catracas INT DEFAULT NULL,
    PRIMARY KEY (empresa),
    CONSTRAINT BDEmpresaInterno_chk_1 CHECK (plano_contratado IN ('Starter', 'Pro', 'Ultra')),
    CONSTRAINT BDEmpresaInterno_chk_2 CHECK (status_contrato IN ('Ativo', 'Inativo')),
    CONSTRAINT BDEmpresaInterno_chk_3 CHECK (qtd_colaboradores >= 0 OR qtd_colaboradores IS NULL),
    CONSTRAINT BDEmpresaInterno_chk_4 CHECK (qtd_catracas >= 0 OR qtd_catracas IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Criar tabela Departamento
CREATE TABLE Departamento (
    idDepartamento INT NOT NULL,
    idEmpresa INT DEFAULT NULL, 
    nome_departamento VARCHAR(100) NOT NULL, 
    PRIMARY KEY (idDepartamento),
    INDEX idx_fk_idEmpresa (idEmpresa ASC), 
    CONSTRAINT fk_Departamento_Empresa
        FOREIGN KEY (idEmpresa)
        REFERENCES BDEmpresaInterno (empresa)
        ON DELETE SET NULL 
        ON UPDATE CASCADE 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Criar tabela Colaborador com ordem de colunas organizada
CREATE TABLE Colaborador (
    matricula VARCHAR(30) NOT NULL,
    nome VARCHAR(100) DEFAULT NULL,
  	encoding LONGBLOB DEFAULT NULL,                 
  	empresa INT DEFAULT NULL,                       
    escala VARCHAR(20) DEFAULT NULL,
    horariocontratual FLOAT DEFAULT NULL,
  	idDepartamento INT DEFAULT NULL,                
 		cargo VARCHAR(30) DEFAULT NULL,                 
    
    PRIMARY KEY (matricula),

    -- Índices para otimização de chaves estrangeiras e colunas frequentemente consultadas
    INDEX idx_col_idDepartamento (idDepartamento ASC),
    INDEX idx_col_empresa (empresa ASC),
    INDEX idx_col_cargo (cargo ASC), 

    -- Restrições de Chave Estrangeira
    CONSTRAINT fk_Colaborador_Departamento
        FOREIGN KEY (idDepartamento)
        REFERENCES Departamento (idDepartamento)
        ON DELETE SET NULL  
        ON UPDATE CASCADE,  

    CONSTRAINT fk_Colaborador_Empresa
        FOREIGN KEY (empresa)
        REFERENCES BDEmpresaInterno (empresa)
        ON DELETE SET NULL  
        ON UPDATE CASCADE,  

    -- Restrição CHECK para os valores permitidos na coluna 'cargo'
    CONSTRAINT chk_Colaborador_cargo CHECK (
        cargo IN (
            'Diretor',
            'Gerente',
            'Coordenador',
            'Supervisor',
            'Analista',
            'Assistente',
            'Auxiliar',
            'Estagiário',
            'Aprendiz'
        ) OR cargo IS NULL 
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Criar tabela Ponto
CREATE TABLE Ponto (
    idPonto BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    idColaborador VARCHAR(30) DEFAULT NULL, -- FK para Colaborador (matricula)
    dataRegistro DATE DEFAULT NULL,
    horarioentrada TIME DEFAULT NULL,
    horariosaida TIME DEFAULT NULL,
    PRIMARY KEY (idPonto),
    UNIQUE KEY idx_idPonto_unique (idPonto),
    KEY idx_idColaborador_ponto (idColaborador), -- Renomeado para evitar conflito
    CONSTRAINT fk_Ponto_Colaborador FOREIGN KEY (idColaborador) REFERENCES Colaborador (matricula) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Criar tabela BackupPontoCompleto
CREATE TABLE BackupPontoCompleto (
    idBackup BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    idEmpresa INT DEFAULT NULL, -- Para armazenar o ID da empresa do colaborador
    nome_fantasia VARCHAR(100) DEFAULT NULL, -- Para armazenar o nome fantasia da empresa
    matricula VARCHAR(30) DEFAULT NULL,
    nome_colaborador VARCHAR(100) DEFAULT NULL,
    encoding LONGBLOB, -- Para armazenar o encoding do colaborador
    nome_departamento VARCHAR(100) DEFAULT NULL, -- Para armazenar o nome do departamento
    funcao VARCHAR(30) DEFAULT NULL,
    escala VARCHAR(20) DEFAULT NULL,
    data_registro DATE DEFAULT NULL,
    horariocontratual FLOAT DEFAULT NULL,
    horario_entrada TIME DEFAULT NULL,
    horario_saida TIME DEFAULT NULL,
    data_backup TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (idBackup),
    UNIQUE KEY idx_idBackup_unique (idBackup)
    -- Opcional: Adicionar UNIQUE KEY (matricula, data_registro) se cada colaborador só tiver um registro por dia no backup.
    -- UNIQUE KEY uq_matricula_data (matricula, data_registro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Reabilitar verificações de chaves estrangeiras
SET FOREIGN_KEY_CHECKS = 1;
    -- Tenta obter um nome de departamento. Se todos forem NULL, o resultado será NULL.
    COALESCE(d.rh, d.marketing, d.logistica, d.ti, d.engenharia) AS nome_departamento_calculado,
    e.empresa, -- Mapeando e.empresa (INT) para nome_empresa (TEXT). Pode ser necessário ajustar para um nome descritivo da empresa.
    e.status_contrato
  FROM Colaborador c
  LEFT JOIN Departamento d ON c.idDepartamento = d.idDepartamento
  LEFT JOIN BDEmpresaInterno e ON c.empresa = e.empresa
  WHERE c.matricula = NEW.idColaborador;
END;


