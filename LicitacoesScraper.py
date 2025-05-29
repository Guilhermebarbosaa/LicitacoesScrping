!pip install openpyxl
import requests
from bs4 import BeautifulSoup
import json
import urllib3
import pandas as pd
from google.colab import files
urllib3.disable_warnings()
palavras_chave = [
    'CLP', 'PLC', 'PAC', 'Controlador Lógico Programável', '6ES7', 'remotas I/O', 'I/O', 'cabeça remota', 'UTR', 'RTU',
    'unidade terminal remota', 'IHM', 'HMI', 'interface homem máquina', 'SCADA', 'supervisório', 'sistema de supervisão',
    'estação de supervisão', 'CCO', 'COR', 'gestão de energia', 'gerenciamento de energia', 'PIMS', 'telemetria',
    'telemonitoramento', 'telecontrole', 'automação', 'automatismo', 'elevatória', 'estação elevatória', 'EE', 'EEE',
    'EEEB', 'EEET', 'EEA', 'EEAB', 'EEAT', 'EBAP', 'profinet', 'profibus', 'modbus', 'ethernet/ip', 'RS485',
    'industrial PC', 'switch industrial', 'edge computing', 'edge', 'fonte de alimentação'
]
def pesquisar_palavras_chave(texto):
    texto = texto.upper()
    return any(palavra.upper() in texto for palavra in palavras_chave)
def scraping_sanepar():
    print("🔍 Coletando dados da Sanepar...")
    url = 'https://licitacoes.sanepar.com.br/SLI2A000.aspx'
    response = requests.get(url)
    resultados = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for classe in ['tabPar', 'tabImpar']:
            elementos = soup.find_all(class_=classe)
            for item in elementos:
                texto_item = item.text.upper()
                if pesquisar_palavras_chave(texto_item):
                    resultados.append({
                        "origem": "Sanepar",
                        "tipo": "obras/serviços",
                        "descricao": item.text.strip()
                    })
    else:
        print(f"Erro ao acessar o site da Sanepar: {response.status_code}")
    return resultados
def verificar_palavra_em_json(data):
    for key, value in data.items():
        for palavra in palavras_chave:
            if palavra.upper() in str(key).upper() or palavra.upper() in str(value).upper():
                return True
    return False
def scraping_copasa():
    print("🔍 Coletando dados da Copasa...")
    url_principal = "https://srm.copasa.com.br/sap/bc/pagina/zsrm_filtro_pro?sap-client=300&sap-language=PT&ANO=2024&MODALIDADE=PREGAO_ELETRONICO&ZZSTATUS=PU"
    resultados = []
    try:
        response = requests.get(url_principal, verify=False)
        response.raise_for_status()
        data = response.json()
        leiloes = data.get('data', {}).get('leilao', [])
        for leilao in leiloes:
            guid = leilao.get('guid')
            if not guid:
                continue
            url_detalhe = f"https://srm.copasa.com.br/sap/bc/pagina/zsrmf087?sap-client=300&sap-language=PT&GUID={guid}"
            r = requests.get(url_detalhe, verify=False)
            if r.status_code != 200:
                continue
            json_data = r.json()
            if verificar_palavra_em_json(json_data):
                resultados.append({
                    "origem": "Copasa",
                    "tipo": "obras/serviços",
                    "descricao": f"{leilao.get('processNumBr')} - {leilao.get('objectDesc')}",
                    "data_final": f"{leilao.get('quotDead')} {leilao.get('quotDeadTime')}"
                })
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição: {e}")
    return resultados
def exportar_para_excel(sanepar_resultados, copasa_resultados):
    if not sanepar_resultados and not copasa_resultados:
        print("⚠️ Nenhum dado para exportar.")
        return None
    dados_completos = sanepar_resultados + copasa_resultados
    df = pd.DataFrame(dados_completos)
    nome_arquivo = "licitacoes_filtradas.xlsx"
    df.to_excel(nome_arquivo, index=False)
    print(f"✅ Planilha gerada: {nome_arquivo}")
    return nome_arquivo
sanepar_resultados = scraping_sanepar()
copasa_resultados = scraping_copasa()
arquivo_excel = exportar_para_excel(sanepar_resultados, copasa_resultados)
if arquivo_excel:
    files.download(arquivo_excel)
