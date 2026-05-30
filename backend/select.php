<?php
// select.php

// Define o cabeçalho da resposta como JSON desde o início
header('Content-Type: application/json');

// Configurações do banco de dados (IMPORTANTE: Substitua com seus dados reais)
$host = "www.***************.com.br:3306"; // Endereço do servidor do banco de dados
$username = "***************";             // Nome de usuário para o banco de dados
$password = "***************";             // Senha para o banco de dados
$dbname = "***************";               // Nome do banco de dados

// Cria a conexão com o banco de dados MySQL
$conn = new mysqli($host, $username, $password, $dbname);

// Verifica se a conexão foi bem-sucedida
if ($conn->connect_error) {
    http_response_code(500); // Código HTTP para Internal Server Error
    die(json_encode([
        "status" => "error",
        "message" => "Conexão com o banco de dados falhou: " . $conn->connect_error
    ]));
}

$response = [];
$tableName = "Ponto"; // Nome da tabela

// Prepara a consulta SQL para buscar todos os dados da tabela especificada
// Ex: "SELECT * FROM {$tableName} ORDER BY id DESC" se você tiver uma coluna 'id' para ordenação
$sql_select = "SELECT * FROM {$tableName}";
$result_select = $conn->query($sql_select);

if ($result_select) {
    $data = [];
    if ($result_select->num_rows > 0) {
        while ($row = $result_select->fetch_assoc()) {
            $data[] = $row;
        }
        // Dados foram recuperados e estão em $data.
        // Prepara a resposta com os dados recuperados.
        $response = [
            "status" => "success",
            "message" => "Dados recuperados da tabela '{$tableName}'.",
            "count" => $result_select->num_rows,
            "data" => $data
        ];

        // Agora, tenta deletar TODOS os registros da tabela.
        // ATENÇÃO: Isto deletará todos os dados da tabela '{$tableName}'.
        // Se você precisar deletar apenas os registros específicos que foram lidos
        // e a tabela puder ter outros dados, você precisará de uma lógica de DELETE mais específica
        // (ex: DELETE FROM {$tableName} WHERE id IN (id1, id2, ...)).
        $sql_delete = "DELETE FROM {$tableName}";
        if ($conn->query($sql_delete)) {
            $response["message"] .= " Todos os registros da tabela '{$tableName}' foram deletados com sucesso.";
        } else {
            // Falha na deleção, atualiza a mensagem e o status na resposta
            $response["status"] = "partial_error"; // Indica sucesso na leitura, mas falha na deleção
            $response["message"] .= " ERRO: Falha ao deletar os registros da tabela '{$tableName}': " . $conn->error;
        }

    } else {
        // Nenhum registro encontrado na tabela
        $response = [
            "status" => "success", // A consulta foi bem-sucedida, mas não retornou dados
            "message" => "Nenhum registro encontrado na tabela '{$tableName}'.",
            "count" => 0,
            "data" => []
        ];
    }
    $result_select->free(); // Libera a memória do resultado da seleção
} else {
    // Erro ao executar a consulta SELECT
    http_response_code(500);
    $response = [
        "status" => "error",
        "message" => "Erro ao executar a consulta SELECT na tabela '{$tableName}': " . $conn->error
    ];
}

$conn->close(); // Fecha a conexão com o banco de dados

// Envia a resposta JSON final
echo json_encode($response);
?>
