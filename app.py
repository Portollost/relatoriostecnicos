import mysql.connector
from datetime import datetime, timedelta
import schedule
import time
import requests
from app.whatsapp import get_headers, get_number_id  # ✅ usa as mesmas funções do seu sistema

# ==========================
# CONFIGURAÇÕES
# ==========================

# Conexão com o banco MySQL
db_config = {
    'host': '187.73.33.163',
    'user': 'eugon2',
    'password': 'Master45@net',
    'database': 'eugon2'
}

# Mapeia técnicos para números de WhatsApp
parceiros = {
    "Gabriel Comonian Porto": "5531971538434",
}


# ==========================
# FUNÇÃO PRINCIPAL
# ==========================

def gerar_e_enviar_relatorios():
    print(f"📅 Gerando relatórios: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        a.start_date, a.start_time, a.end_date, a.end_time,
        b.NomeCli, a.relatorio, a.CodStatus, c.NomeParceiro
    FROM calendar AS a
    LEFT JOIN C_Clientes AS b ON a.CodCli = b.CodCli
    LEFT JOIN C_ParceirosInternos AS c ON a.CodDent = c.CodParceiroInt
    WHERE DATE(a.start_date) = CURDATE() - INTERVAL 1 DAY
    ORDER BY c.NomeParceiro, a.id
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print("⚠️ Nenhum atendimento encontrado para o dia anterior.")
        return

    # Agrupa por técnico
    relatorios_por_tecnico = {}
    for row in rows:
        tecnico = row["NomeParceiro"] or "SEM TÉCNICO"
        relatorios_por_tecnico.setdefault(tecnico, []).append(row)

    data_anterior = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

    # Envia relatório para cada técnico
    for tecnico, atendimentos in relatorios_por_tecnico.items():
        mensagem = f"Bom dia {tecnico}!\n"
        mensagem += f"Segue abaixo um breve relatório do seu dia {data_anterior}:\n\nATENDIMENTOS:\n\n"

        for i, a in enumerate(atendimentos, start=1):
            status = (
                "(PENDENTE)" if not a["CodStatus"]
                else "CONCLUÍDO" if a["CodStatus"] == 4
                else "EM ANDAMENTO" if a["CodStatus"] == 3
                else "A CONFIRMAR"
            )

            relatorio = a["relatorio"] if a["relatorio"] else "(PENDENTE)"
            data_ini = a["start_date"].strftime("%d/%m/%Y") if a["start_date"] else "(PENDENTE)"
            hora_ini = a["start_time"] if a["start_time"] else "(PENDENTE)"
            data_fim = a["end_date"].strftime("%d/%m/%Y") if a["end_date"] else "(PENDENTE)"
            hora_fim = a["end_time"] if a["end_time"] else "(PENDENTE)"

            mensagem += (
                f"{i}) {a['NomeCli']}\n"
                f"STATUS: {status}\n"
                f"RELATÓRIO: {relatorio}\n"
                f"DATA INÍCIO: {data_ini} {hora_ini}\n"
                f"DATA FINALIZAÇÃO: {data_fim} {hora_fim}\n"
                f"{'-'*90}\n\n"
            )

        enviar_whatsapp(tecnico, mensagem)


# ==========================
# ENVIO VIA WHATSAPP
# ==========================

def enviar_whatsapp(tecnico, mensagem):
    numero = parceiros.get(tecnico)
    if not numero:
        print(f"⚠️ Sem número de WhatsApp configurado para {tecnico}")
        return

    headers = get_headers()
    number_id = get_number_id()
    url = f"https://graph.facebook.com/v17.0/{number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }

    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            print(f"✅ Relatório enviado para {tecnico} ({numero})")
        else:
            print(f"❌ Erro ao enviar para {tecnico}: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro ao conectar com a API WhatsApp: {e}")


# ==========================
# AGENDAMENTO DIÁRIO
# ==========================

schedule.every().day.at("08:00").do(gerar_e_enviar_relatorios)

print("⏰ Script agendado: enviará relatórios todos os dias às 08:00.")
while True:
    schedule.run_pending()
    time.sleep(60)
