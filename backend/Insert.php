<?php
// Nome do arquivo: por exemplo, registrar_ponto_api.php
$start_time = microtime(true);
header('Content-Type: application/json');

// Configurações do banco de dados
$host = "www.**************.com.br:3306";
$username = "***************";
$password = "****************";
$dbname = "*******************";

$conn = new mysqli($host, $username, $password, $dbname);

if ($conn->connect_error) {
    http_response_code(500);
    die(json_encode(["status" => "error", "message" => "Conexão com o banco de dados falhou: " . $conn->connect_error]));
}

$response = [];
$input = json_decode(file_get_contents('php://input'), true);

$horario_atual_passagem = isset($input['horarioentrada']) ? $input['horarioentrada'] : null;
error_log("DEBUG PHP: HorarioAtualPassagem (após ler input): '" . $horario_atual_passagem . "'"); // Log existente

$dataRegistro_input = isset($input['dataRegistro']) ? $input['dataRegistro'] : null;
$encoding_recebido_base64 = isset($input['encoding']) ? $input['encoding'] : null;

// Define o intervalo mínimo entre batidas em segundos (ex: 30 segundos)
const MIN_PUNCH_INTERVAL_SECONDS = 20; // Ajuste para 0 ou outro valor para testar

if ($encoding_recebido_base64 && $dataRegistro_input && $horario_atual_passagem) {

    $encoding_binario_para_db = base64_decode($encoding_recebido_base64);

    if ($encoding_binario_para_db === false) {
        $response = ["status" => "error", "message" => "Encoding em formato Base64 inválido."];
    } else {
        $sql_colaborador = "SELECT matricula, nome, last_punch_timestamp FROM Colaborador WHERE encoding = ?";
        $stmt_colaborador = $conn->prepare($sql_colaborador);

        if ($stmt_colaborador === false) {
            $response = ["status" => "error", "message" => "Erro na preparação da consulta Colaborador: " . $conn->error];
        } else {
            $stmt_colaborador->bind_param("s", $encoding_binario_para_db);
            $stmt_colaborador->execute();
            $result_colaborador = $stmt_colaborador->get_result();

            if ($result_colaborador && $result_colaborador->num_rows > 0) {
                $colaborador_data = $result_colaborador->fetch_assoc();
                $matricula_colaborador = $colaborador_data['matricula'];
                $nome_colaborador = $colaborador_data['nome'];
                $last_punch_timestamp_db = $colaborador_data['last_punch_timestamp'];
                $stmt_colaborador->close();

                $current_punch_full_timestamp = $dataRegistro_input . ' ' . $horario_atual_passagem;

                $time_current_punch = strtotime($current_punch_full_timestamp);
                $time_last_punch_db = strtotime($last_punch_timestamp_db);

                if ($last_punch_timestamp_db !== null && ($time_current_punch - $time_last_punch_db) < MIN_PUNCH_INTERVAL_SECONDS) {
                    $response = [
                        "status" => "blocked",
                        "message" => "Batida consecutiva bloqueada. Aguarde " . MIN_PUNCH_INTERVAL_SECONDS . " segundos entre as batidas.",
                        "matricula" => $matricula_colaborador,
                        "nome" => $nome_colaborador,
                        "ultima_batida_registrada" => $last_punch_timestamp_db,
                        "tentativa_atual" => $current_punch_full_timestamp
                    ];
                    $conn->close();
                    echo json_encode($response);
                    exit; 
                }

                $horario_entrada_para_ponto_final = null;
                $horario_saida_para_ponto_final = null;
                $tipo_registro_mensagem = "";

                // Verificar BackupPontoCompleto para definir horários de entrada/saída para Ponto
                $sql_check_backup = "SELECT horario_entrada FROM BackupPontoCompleto
                                     WHERE matricula = ? AND data_registro = ?
                                     LIMIT 1";
                $stmt_check_backup = $conn->prepare($sql_check_backup);

                if ($stmt_check_backup === false) {
                    $response = ["status" => "error", "message" => "Erro na preparação da consulta BackupPontoCompleto: " . $conn->error . " SQL: " . $sql_check_backup];
                } else {
                    $stmt_check_backup->bind_param("ss", $matricula_colaborador, $dataRegistro_input);
                    $stmt_check_backup->execute();
                    $result_backup = $stmt_check_backup->get_result();
                    $backup_record = $result_backup->fetch_assoc();
                    $stmt_check_backup->close();

                    if (!$backup_record) {
                        // CASO 1: NENHUM registro em BackupPontoCompleto. É a primeira passagem do dia.
                        $horario_entrada_para_ponto_final = $horario_atual_passagem;
                        $horario_saida_para_ponto_final = null; // Saída é nula na primeira entrada
                        $tipo_registro_mensagem = "Primeira entrada do dia. Registrando em Ponto (trigger para backup).";
                    } else {
                        // CASO 2: JÁ EXISTE registro em BackupPontoCompleto. O dia já começou.
                        $horario_entrada_para_ponto_final = $backup_record['horario_entrada'];
                        $horario_saida_para_ponto_final = $horario_atual_passagem;
                        $tipo_registro_mensagem = "Passagem subsequente. Registrando em Ponto (trigger atualizará backup).";
                    }

                    // --- REMOVIDO: Apagar registros anteriores do mesmo colaborador/dia na Ponto. ---
                    // $delete_old_ponto_sql = "DELETE FROM Ponto WHERE idColaborador = ? AND dataRegistro = ?";
                    // $stmt_delete_ponto = $conn->prepare($delete_old_ponto_sql);
                    // if($stmt_delete_ponto) {
                    //     $stmt_delete_ponto->bind_param("ss", $matricula_colaborador, $dataRegistro_input);
                    //     $stmt_delete_ponto->execute();
                    //     $stmt_delete_ponto->close();
                    // } else {
                    //     error_log("PHP: Erro ao preparar delete para Ponto: " . $conn->error);
                    // }

                    // Sempre insere na tabela Ponto.
                    $insert_ponto_sql = "INSERT INTO Ponto (idColaborador, dataRegistro, horarioentrada, horariosaida) VALUES (?, ?, ?, ?)";
                    $stmt_insert_ponto = $conn->prepare($insert_ponto_sql);

                    if ($stmt_insert_ponto === false) {
                        $response = ["status" => "error", "message" => "Erro na preparação da inserção em Ponto: " . $conn->error . " SQL: " . $insert_ponto_sql];
                    } else {
                        error_log("DEBUG PHP BIND: Valores para Ponto -> Matrícula: '" . $matricula_colaborador . "', Data: '" . $dataRegistro_input . "', HE_Final: '" . $horario_entrada_para_ponto_final . "', HS_Final: '" . $horario_saida_para_ponto_final . "'");

                        $stmt_insert_ponto->bind_param("ssss", $matricula_colaborador, $dataRegistro_input, $horario_entrada_para_ponto_final, $horario_saida_para_ponto_final);
                        if ($stmt_insert_ponto->execute()) {
                            $update_colaborador_punch_time_sql = "UPDATE Colaborador SET last_punch_timestamp = ? WHERE matricula = ?";
                            $stmt_update_colaborador_punch_time = $conn->prepare($update_colaborador_punch_time_sql);
                            if ($stmt_update_colaborador_punch_time) {
                                $stmt_update_colaborador_punch_time->bind_param("ss", $current_punch_full_timestamp, $matricula_colaborador);
                                $stmt_update_colaborador_punch_time->execute();
                                $stmt_update_colaborador_punch_time->close();
                            } else {
                                error_log("PHP: Erro ao preparar atualização de last_punch_timestamp: " . $conn->error);
                            }

                            $response = [
                                "status" => "success",
                                "message" => $tipo_registro_mensagem,
                                "dataRegistro" => $dataRegistro_input,
                                "horarioEntradaRegistrado" => $horario_entrada_para_ponto_final,
                                "horarioSaidaRegistrado" => $horario_saida_para_ponto_final,
                                "matricula" => $matricula_colaborador,
                                "nome" => $nome_colaborador,
                                "lastPunchTimestampAtualizado" => $current_punch_full_timestamp
                            ];
                        } else {
                            $response = ["status" => "error", "message" => "Erro ao inserir registro em Ponto: " . $stmt_insert_ponto->error];
                        }
                        $stmt_insert_ponto->close();
                    }
                }
            } else {
                if (isset($stmt_colaborador)) $stmt_colaborador->close();
                $response = ["status" => "fail", "message" => "Nenhum colaborador encontrado com o encoding informado."];
            }
        }
    }
} else {
    http_response_code(400);
    $response = ["status" => "error", "message" => "Dados incompletos. Encoding, dataRegistro e horarioentrada (representando a passagem atual) são obrigatórios."];
}

$conn->close();
echo json_encode($response);

$end_time = microtime(true);
$execution_time = ($end_time - $start_time) * 1000;
error_log("PHP API Execution Time: " . $execution_time . " ms");
?>
