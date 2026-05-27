"""
Gerador de PDF - Fase 6
-----------------------
Módulo responsável por exportar a lista de embarque de um passeio 
específico para um documento PDF bem formatado usando reportlab.
"""

import sqlite3
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

def calcular_idade(data_nascimento: str) -> str:
    """Calcula a idade subtraindo o ano de nascimento do ano atual."""
    if not data_nascimento or len(data_nascimento) < 10:
        return "N/A"
    try:
        ano_nasc = int(data_nascimento[-4:])
        ano_atual = datetime.date.today().year
        idade = ano_atual - ano_nasc
        return str(idade)
    except ValueError:
        return "N/A"

def conectar():
    return sqlite3.connect(DB_PATH)

def gerar_relatorio_embarque(id_passeio, tipo="completo"):
    """Gera um PDF zebrado com os passageiros alocados no passeio."""
    
    # 1. Criar pasta se não existir
    if not os.path.exists(RELATORIOS_DIR):
        os.makedirs(RELATORIOS_DIR)
        
    conn = conectar()
    cursor = conn.cursor()
    
    # 2. Resgatar dados do passeio
    cursor.execute("SELECT destino, data_passeio, hora_saida, hora_retorno FROM passeios WHERE id=?", (id_passeio,))
    passeio = cursor.fetchone()
    
    if not passeio:
        conn.close()
        raise Exception("Passeio não encontrado no banco de dados.")
        
    destino, data_pass, hora_saida, hora_retorno = passeio
    destino_clean = "".join([c for c in destino if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    data_clean = data_pass.replace("/", "-")
    
    # Nome do arquivo final
    nome_arquivo = f"Lista_{tipo.capitalize()}_{destino_clean.replace(' ', '_')}_{data_clean}.pdf"
    pdf_path = os.path.join(RELATORIOS_DIR, nome_arquivo)
    
    # 3. Resgatar lista de passageiros alocados
    query = """
        SELECT a.numero_poltrona, p.nome_completo, p.data_nascimento, p.whatsapp, p.rg, p.cpf, a.local_embarque, 
               pc.nome_completo as crianca_nome, pc.data_nascimento as crianca_nasc, pc.rg as crianca_rg, pc.cpf as crianca_cpf
        FROM alocacao_poltronas a
        JOIN passageiros p ON a.passageiro_id = p.id
        LEFT JOIN passageiros pc ON a.crianca_colo = CAST(pc.id AS TEXT)
        WHERE a.passeio_id = ?
        ORDER BY a.numero_poltrona ASC
    """
    cursor.execute(query, (id_passeio,))
    alocacoes = cursor.fetchall()
    conn.close()
    
    # 4. Construir o documento
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=10)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], alignment=0, spaceAfter=10, spaceBefore=20, textColor=colors.HexColor('#3D7BA3'))
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=11, spaceAfter=20)
    
    # Imagem/Logo (se existir)
    if os.path.exists(LOGO_PATH):
        img = Image(LOGO_PATH, width=150, height=80)
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 15))
        
    # Título Principal
    tipo_str = "Completa" if tipo == "completo" else "Resumida"
    story.append(Paragraph(f"<b>Lista de Passageiros ({tipo_str}) - Pé Na Estrada Tour</b>", title_style))
    
    # Info do Passeio
    info_text = f"<b>Destino:</b> {destino} &nbsp;&nbsp;&nbsp; <b>Data:</b> {data_pass}<br/>"
    info_text += f"<b>Saída:</b> {hora_saida or '--:--'} &nbsp;&nbsp;&nbsp; <b>Retorno:</b> {hora_retorno or '--:--'}"
    story.append(Paragraph(info_text, info_style))
    
    # 5. Tabelas
    if tipo == "completo":
        dados_tabela = [["Pol", "Nome Completo", "Idade", "Contato", "Doc (RG/CPF)", "Embarque"]]
        col_widths = [30, 160, 40, 90, 115, 120] 
        dados_tabela_criancas = [["Pol Resp.", "Nome da Criança", "Idade", "Doc (RG/CPF)", "Responsável"]]
        col_widths_criancas = [50, 160, 40, 115, 190]
    else:
        dados_tabela = [["Pol", "Nome Completo", "Contato", "Embarque"]]
        col_widths = [30, 230, 110, 185] 
        dados_tabela_criancas = [["Pol Resp.", "Nome da Criança", "Responsável"]]
        col_widths_criancas = [60, 245, 250]
        
    for row in alocacoes:
        pol = f"{row[0]:02d}"
        nome = row[1]
        idade = calcular_idade(row[2])
        contato = row[3] or "—"
        rg = row[4]
        cpf = row[5]
        local = row[6] or "Padrão"
        
        c_nome = row[7]
        c_idade = calcular_idade(row[8]) if c_nome else "—"
        c_rg = row[9]
        c_cpf = row[10]
        
        doc_str = ""
        if rg and cpf: doc_str = f"RG: {rg}\nCPF: {cpf}"
        elif rg: doc_str = f"RG: {rg}"
        elif cpf: doc_str = f"CPF: {cpf}"
        else: doc_str = "—"
        
        if tipo == "completo":
            dados_tabela.append([pol, nome, idade, contato, doc_str, local])
        else:
            dados_tabela.append([pol, nome, contato, local])
            
        if c_nome:
            c_doc_str = ""
            if c_rg and c_cpf: c_doc_str = f"RG: {c_rg}\nCPF: {c_cpf}"
            elif c_rg: c_doc_str = f"RG: {c_rg}"
            elif c_cpf: c_doc_str = f"CPF: {c_cpf}"
            else: c_doc_str = "—"
            
            if tipo == "completo":
                dados_tabela_criancas.append([pol, c_nome, c_idade, c_doc_str, nome])
            else:
                dados_tabela_criancas.append([pol, c_nome, nome])

    if len(dados_tabela) == 1:
        if tipo == "completo":
            dados_tabela.append(["—", "Nenhum passageiro", "—", "—", "—", "—"])
        else:
            dados_tabela.append(["—", "Nenhum passageiro", "—", "—"])
            
    # Estilo genérico das tabelas
    def criar_estilo_tabela(dados):
        estilo = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3D7BA3')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E4F7FE')),
        ])
        for i in range(1, len(dados)):
            bg_color = colors.HexColor('#F8F9FA') if i % 2 == 0 else colors.white
            estilo.add('BACKGROUND', (0, i), (-1, i), bg_color)
        return estilo

    # Tabela 1: Adultos
    tabela1 = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
    tabela1.setStyle(criar_estilo_tabela(dados_tabela))
    story.append(tabela1)
    
    # Tabela 2: Crianças (se houver)
    if len(dados_tabela_criancas) > 1:
        story.append(Paragraph("👶 Crianças de Colo", subtitle_style))
        tabela2 = Table(dados_tabela_criancas, colWidths=col_widths_criancas, repeatRows=1)
        tabela2.setStyle(criar_estilo_tabela(dados_tabela_criancas))
        story.append(tabela2)
    
    # 6. Gerar o arquivo
    try:
        doc.build(story)
    except PermissionError:
        messagebox.showwarning("Aviso", "O arquivo PDF já está aberto no seu computador. Por favor, feche-o antes de gerar uma versão atualizada.")
        return None
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")
        return None
    
    # 7. Abrir no visualizador padrão (Windows)
    try:
        os.startfile(pdf_path)
    except Exception as e:
        print(f"Não foi possível abrir o PDF automaticamente: {e}")
        
    return pdf_path

# Bloco para teste isolado
if __name__ == "__main__":
    try:
        gerar_relatorio_embarque(1)
        print("PDF gerado com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
