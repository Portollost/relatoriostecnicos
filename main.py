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

    "WARLEY PIMENTEL FERNANDES": "553171538434",
    "CARLOS HENRIQUE DA SILVA SOUZA": "553171538434",

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
        tecnico = (row["NomeParceiro"] or "SEM TÉCNICO").strip()
        relatorios_por_tecnico.setdefault(tecnico, []).append(row)

    data_anterior = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

    # Envia relatório para cada técnico
    for tecnico, atendimentos in relatorios_por_tecnico.items():
        primeiro_nome = tecnico.strip().split()[0].capitalize()

        mensagem = (
            f"🌞 *Bom dia, {primeiro_nome}!* 🌞\n\n"
            f"Aqui está um breve resumo dos seus atendimentos de ontem (*{data_anterior}*):\n\n"
            f"📋 *RELATÓRIO DIÁRIO*\n\n"
        )

        for i, a in enumerate(atendimentos, start=1):
            status = (
                "⚠️ *PENDENTE*" if not a["CodStatus"] or a["CodStatus"] in [1, 3]
                else "✅ *CONCLUÍDO*" if a["CodStatus"] == 4
                else "⚠️ *PENDENTE*"
            )

            relatorio = a["relatorio"] if a["relatorio"] else "⚠️ *PENDENTE*"
            data_ini = a["start_date"].strftime("%d/%m/%Y") if a["start_date"] else "⚠️ *PENDENTE*"
            hora_ini = a["start_time"] if a["start_time"] else "⚠️ *PENDENTE*"
            data_fim = a["end_date"].strftime("%d/%m/%Y") if a["end_date"] else "⚠️ *PENDENTE*"
            hora_fim = a["end_time"] if a["end_time"] else "⚠️ *PENDENTE*"

            mensagem += (
                f"*{i}) {a['NomeCli']}*\n"
                f"• 🏷️ *Status:* {status}\n"
                f"• 📝 *Relatório:* {relatorio}\n"
                f"• ⏰ *Início:* {data_ini} às {hora_ini}\n"
                f"• ✅ *Finalização:* {data_fim} às {hora_fim}\n"
                f"──────────────────────\n\n"
            )

        mensagem += "💪 *Vamos deixar tudo 100% atualizado hoje?*\n"
        mensagem += "Manter seus relatórios em dia ajuda toda a equipe! 🚀\n"
        mensagem += "https://eugon.net.br/gestaomsw\n"

        enviar_whatsapp(tecnico, mensagem)



# ==========================
# ENVIO VIA WHATSAPP
# ==========================

def enviar_whatsapp(tecnico, mensagem):
    tecnico_key = tecnico.strip().upper()
    
    # Normaliza o dicionário de parceiros
    parceiros_normalizado = {k.strip().upper(): v for k, v in parceiros.items()}
    numero = parceiros_normalizado.get(tecnico_key)
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



print("⏰ Script agendado: enviará relatórios todos os dias às 08:00.")
gerar_e_enviar_relatorios()

while True:
    schedule.run_pending()
    time.sleep(60)

