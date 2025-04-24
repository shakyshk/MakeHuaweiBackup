import paramiko
import logging
import sys
from datetime import datetime
import os
import uuid
import glob
import time
import requests
import json

#########################################################
# Inicio do script
#########################################################

message_data = {
    "token_do_bot": "",
    "id_do_chat": "",
    "enviar_mensagem_telegram": None
}

#########################################################
# Declarando função para imprimir mensagem na tela e salvar nos logs.
# (Para evitar redundância)
# A função recebe uma mensagem e um level de log (opcional).
# Padrão: "info"
# Valores possíveis: "info", "debug", "warning", "error", "critical".
#########################################################


def print_and_log(message, level="info"):
    message = '\n'.join([m.lstrip() for m in message.split('\n')])
    match level:
        case "info":
            print(message)
            logging.info(message.strip())
        case "debug":
            print(message)
            logging.debug(message.strip())
        case "warning":
            print(message)
            logging.warning(message.strip())
        case "error":
            print(message)
            logging.error(message.strip())
        case "critical":
            print(message)
            logging.critical(message.strip())
        case _:
            print(f"\nO level de log {level} não existe!")
            logging.critical(f"O level de log {level} não existe!")
            end_script(1, message_data)

#########################################################
# Declarando uma função simples para finalizar
# o script, mostrar uma mensagem e salvar no log
#########################################################


def end_script(finish_code: 0, message_data: None):
    match finish_code:
        case 0:
            if message_data["enviar_mensagem_telegram"]:
                send_telegram_messages(message_data)
            print_and_log(f"""\n*********************************************************\n
                        Programa finalizado com sucesso!
                        \n/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/\n""")
            sys.exit(0)
        case 1:
            if message_data["enviar_mensagem_telegram"]:
                send_telegram_messages(message_data)
            print_and_log(f"""\n*********************************************************\n
                        Programa finalizado com erro!
                        \n/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/\n""", "critical")
            sys.exit(1)


#########################################################
# Funções para envio de mensagens via telegram
#########################################################

def send_telegram_messages(message_data):
    print_and_log(f"""\n*********************************************************\n
              Enviando mensagens via Telegram...""")
    telegram_info = {
        "token_do_bot": message_data["token_do_bot"],
        "id_do_chat": message_data["id_do_chat"]
    }
    for dispositivo in message_data["dispositivos"]:
        send_telegram_message(telegram_info, dispositivo, message_data["dispositivos"][dispositivo]
                              ["backup_with_success"], message_data["dispositivos"][dispositivo])
        time.sleep(1)


def escape_markdown_v2(text_to_escape):
    text_to_escape = str(text_to_escape)
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text_to_escape)


def send_telegram_message(telegram_info: None, device_name: None, is_success: bool, message_data: None):
    json_formatted_str = json.dumps(
        message_data, indent=2, ensure_ascii=False)

    message_data["nome_do_dispositivo"] = escape_markdown_v2(device_name)
    message_data["data_e_hora_atual"] = escape_markdown_v2(
        message_data["data_e_hora_atual"])
    message_data["duração"] = escape_markdown_v2(message_data["duração"])
    message_data["bkp_name"] = escape_markdown_v2(
        message_data["bkp_name"])
    mensagem = ""
    if is_success:
        mensagem = f"""─────────────────────────
✅ BACKUP: *{message_data["nome_do_dispositivo"]}*
_Backup do HUAWEI realizado com sucesso\\!_
─────────────────────────
🏢 *Huawei:* {message_data["nome_do_dispositivo"]}
📅 *Data:* {message_data["data_e_hora_atual"]}
⏳ *Duração:* {message_data["duração"]} minutos
💾 *Backup:* {message_data["bkp_name"]}
─────────────────────────"""
    else:
        mensagem = f"""─────────────────────────
❌ BACKUP: *{message_data["nome_do_dispositivo"]}*
_Erro ao realizar backup do HUAWEI\\!_
─────────────────────────
🏢 *Huawei:* {message_data["nome_do_dispositivo"]}
📅 *Data:* {message_data["data_e_hora_atual"]}
⏳ *Duração:* {message_data["duração"]} minutos
─────────────────────────"""

    print_and_log(f"""
---------------------------------------------------------
Enviando mensagem: {device_name}
Backup com sucesso? {is_success}
Dados do backup: {json_formatted_str}
Mensagem:
{mensagem}
""")

    url = f"https://api.telegram.org/bot{telegram_info["token_do_bot"]}/sendMessage"
    dados = {
        'chat_id': telegram_info["id_do_chat"],
        'text': mensagem,
        'parse_mode': 'MarkdownV2'
    }
    try:
        resposta = requests.post(url, data=dados)
        resposta.raise_for_status()
    except:
        print_and_log(
            f"Código: {resposta.status_code}\nErro no envio da mensagem!\n{resposta.description}", "critical")
    if resposta.status_code == 200:
        print_and_log(
            f"Código: {resposta.status_code}\nSucesso no envio da mensagem!")
    else:
        print_and_log(
            f"Código: {resposta.status_code}\nErro no envio da mensagem!\n{resposta.description}", "critical")

