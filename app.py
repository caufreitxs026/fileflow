import streamlit as st
import fitz  # PyMuPDF (ainda pode ser útil para pdf2docx)
import pandas as pd
import re
import io
from PIL import Image
from pdf2docx import Converter as PDFToWordConverter
from fpdf import FPDF

# --- Funções de Conversão ---

def convert_pdf_to_word(file_bytes):
    """Converte bytes de PDF para bytes de DOCX."""
    pdf_stream = io.BytesIO(file_bytes)
    docx_stream = io.BytesIO()
    
    # Converte o PDF (stream) para DOCX (stream)
    cv = PDFToWordConverter(pdf_stream)
    cv.convert(docx_stream)
    cv.close()
    
    docx_stream.seek(0)
    return docx_stream.getvalue()

def convert_image_to_format(file_bytes, output_format):
    """Converte bytes de imagem (PNG, JPG) para um novo formato."""
    img = Image.open(io.BytesIO(file_bytes))
    
    # Garante que imagens RGBA (com transparência) sejam convertidas para RGB
    # antes de salvar como JPG, que não suporta transparência.
    if output_format == 'JPEG' and img.mode == 'RGBA':
        img = img.convert('RGB')
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format=output_format)
    return output_buffer.getvalue()

def convert_excel_to_pdf(file_bytes):
    """Converte bytes de Excel (primeira aba) para bytes de PDF."""
    df = pd.read_excel(io.BytesIO(file_bytes))
    
    pdf = FPDF()
    pdf.add_page(orientation='L') # Paisagem para caber mais colunas
    pdf.set_font("Arial", size=8)
    
    # Adiciona Cabeçalho
    col_width = pdf.w / (len(df.columns) + 1) # Largura da coluna
    
    pdf.set_fill_color(200, 220, 255) # Cor de fundo do cabeçalho
    for col_name in df.columns:
        pdf.cell(col_width, 10, str(col_name), border=1, fill=True)
    pdf.ln()
    
    # Adiciona Linhas
    for index, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.ln()
        
    output_buffer = io.BytesIO()
    pdf.output(output_buffer)
    return output_buffer.getvalue()

def convert_image_to_pdf(file_bytes):
    """Converte bytes de imagem (PNG, JPG) para bytes de PDF."""
    img = Image.open(io.BytesIO(file_bytes))
    
    # Converte para RGB se for RGBA
    if img.mode == 'RGBA':
        img = img.convert('RGB')
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="PDF", resolution=100.0)
    return output_buffer.getvalue()

# --- FIM: Funções de Conversão ---


# --- INTERFACE GRÁFICA (UI) ---

st.set_page_config(
    page_title="FileFlow Conversor",
    layout="centered"
)

# --- CSS Customizado (Logo + Sidebar Footer + Main Container) ---
st.markdown("""
<style>
    /* --- Início do Bloco da Logo --- */
	.logo-text {
		font-family: 'Courier New', monospace;
		font-size: 28px; /* Ajuste o tamanho se necessário para as páginas internas */
		font-weight: bold;
		padding-top: 20px;
	}
	/* Estilos para o tema claro (light) */
	.logo-file {
		color: #FFFFFF; /* Fonte branca */
		text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7); /* Sombra preta */
	}
	.logo-flow {
		color: #E30613; /* Fonte vermelha */
		text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7); /* Sombra preta */
	}

	/* Estilos para o tema escuro (dark) */
	@media (prefers-color-scheme: dark) {
		.logo-file {
			color: #FFFFFF;
			text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7); /* Mantém a sombra preta para contraste */
		}
		.logo-flow {
			color: #FF4B4B; /* Um vermelho mais vibrante para o tema escuro */
			text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7); /* Sombra preta */
		}
	}
	/* --- Fim do Bloco da Logo --- */

    /* --- CSS Antigo para Centralizar --- */
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-top: 2rem;
    }

    /* --- Estilos para o footer na barra lateral --- */
    /* ATENÇÃO: Modifiquei 'img' para 'svg' para funcionar com seu código SVG */
    .sidebar-footer { text-align: center; padding-top: 20px; padding-bottom: 20px; }
    .sidebar-footer a { margin-right: 15px; text-decoration: none; }
    .sidebar-footer svg { width: 25px; height: 25px; fill: #888; transition: fill 0.3s; }
    .sidebar-footer svg:hover { fill: #FFF; }
    
    @media (prefers-color-scheme: dark) {
        .sidebar-footer svg { fill: #888; }
        .sidebar-footer svg:hover { fill: #FFF; }
    }
</style>
""", unsafe_allow_html=True)

