import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io
from PIL import Image
from pdf2docx import Converter as PDFToWordConverter
from fpdf import FPDF
from rembg import remove
import os

# --- Funções de Conversão (Bloco 1) ---

def convert_pdf_to_word(file_bytes):
    """Converte bytes de PDF para bytes de DOCX."""
    try:
        # A biblioteca pdf2docx espera caminhos de arquivo,
        # então usamos arquivos temporários
        
        # 1. Salvar o PDF de entrada temporariamente
        pdf_temp_path = "temp_input.pdf"
        with open(pdf_temp_path, "wb") as f:
            f.write(file_bytes)
            
        # 2. Definir o caminho do DOCX de saída temporário
        docx_temp_path = "temp_output.docx"

        # 3. Realizar a conversão
        cv = PDFToWordConverter(pdf_temp_path)
        cv.convert(docx_temp_path, start=0, end=None)
        cv.close()

        # 4. Ler os bytes do arquivo DOCX de saída
        with open(docx_temp_path, "rb") as f:
            docx_bytes = f.read()

        # 5. Limpar arquivos temporários
        os.remove(pdf_temp_path)
        os.remove(docx_temp_path)
        
        return docx_bytes

    except Exception as e:
        # Tenta limpar em caso de erro
        if os.path.exists(pdf_temp_path):
            os.remove(pdf_temp_path)
        if os.path.exists(docx_temp_path):
            os.remove(docx_temp_path)
        raise e


def convert_image_to_format(file_bytes, target_format):
    """Converte bytes de imagem (PNG/JPG) para um novo formato (PNG/JPG)."""
    img = Image.open(io.BytesIO(file_bytes))
    
    # Garante que imagens PNG com transparência (RGBA) possam ser salvas como JPG (RGB)
    if target_format == "JPG" and img.mode == "RGBA":
        img = img.convert("RGB")
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format=target_format)
    return output_buffer.getvalue()

def convert_excel_to_pdf(file_bytes):
    """Converte o primeiro sheet de um Excel para um PDF simples."""
    df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    
    # Larguras de coluna (simples)
    col_width = pdf.w / (len(df.columns) + 1)
    row_height = pdf.font_size * 1.5

    # Cabeçalho
    for col in df.columns:
        pdf.cell(col_width, row_height, str(col), border=1, align='C')
    pdf.ln(row_height)
    
    # Dados
    for index, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1, align='L')
        pdf.ln(row_height)
        
    output_buffer = io.BytesIO()
    # Salvando os bytes do PDF na memória
    pdf_bytes = pdf.output(dest='S').encode('latin-1') 
    
    return pdf_bytes

def convert_image_to_pdf(file_bytes):
    """Salva uma imagem (JPG ou PNG) como um arquivo PDF."""
    img = Image.open(io.BytesIO(file_bytes))
    
    # Converte RGBA para RGB se for PNG para evitar erro no FPDF/Pillow
    if img.mode == 'RGBA':
        img = img.convert('RGB')
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="PDF", resolution=100.0)
    return output_buffer.getvalue()

# --- Funções de Otimização de Imagem (Bloco 2) ---

def remove_background(file_bytes):
    """Remove o fundo de uma imagem."""
    output_bytes = remove(file_bytes)
    return output_bytes

def optimize_image(file_bytes):
    """Otimiza uma imagem (JPG/PNG) para reduzir o tamanho."""
    img = Image.open(io.BytesIO(file_bytes))
    output_buffer = io.BytesIO()
    
    # Qualidade 85 é um bom equilíbrio
    img.save(output_buffer, format=img.format, quality=85, optimize=True)
    return output_buffer.getvalue()


# --- INTERFACE GRÁFICA (UI) ---

st.set_page_config(
    page_title="FileFlow",
    layout="centered"
)