#########################################################
# Configurando os logs do script
#########################################################


print(f"""\n/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/\n\nIniciando arquivo de log...""")

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
unique_time_id = f"{datetime.now().strftime('%d-%m-%Y__%H-%M-%S')}__{uuid.uuid4().hex}"
log_name = f"log__{unique_time_id}.log"
log_filename = os.path.join(
    log_dir,
    log_name)

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s:\n%(message)s\n"
)

print_and_log(f"""Arquivo de log iniciado com sucesso!""")

#########################################################
# Lendo arquivo settings.txt
#########################################################

print_and_log(f"""\n*********************************************************\n
              Iniciando leitura das configurações...""")

dispositivos_to_backup = {}
max_logs = None
main_delimiter_count = 0
config_section = 0

try:
    with open("settings.txt", "r", encoding="utf-8") as file:
        lines = file.readlines()
        for index, line in enumerate(lines):
            if line[0:1] == "#":
                continue
            if line[0:3] == "---":
                main_delimiter_count += 1
                continue
            if main_delimiter_count == 1:
                config_section = 1
            elif main_delimiter_count == 3:
                config_section = 2
            else:
                config_section = 0
            if config_section == 1:
                if "max_logs" in line:
                    try:
                        max_logs = int(line.split("=")[1].strip())
                    except Exception as error:
                        print_and_log(
                            "\nErro: Erro ao ler o parâmetro 'max_logs'", "critical")
                        end_script(1, message_data)
                    else:
                        print_and_log(
                            f"Máximo de logs a serem mantidos no sistema: {max_logs}")
                if "send_telegram_message" in line:
                    try:
                        string_send_telegram_message = line.split("=")[
                            1].strip()
                        if "true" in string_send_telegram_message:
                            message_data["enviar_mensagem_telegram"] = True
                        elif "false" in string_send_telegram_message:
                            message_data["enviar_mensagem_telegram"] = False
                    except Exception as error:
                        print_and_log(
                            "\nErro: Erro ao ler o parâmetro 'send_telegram_message'", "critical")
                        end_script(1, message_data)
                    else:
                        print_and_log(
                            f"Deve enviar mensagem via telegram: {message_data["enviar_mensagem_telegram"]}")
                if "token_do_bot" in line:
                    try:
                        message_data["token_do_bot"] = line.split("=")[
                            1].strip()
                    except Exception as error:
                        print_and_log(
                            "\nErro: Erro ao ler o parâmetro 'token_do_bot'", "critical")
                    else:
                        print_and_log(
                            f"Token do bot telegram: {message_data["token_do_bot"]}")
                if "id_do_chat" in line:
                    try:
                        message_data["id_do_chat"] = line.split("=")[
                            1].strip()
                    except Exception as error:
                        print_and_log(
                            "\nErro: Erro ao ler o parâmetro 'id_do_chat'", "critical")
                    else:
                        print_and_log(
                            f"ID do chat que o bot enviará a mensagem: {message_data["id_do_chat"]}")
            elif config_section == 2:
                if line[0:1] == "-":
                    continue
                elif line[0:1] == ">":
                    try:
                        device_name = line[1:].strip()
                        device_data = lines[index+1].strip().split("|")
                        device_data = {
                            "ip": str(device_data[0].strip()),
                            "porta": int(device_data[1].strip()),
                            "usuario": str(device_data[2].strip()),
                            "senha": str(device_data[3].strip()),
                            "backup_with_success": False
                        }
                        dispositivos_to_backup[device_name] = device_data
                    except Exception as error:
                        print_and_log(
                            f"\nErro: Erro na leitura dos dados dos dispositivos no arquivo de configuração\n{error}", "critical")
                        end_script(1, message_data)
                    else:
                        print_and_log(
                            f"Sucesso ao ler os dados do dispositivo {device_name} no arquivo de configuração.")
except IOError as error:
    print_and_log(f"""\nErro ao tentar abrir o arquivo settings.txt:\n
        {error}\n
        #########################################################\n""", "critical")
    end_script(1, message_data)
except Exception as error:
    print_and_log(f"""\nErro ao tentar abrir o arquivo settings.txt:\n
        {error}\n
        #########################################################\n""", "critical")
    end_script(1, message_data)

message_data["dispositivos"] = dispositivos_to_backup

print_and_log(f"""Configurações lidas com sucesso!""")

#########################################################
# Limpando logs antigos caso excedido o número máximo de logs
#########################################################

print_and_log(f"""\n*********************************************************\n
              Iniciando limpeza dos logs antigos...""")

logs = sorted(glob.glob(os.path.join(log_dir, "log_*.log")),
              key=os.path.getctime)

if len(logs) > max_logs:
    print_and_log(f"""Quantidade de logs excedida!""")
    logs_a_excluir = logs[:len(logs) - max_logs]
    for log in logs_a_excluir:
        os.remove(log)
        print_and_log(f"""Log removido: {log}""")

