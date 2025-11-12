import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io
from PIL import Image
from pdf2docx import Converter as PDFToWordConverter
from fpdf import FPDF
# from rembg import remove # TESTE: Desabilitando a importação

# --- Funções de Conversão (Bloco 1) ---

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

# --- Funções de Otimização de Imagem (Bloco 2) ---

# TESTE: Desabilitando a função que usa rembg
# def remove_background(file_bytes):
#     """Remove o fundo de uma imagem."""
#     output_bytes = remove(file_bytes)
#     return output_bytes

def optimize_image(file_bytes):
    """Otimiza uma imagem (JPG ou PNG)."""
    img = Image.open(io.BytesIO(file_bytes))
    output_buffer = io.BytesIO()
    
    file_format = img.format
    if file_format == 'JPEG':
        img.save(output_buffer, format='JPEG', optimize=True, quality=85)
    elif file_format == 'PNG':
        img.save(output_buffer, format='PNG', optimize=True)
    else:
        # Se não for JPG/PNG, apenas retorna os bytes originais
        return file_bytes
        
    return output_buffer.getvalue()


# --- INTERFACE GRÁFICA (UI) ---

st.set_page_config(
    page_title="FileFlow Conversor",
    layout="centered"
)

# --- CSS Customizado (Logo + Footer + Main Container) ---
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

    /* --- CSS para Centralizar o Conteúdo --- */
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-top: 2rem;
        padding-bottom: 5rem; /* Adiciona espaço para o rodapé não sobrepor */
    }

    /* --- Estilos para o footer (Rodapé Fixo) --- */
    .footer {
        text-align: center;
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        padding: 1rem;
        color: #888;
        /* Adiciona um leve fundo para destacar em ambos os temas */
        background-color: var(--streamlit-theme-base)
    }
    .footer a {
        margin: 0 10px;
        display: inline-block;
        transition: transform 0.2s ease;
    }
    .footer svg { 
        width: 24px; 
        height: 24px; 
        fill: #888; 
        transition: fill 0.3s, transform 0.2s;
    }
    .footer a:hover svg { 
        fill: #FF4B4B; /* Cor vermelha do logo */
        transform: scale(1.1);
    }
    .footer a:hover {
        transform: scale(1.1);
    }
    
    @media (prefers-color-scheme: dark) {
        .footer svg { fill: #888; }
        .footer a:hover svg { fill: #FF4B4B; }
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

# --- Bloco 1: Conversor Universal ---
with st.container(border=True):
    st.title("Conversor Universal de Arquivos")
    st.markdown("Selecione a conversão desejada e faça o upload do seu arquivo.")

    # Dicionário de opções de conversão
    conversion_options = {
        "PDF (Geral) para Word": (["pdf"], "docx", "PDF"),
        "Excel para PDF": (["xlsx", "xls"], "pdf", "Excel"),
        "PNG para JPG": (["png"], "jpg", "PNG"),
        "JPG para PNG": (["jpg", "jpeg"], "png", "JPG"),
        "Imagem (PNG/JPG) para PDF": (["png", "jpg", "jpeg"], "pdf", "Imagem")
    }

    option = st.selectbox(
        "Escolha o tipo de conversão:",
        list(conversion_options.keys()),
        key="conversor_select" # Chave única
    )

    in_ext, out_ext, label = conversion_options[option]

    uploaded_file = st.file_uploader(
        f"Selecione o arquivo {label}",
        type=in_ext,
        label_visibility="collapsed",
        key="conversor_uploader" # Chave única
    )

    if uploaded_file:
        with st.spinner("Processando..."):
            try:
                file_bytes = uploaded_file.getvalue()
                output_bytes = None
                
                base_name = uploaded_file.name.split('.')[0]
                file_name = f"{base_name}.{out_ext}"

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

st.divider() # Separador visual

# --- Bloco 2: Ferramentas de Imagem ---
with st.container(border=True):
    st.title("Otimizador de Imagens")
    st.markdown("Remova fundos ou otimize o tamanho de arquivos JPG/PNG.")

    image_options = {
        # "Remover Fundo": ("png", "Imagem"), # TESTE: Desabilitando a opção
        "Otimizar Imagem": (None, "JPG ou PNG") # 'None' significa que a extensão original será mantida
    }
    
    img_option = st.selectbox(
        "Escolha a ferramenta de imagem:",
        list(image_options.keys()),
        key="imagem_select" # Chave única
    )
    
    out_ext_img, label_img = image_options[img_option]

    uploaded_image = st.file_uploader(
        f"Selecione o arquivo {label_img}",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key="imagem_uploader" # Chave única
    )

    if uploaded_image:
        with st.spinner("Processando imagem..."):
            try:
                img_bytes = uploaded_image.getvalue()
                output_img_bytes = None
                
                # Define o nome do arquivo de saída
                base_name_img = uploaded_image.name.split('.')[0]
                
                # TESTE: Desabilitando o bloco lógico
                # if img_option == "Remover Fundo":
                #     out_ext_img = "png" # Saída sempre será PNG para fundos transparentes
                #     file_name_img = f"{base_name_img}_sem_fundo.png"
                #     output_img_bytes = remove_background(img_bytes)
                
                if img_option == "Otimizar Imagem": # Alterado de 'elif' para 'if'
                    # Mantém a extensão original
                    out_ext_img = uploaded_image.name.split('.')[-1]
                    file_name_img = f"{base_name_img}_otimizado.{out_ext_img}"
                    output_img_bytes = optimize_image(img_bytes)

                st.success("Imagem processada com sucesso!")
                st.download_button(
                    label=f"Baixar {file_name_img}",
                    data=output_img_bytes,
                    file_name=file_name_img,
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a imagem: {e}")


st.markdown('</div>', unsafe_allow_html=True) # Fecha o main-container


# --- Rodapé Fixo ---
github_icon_svg = """
<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
<title>GitHub</title>
<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
</svg>
"""
linkedin_icon_svg = """
<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
<title>LinkedIn</title>
<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
</svg>
"""

# Links
github_url = "https://github.com/caufreitxs026"
linkedin_url = "https://www.linkedin.com/in/cauafreitas"

# Renderização do rodapé
st.markdown(f"""
<div class="footer">
    <a href="{github_url}" target="_blank">{github_icon_svg}</a>
    <a href="{linkedin_url}" target="_blank">{linkedin_icon_svg}</a>
</div>
""", unsafe_allow_html=True)