# CSS para a Logo (Agora à Esquerda) e Rodapé (Fixo)
st.markdown("""
<style>
    /* --- Início do Bloco da Logo --- */
	.logo-text {
		font-family: 'Courier New', monospace;
		font-size: 28px; /* Ajuste o tamanho se necessário para as páginas internas */
		font-weight: bold;
		padding-top: 20px;
		/* text-align: center; */ /* REMOVIDO: Linha que centralizava a logo */
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

    /* --- Estilos para o footer (Rodapé Fixo) --- */
    .footer {
        text-align: center;
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        padding: 1rem;
        color: #888;
        background-color: transparent; /* Garante que não cubra o conteúdo */
    }
    .footer a {
        margin: 0 10px;
        display: inline-block;
        transition: transform 0.2s ease;
    }
    .footer a:hover {
        transform: scale(1.1);
    }
    .footer svg { /* Aplicar estilo ao SVG */
        width: 24px;
        height: 24px;
        fill: #888;
        transition: fill 0.3s;
    }
    .footer a:hover svg {
        fill: #FFF; /* Cor no hover (tema escuro) */
    }
    @media (prefers-color-scheme: light) {
        .footer a:hover svg {
            fill: #000; /* Cor no hover (tema claro) */
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Header (Logo no canto superior) ---
st.markdown(
    """
    <div class="logo-text">
        <span class="logo-text"><span class="logo-file">FILE</span><span class="logo-flow">FLOW</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Seletor de Ferramenta (NOVA LÓGICA) ---
tool_selection = st.radio(
    "Escolha a ferramenta:",
    ["Conversor Universal", "Otimizador de Imagens"],
    horizontal=True,
    label_visibility="collapsed" # Esconde o rótulo "Escolha a ferramenta:"
)

st.divider() # Linha separadora

# --- Bloco 1: Conversor Universal (Condicional) ---
if tool_selection == "Conversor Universal":
    with st.container(border=True):
        st.title("Conversor Universal de Arquivos")
        st.markdown("Selecione a conversão desejada e faça o upload do seu arquivo.")
        
        # Opções de conversão e tipos de arquivo aceitos
        conversion_options = {
            "PDF para Word (.docx)": ("pdf", "application/pdf"),
            "Excel para PDF (.pdf)": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "PNG para JPG": ("png", "image/png"),
            "JPG para PNG": ("jpg", "image/jpeg"),
            "Imagem (JPG/PNG) para PDF": (["jpg", "png"], ["image/jpeg", "image/png"]),
        }

        option = st.selectbox(
            "Selecione o tipo de conversão:",
            list(conversion_options.keys())
        )
        
        selected_types = conversion_options[option][0]
        
        # Uploader de arquivo
        uploaded_file = st.file_uploader(
            f"Faça upload do seu arquivo ({selected_types})",
            type=selected_types,
            label_visibility="collapsed"
        )
        
        # Lógica de processamento e download
        if uploaded_file:
            with st.spinner("Convertendo..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    output_bytes = None
                    file_name = "conversao"
                    
                    base_name = uploaded_file.name.split('.')[0]

                    if option == "PDF para Word (.docx)":
                        output_bytes = convert_pdf_to_word(file_bytes)
                        file_name = f"{base_name}.docx"
                        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    
                    elif option == "Excel para PDF (.pdf)":
                        output_bytes = convert_excel_to_pdf(file_bytes)
                        file_name = f"{base_name}.pdf"
                        mime = "application/pdf"

                    elif option == "PNG para JPG":
                        output_bytes = convert_image_to_format(file_bytes, "JPG")
                        file_name = f"{base_name}.jpg"
                        mime = "image/jpeg"

                    elif option == "JPG para PNG":
                        output_bytes = convert_image_to_format(file_bytes, "PNG")
                        file_name = f"{base_name}.png"
                        mime = "image/png"
                    
                    elif option == "Imagem (JPG/PNG) para PDF":
                        output_bytes = convert_image_to_pdf(file_bytes)
                        file_name = f"{base_name}.pdf"
                        mime = "application/pdf"

                    st.success("Conversão concluída!")
                    st.download_button(
                        label="Baixar Arquivo Convertido",
                        data=output_bytes,
                        file_name=file_name,
                        mime=mime,
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Ocorreu um erro durante a conversão: {e}")
                    st.exception(e) # Mostra o stack trace para depuração


# --- Bloco 2: Ferramentas de Imagem (Condicional) ---
elif tool_selection == "Otimizador de Imagens":
    with st.container(border=True):
        st.title("Otimizador de Imagens")
        st.markdown("Remova fundos ou otimize o tamanho de arquivos JPG/PNG.")

        image_options = {
            "Remover Fundo": ("png", "Imagem"),
            "Otimizar Imagem": (None, "JPG ou PNG") # 'None' significa que a extensão original será mantida
        }
        
        img_option = st.selectbox(
            "Selecione a ferramenta de imagem:",
            list(image_options.keys())
        )
        
        # Tipos de arquivo aceitos (JPG e PNG)
        accepted_img_types = ["jpg", "jpeg", "png"]
        
        uploaded_image = st.file_uploader(
            "Faça upload do seu arquivo (JPG ou PNG)",
            type=accepted_img_types,
            label_visibility="collapsed"
        )
        
        if uploaded_image:
            with st.spinner("Processando imagem..."):
                try:
                    # Armazena os bytes originais para o preview
                    img_bytes = uploaded_image.getvalue() 
                    
                    output_img_bytes = None
                    file_name_img = "imagem_processada"
                    mime_img = "application/octet-stream"
                    
                    # Define o nome do arquivo de saída
                    base_name_img = uploaded_image.name.split('.')[0]
                    
                    if img_option == "Remover Fundo":
                        output_img_bytes = remove_background(img_bytes)
                        file_name_img = f"{base_name_img}_sem_fundo.png"
                        mime_img = "image/png"
                    
                    elif img_option == "Otimizar Imagem":
                        output_img_bytes = optimize_image(img_bytes)
                        # Mantém a extensão original
                        out_ext_img = uploaded_image.name.split('.')[-1]
                        file_name_img = f"{base_name_img}_otimizada.{out_ext_img}"
                        mime_img = uploaded_image.type

                    st.success("Processamento concluído!")
                    st.download_button(
                        label="Baixar Imagem Processada",
                        data=output_img_bytes,
                        file_name=file_name_img,
                        mime=mime_img,
                        use_container_width=True
                    )
                    
                    # --- NOVO: Preview da Imagem ---
                    st.divider() # Adiciona um separador
                    
                    if img_option == "Remover Fundo":
                        st.markdown("##### Comparativo:")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(img_bytes, caption="Original")
                        with col2:
                            st.image(output_img_bytes, caption="Fundo Removido")
                    
                    elif img_option == "Otimizar Imagem":
                        st.markdown("##### Preview da Imagem Otimizada:")
                        st.image(output_img_bytes, caption="Imagem Otimizada")
                    # --- FIM DO NOVO PREVIEW ---

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a imagem: {e}")
                    st.exception(e) # Mostra o stack trace para depuração


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