print_and_log(f"""Limpeza dos logs antigos finalizada com sucesso!""")

#########################################################
# Conectando SSH
#########################################################

print_and_log(f"""\n*********************************************************\n
              Acessando dispositivos e fazendo backup...""")


def aguardar_o_comando_finalizar(shell, prompt, timeout):
    output = ""
    start_time = time.time()

    while True:
        if shell.recv_ready():
            output += shell.recv(9999).decode("utf-8")
            if output.strip().endswith(prompt) and "\n" not in repr(output)[-5:] and "\r" not in repr(output)[-5:]:
                break
        if time.time() - start_time > timeout:
            print_and_log("Timeout esperando prompt.")
            break
        time.sleep(0.2)

    return output


for dispositivo in dispositivos_to_backup:
    print_and_log(f"""\n---------------------------------------------------------\n
Acessando: {dispositivo}...""")
    message_data["dispositivos"][dispositivo]["hora_inicio"] = time.time()
    message_data["dispositivos"][dispositivo]["bkp_name"] = ""
    try:
        endereço = dispositivos_to_backup[dispositivo]["ip"]
        porta = dispositivos_to_backup[dispositivo]["porta"]
        usuario = dispositivos_to_backup[dispositivo]["usuario"]
        senha = dispositivos_to_backup[dispositivo]["senha"]
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        print_and_log(f"Tentando conexão com o dispositivo: {dispositivo}")
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=endereço, port=porta,
                       username=usuario, password=senha)

        print_and_log("Conectado!")

        shell = client.invoke_shell()
        prompt_comando_finalizado = f"<{dispositivo}>"

        comando_1 = "screen-length 0 temporary"
        print_and_log(f"Rodando: {comando_1}")
        shell.send(f"{comando_1}\n")
        output = aguardar_o_comando_finalizar(
            shell, prompt_comando_finalizado, 60)
        print_and_log("Finalizado")

        comando_2 = "display current-configuration"
        print_and_log(f"Rodando: {comando_2}")
        shell.send(f"{comando_2}\n")
        output = aguardar_o_comando_finalizar(
            shell, prompt_comando_finalizado, 120)
        print_and_log("Finalizado")

    except paramiko.AuthenticationException:
        print_and_log(
            f"\nAutenticação para {dispositivo} falhou, verifique o usuário e senha.", "critical")
        end_script(1, message_data)
    except paramiko.SSHException as ssh_exception:
        print_and_log(
            f"\nConexão SSH para {dispositivo} falhou:\n{ssh_exception}", "critical")
        end_script(1, message_data)
    except Exception as error:
        print_and_log(
            f"\nErro na conexão com o host: {dispositivo}\n{error}", "critical")
        end_script(1, message_data)
    else:
        date_now = datetime.now().strftime('%d-%m-%Y')
        time_now = datetime.now().strftime('%H-%M-%S')
        nome_do_backup = f"../BACKUP__HUAWEI-{dispositivo}__DATA-{date_now}__HORA-{time_now}.txt"
        print_and_log(f"Salvando backup: {nome_do_backup.split("/")[-1]}")
        message_data["dispositivos"][dispositivo]["bkp_name"] = nome_do_backup.split(
            "/")[-1]
        output = output.split("\n")
        try:
            with open(nome_do_backup, "w") as file:
                for index, line in enumerate(output):
                    if index < 10:
                        if comando_1 in line:
                            continue
                        elif comando_2 in line:
                            continue
                        elif "Info: " in line:
                            continue
                        else:
                            file.write(line)
                    elif index >= len(output)-11:
                        if line == prompt_comando_finalizado:
                            continue
                        else:
                            file.write(line)
                    else:
                        file.write(line)
        except IOError as error:
            print_and_log(f"""\nErro ao tentar salvar o backup {nome_do_backup}:\n
                {error}\n
                #########################################################\n""", "critical")
            end_script(1, message_data)
        except Exception as error:
            print_and_log(f"""\nErro ao tentar salvar o backup {nome_do_backup}:\n
                {error}\n
                #########################################################\n""", "critical")
            end_script(1, message_data)
        else:
            print_and_log(f"""Backup salvo com sucesso!""")
            message_data["dispositivos"][dispositivo]["backup_with_success"] = True
            dispositivos_to_backup[dispositivo]["backup_with_success"] = True
    finally:
        client.close()

    message_data["dispositivos"][dispositivo]["hora_final"] = time.time()
    message_data["dispositivos"][dispositivo]["duração"] = round(
        (message_data["dispositivos"][dispositivo]["hora_final"] - message_data["dispositivos"][dispositivo]["hora_inicio"])/60, 2)
    message_data["dispositivos"][dispositivo]["data_e_hora_atual"] = datetime.now(
    ).strftime("%d/%m/%Y - %H:%M:%S")

# --------------------------------------------------------
# Finalizando o programa
# --------------------------------------------------------

end_script(0, message_data)