# --- Header (Logo no canto superior esquerdo) ---
st.markdown(
    """
    <div class="logo-text">
        <span class="logo-text"><span class="logo-file">FILE</span><span class="logo-flow">FLOW</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Corpo do Aplicativo ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Container principal para dar o efeito de "card"
with st.container(border=True):
    st.title("Conversor Universal de Arquivos")
    st.markdown("Selecione a conversão desejada e faça o upload do seu arquivo.")

    # Dicionário de opções de conversão
    # Formato: "Nome da Opção": (tipo_entrada, ext_saida, label_upload)
    conversion_options = {
        "PDF (Geral) para Word": (["pdf"], "docx", "PDF"),
        "Excel para PDF": (["xlsx", "xls"], "pdf", "Excel"),
        "PNG para JPG": (["png"], "jpg", "PNG"),
        "JPG para PNG": (["jpg", "jpeg"], "png", "JPG"),
        "Imagem (PNG/JPG) para PDF": (["png", "jpg", "jpeg"], "pdf", "Imagem")
    }

    option = st.selectbox(
        "Escolha o tipo de conversão:",
        list(conversion_options.keys())
    )

    # Pega os detalhes da opção selecionada
    in_ext, out_ext, label = conversion_options[option]

    # Uploader de arquivo
    uploaded_file = st.file_uploader(
        f"Selecione o arquivo {label}",
        type=in_ext,
        label_visibility="collapsed"
    )

    # Lógica de processamento e download
    if uploaded_file:
        with st.spinner("Processando..."):
            try:
                file_bytes = uploaded_file.getvalue()
                output_bytes = None
                
                # Define o nome do arquivo de saída
                base_name = uploaded_file.name.split('.')[0]
                file_name = f"{base_name}.{out_ext}"

                # Roteia para a função de conversão correta
                if option == "PDF (Geral) para Word":
                    output_bytes = convert_pdf_to_word(file_bytes)
                elif option == "PNG para JPG":
                    output_bytes = convert_image_to_format(file_bytes, "JPEG")
                elif option == "JPG para PNG":
                    output_bytes = convert_image_to_format(file_bytes, "PNG")
                elif option == "Excel para PDF":
                    output_bytes = convert_excel_to_pdf(file_bytes)
                elif option == "Imagem (PNG/JPG) para PDF":
                     output_bytes = convert_image_to_pdf(file_bytes)

                st.success("Conversão concluída com sucesso!")
                st.download_button(
                    label=f"Baixar {file_name}",
                    data=output_bytes,
                    file_name=file_name,
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

st.markdown('</div>', unsafe_allow_html=True)


# --- Rodapé (Movido para a Sidebar) ---

with st.sidebar:
    st.divider()
    
    github_icon_svg = """
    <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="24" height="24">
    <title>GitHub</title>
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
    </svg>
    """
    linkedin_icon_svg = """
    <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="24" height="24">
    <title>LinkedIn</title>
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
    </svg>
    """

    # Links
    github_url = "https://github.com/caufreitxs026"
    linkedin_url = "https://www.linkedin.com/in/cauafreitas"

    # Renderização do rodapé na sidebar
    st.markdown(f"""
    <div class="sidebar-footer">
        <a href="{github_url}" target="_blank">{github_icon_svg}</a>
        <a href="{linkedin_url}" target="_blank">{linkedin_icon_svg}</a>
    </div>
    """, unsafe_allow_html=True)
