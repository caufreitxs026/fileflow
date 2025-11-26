import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io
import json # Importação para o Bloco 4
from PIL import Image
from pdf2docx import Converter as PDFToWordConverter
from fpdf import FPDF
from rembg import remove
import os
import zipfile  # Para processamento em lote
from pypdf import PdfWriter, PdfReader # Para ferramentas de PDF

# --- Funções de Conversão (Bloco 1) ---

def convert_pdf_to_word(file_bytes):
    """Converte bytes de PDF para bytes de DOCX."""
    try:
        pdf_temp_path = f"temp_input_{hash(file_bytes)}.pdf"
        docx_temp_path = f"temp_output_{hash(file_bytes)}.docx"
        
        with open(pdf_temp_path, "wb") as f:
            f.write(file_bytes)
            
        cv = PDFToWordConverter(pdf_temp_path)
        cv.convert(docx_temp_path, start=0, end=None)
        cv.close()

        with open(docx_temp_path, "rb") as f:
            docx_bytes = f.read()

        os.remove(pdf_temp_path)
        os.remove(docx_temp_path)
        
        return docx_bytes

    except Exception as e:
        if os.path.exists(pdf_temp_path):
            os.remove(pdf_temp_path)
        if os.path.exists(docx_temp_path):
            os.remove(docx_temp_path)
        st.error(f"Erro ao converter PDF para Word: {e}")
        return None


def convert_image_to_format(file_bytes, target_format):
    """Converte bytes de imagem (PNG/JPG) para um novo formato (PNG/JPG)."""
    img = Image.open(io.BytesIO(file_bytes))
    
    # CORREÇÃO: O Pillow exige "JPEG" como nome do formato interno, "JPG" causa erro
    save_format = target_format
    if target_format == "JPG":
        save_format = "JPEG"
    
    # Garante que imagens PNG com transparência (RGBA) possam ser salvas como JPG (RGB)
    if save_format == "JPEG" and img.mode == "RGBA":
        img = img.convert("RGB")
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format=save_format)
    return output_buffer.getvalue()

def convert_excel_to_pdf(file_bytes):
    """Converte o primeiro sheet de um Excel para um PDF simples."""
    df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    
    # Ajuste para evitar divisão por zero se o df estiver vazio
    num_cols = len(df.columns)
    if num_cols == 0:
        return b"" # Retorna PDF vazio se não houver colunas
        
    col_width = pdf.w / (num_cols + 1) # Um pouco mais de margem
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
        
    pdf_bytes = pdf.output(dest='S').encode('latin-1') 
    return pdf_bytes

def convert_image_to_pdf(file_bytes):
    """Salva uma imagem (JPG ou PNG) como um arquivo PDF."""
    img = Image.open(io.BytesIO(file_bytes))
    
    if img.mode == 'RGBA':
        img = img.convert('RGB')
        
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="PDF", resolution=100.0)
    return output_buffer.getvalue()

# --- Funções de Imagem (Bloco 2) ---

def remove_background(file_bytes):
    """Remove o fundo de uma imagem."""
    try:
        return remove(file_bytes)
    except Exception as e:
        st.error(f"Erro ao remover fundo: {e}. A imagem pode ser muito complexa ou estar em um formato inesperado.")
        return None

def optimize_image(file_bytes):
    """Otimiza uma imagem (JPG/PNG) para reduzir o tamanho."""
    img = Image.open(io.BytesIO(file_bytes))
    output_buffer = io.BytesIO()
    img.save(output_buffer, format=img.format, quality=85, optimize=True)
    return output_buffer.getvalue()

# --- Funções de PDF (Bloco 3) ---

def merge_pdfs(files_list):
    """Junta múltiplos arquivos PDF (lista de bytes) em um só."""
    writer = PdfWriter()
    for file_bytes in files_list:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            writer.add_page(page)
    
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    writer.close()
    return output_buffer.getvalue()

def split_pdf(file_bytes):
    """Divide um PDF em páginas individuais e retorna um .zip."""
    reader = PdfReader(io.BytesIO(file_bytes))
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            page_buffer = io.BytesIO()
            writer.write(page_buffer)
            writer.close()
            page_buffer.seek(0)
            
            zf.writestr(f"pagina_{i + 1}.pdf", page_buffer.getvalue())
            
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# --- Funções de Dados (Bloco 4 - NOVO) ---

def convert_excel_to_json(file_bytes):
    """Converte o primeiro sheet de um Excel para JSON (orient=records)."""
    df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    # force_ascii=False para suportar acentos
    json_string = df.to_json(orient='records', indent=4, force_ascii=False)
    return json_string.encode('utf-8')

def convert_csv_to_json(file_bytes):
    """Converte um CSV para JSON (orient=records)."""
    try:
        # Tenta UTF-8 primeiro
        df = pd.read_csv(io.BytesIO(file_bytes))
    except UnicodeDecodeError:
        # Tenta latin-1 como fallback
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1')
        
    json_string = df.to_json(orient='records', indent=4, force_ascii=False)
    return json_string.encode('utf-8')

def convert_json_to_csv(file_bytes):
    """Converte um JSON (lista de objetos) para CSV."""
    # Decodifica os bytes para string
    json_string = file_bytes.decode('utf-8')
    json_data = json.loads(json_string)
    
    # json_normalize é ótimo para achatar JSONs aninhados
    df = pd.json_normalize(json_data)
    
    output_buffer = io.StringIO()
    df.to_csv(output_buffer, index=False)
    return output_buffer.getvalue().encode('utf-8')


# --- INTERFACE GRÁFICA (UI) ---

st.set_page_config(
    page_title="FileFlow",
    layout="centered"
)

# CSS (O mesmo de antes)
st.markdown("""
<style>
    /* --- Início do Bloco da Logo --- */
	.logo-text {
		font-family: 'Courier New', monospace;
		font-size: 28px;
		font-weight: bold;
		padding-top: 20px;
	}
	.logo-file {
		color: #FFFFFF; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
	}
	.logo-flow {
		color: #E30613; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
	}
	@media (prefers-color-scheme: dark) {
		.logo-file {
			color: #FFFFFF; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
		}
		.logo-flow {
			color: #FF4B4B; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
		}
	}
	/* --- Fim do Bloco da Logo --- */

    /* --- Estilos para o footer (Rodapé Fixo) --- */
    .footer {
        text-align: center; position: fixed; left: 0; bottom: 0;
        width: 100%; padding: 1rem; color: #888; background-color: transparent;
    }
    .footer a {
        margin: 0 10px; display: inline-block; transition: transform 0.2s ease;
    }
    .footer a:hover { transform: scale(1.1); }
    .footer svg {
        width: 24px; height: 24px; fill: #888; transition: fill 0.3s;
    }
    .footer a:hover svg { fill: #FFF; }
    @media (prefers-color-scheme: light) {
        .footer a:hover svg { fill: #000; }
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

# --- Seletor de Ferramenta (RÓTULOS ATUALIZADOS) ---
tool_selection = st.radio(
    "Escolha a ferramenta:",
    ["Conversor", "Imagem (IA)", "PDF", "Dados"], # Rótulos curtos
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- Bloco 1: Conversor Universal (Condicional atualizada) ---
if tool_selection == "Conversor":
    with st.container(border=True):
        st.title("Conversor Universal de Arquivos")
        st.markdown("Selecione a conversão desejada e faça o upload do seu arquivo.")
        
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
        
        # Modo Lote (Não disponível para Excel para PDF)
        modo_lote = False
        if option != "Excel para PDF (.pdf)":
            modo_lote = st.toggle("Ativar processamento em lote")

        uploaded_files = st.file_uploader(
            f"Faça upload do(s) arquivo(s) ({selected_types})",
            type=selected_types,
            accept_multiple_files=modo_lote,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            # Garante que 'uploaded_files' seja sempre uma lista
            if not modo_lote:
                uploaded_files = [uploaded_files] # Transforma o arquivo único em lista
            
            # --- Lógica de Processamento (Lote ou Único) ---
            if modo_lote:
                # --- Modo Lote (ZIP) ---
                with st.spinner(f"Processando {len(uploaded_files)} arquivos..."):
                    try:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                            for uploaded_file in uploaded_files:
                                file_bytes = uploaded_file.getvalue()
                                base_name = uploaded_file.name.split('.')[0]
                                output_bytes = None
                                file_name_in_zip = "erro.txt"
                                
                                if option == "PDF para Word (.docx)":
                                    output_bytes = convert_pdf_to_word(file_bytes)
                                    file_name_in_zip = f"{base_name}.docx"
                                elif option == "PNG para JPG":
                                    output_bytes = convert_image_to_format(file_bytes, "JPG")
                                    file_name_in_zip = f"{base_name}.jpg"
                                elif option == "JPG para PNG":
                                    output_bytes = convert_image_to_format(file_bytes, "PNG")
                                    file_name_in_zip = f"{base_name}.png"
                                elif option == "Imagem (JPG/PNG) para PDF":
                                    output_bytes = convert_image_to_pdf(file_bytes)
                                    file_name_in_zip = f"{base_name}.pdf"
                                
                                if output_bytes:
                                    zf.writestr(file_name_in_zip, output_bytes)
                        
                        zip_buffer.seek(0)
                        st.success("Conversão em lote concluída!")
                        st.download_button(
                            label="Baixar Arquivos (.zip)",
                            data=zip_buffer,
                            file_name="conversao_em_lote.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Ocorreu um erro durante o processamento em lote: {e}")

            else:
                # --- Modo Arquivo Único ---
                with st.spinner("Convertendo..."):
                    try:
                        uploaded_file = uploaded_files[0] # Pega o primeiro (e único) arquivo
                        file_bytes = uploaded_file.getvalue()
                        output_bytes = None
                        file_name = "conversao"
                        mime = "application/octet-stream"
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
                        
                        if output_bytes:
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


# --- Bloco 2: Ferramentas de Imagem (Condicional atualizada) ---
elif tool_selection == "Imagem (IA)":
    with st.container(border=True):
        st.title("Ferramentas de Imagem (com IA)") # Título completo mantido
        st.markdown("Remova fundos de imagens usando IA ou otimize o tamanho de arquivos.")

        image_options = {
            "Remover Fundo (IA)": "png",
            "Otimizar Imagem": None # Mantém extensão original
        }
        
        img_option = st.selectbox(
            "Selecione a ferramenta de imagem:",
            list(image_options.keys())
        )
        
        modo_lote_img = st.toggle("Ativar processamento em lote")
        
        uploaded_files_img = st.file_uploader(
            "Faça upload do(s) arquivo(s) (JPG ou PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=modo_lote_img,
            label_visibility="collapsed"
        )
        
        if uploaded_files_img:
            if not modo_lote_img:
                uploaded_files_img = [uploaded_files_img] # Transforma em lista
            
            if modo_lote_img:
                # --- Modo Lote (ZIP) ---
                with st.spinner(f"Processando {len(uploaded_files_img)} imagens..."):
                    try:
                        zip_buffer_img = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer_img, 'w', zipfile.ZIP_DEFLATED) as zf_img:
                            for uploaded_image in uploaded_files_img:
                                img_bytes = uploaded_image.getvalue()
                                base_name_img = uploaded_image.name.split('.')[0]
                                output_img_bytes = None
                                file_name_in_zip_img = "erro.txt"
                                
                                if img_option == "Remover Fundo (IA)":
                                    output_img_bytes = remove_background(img_bytes)
                                    file_name_in_zip_img = f"{base_name_img}_sem_fundo.png"
                                elif img_option == "Otimizar Imagem":
                                    output_img_bytes = optimize_image(img_bytes)
                                    ext_img = uploaded_image.name.split('.')[-1]
                                    file_name_in_zip_img = f"{base_name_img}_otimizada.{ext_img}"
                                
                                if output_img_bytes:
                                    zf_img.writestr(file_name_in_zip_img, output_img_bytes)
                        
                        zip_buffer_img.seek(0)
                        st.success("Processamento em lote concluído!")
                        st.download_button(
                            label="Baixar Imagens (.zip)",
                            data=zip_buffer_img,
                            file_name="imagens_processadas.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Ocorreu um erro durante o processamento em lote: {e}")
            else:
                # --- Modo Arquivo Único (com Preview) ---
                with st.spinner("Processando imagem..."):
                    try:
                        uploaded_image = uploaded_files_img[0]
                        img_bytes = uploaded_image.getvalue()
                        output_img_bytes = None
                        file_name_img = "imagem_processada"
                        mime_img = "application/octet-stream"
                        base_name_img = uploaded_image.name.split('.')[0]
                        
                        if img_option == "Remover Fundo (IA)":
                            output_img_bytes = remove_background(img_bytes)
                            file_name_img = f"{base_name_img}_sem_fundo.png"
                            mime_img = "image/png"
                        elif img_option == "Otimizar Imagem":
                            output_img_bytes = optimize_image(img_bytes)
                            ext_img = uploaded_image.name.split('.')[-1]
                            file_name_img = f"{base_name_img}_otimizada.{ext_img}"
                            mime_img = uploaded_image.type

                        if output_img_bytes:
                            st.success("Processamento concluído!")
                            st.download_button(
                                label="Baixar Imagem Processada",
                                data=output_img_bytes,
                                file_name=file_name_img,
                                mime=mime_img,
                                use_container_width=True
                            )
                            
                            st.divider()
                            if img_option == "Remover Fundo (IA)":
                                st.markdown("##### Comparativo:")
                                col1, col2 = st.columns(2)
                                col1.image(img_bytes, caption="Original")
                                col2.image(output_img_bytes, caption="Fundo Removido")
                            elif img_option == "Otimizar Imagem":
                                st.markdown("##### Preview da Imagem Otimizada:")
                                st.image(output_img_bytes, caption="Imagem Otimizada")

                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar a imagem: {e}")


# --- Bloco 3: Ferramentas de PDF (Condicional atualizada) ---
elif tool_selection == "PDF":
    with st.container(border=True):
        st.title("Ferramentas de PDF") # Título completo mantido
        st.markdown("Combine ou separe seus arquivos PDF.")
        
        pdf_option = st.selectbox(
            "Selecione a ferramenta de PDF:",
            ["Juntar PDFs", "Dividir PDF (por página)"]
        )
        
        if pdf_option == "Juntar PDFs":
            st.markdown("Faça upload de dois ou mais arquivos PDF para combiná-los.")
            uploaded_pdfs = st.file_uploader(
                "Selecione os PDFs para juntar",
                type="pdf",
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            
            if uploaded_pdfs and len(uploaded_pdfs) >= 2:
                with st.spinner(f"Juntando {len(uploaded_pdfs)} PDFs..."):
                    try:
                        files_bytes_list = [f.getvalue() for f in uploaded_pdfs]
                        merged_pdf_bytes = merge_pdfs(files_bytes_list)
                        
                        st.success("PDFs juntados com sucesso!")
                        st.download_button(
                            label="Baixar PDF Juntado",
                            data=merged_pdf_bytes,
                            file_name="pdf_juntado.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao juntar os PDFs: {e}")
            elif uploaded_pdfs and len(uploaded_pdfs) < 2:
                st.warning("Você precisa fazer upload de pelo menos 2 arquivos PDF para juntar.")

        elif pdf_option == "Dividir PDF (por página)":
            st.markdown("Faça upload de um PDF para dividi-lo em páginas separadas (entregue como .zip).")
            uploaded_pdf_split = st.file_uploader(
                "Selecione o PDF para dividir",
                type="pdf",
                accept_multiple_files=False,
                label_visibility="collapsed"
            )
            
            if uploaded_pdf_split:
                with st.spinner("Dividindo PDF..."):
                    try:
                        pdf_bytes = uploaded_pdf_split.getvalue()
                        zip_bytes = split_pdf(pdf_bytes)
                        
                        st.success("PDF dividido com sucesso!")
                        st.download_button(
                            label="Baixar Páginas (.zip)",
                            data=zip_bytes,
                            file_name="pdf_dividido.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao dividir o PDF: {e}")

# --- Bloco 4: Ferramentas de Dados (Condicional atualizada) ---
elif tool_selection == "Dados":
    with st.container(border=True):
        st.title("Ferramentas de Dados") # Título completo mantido
        st.markdown("Converta formatos de dados estruturados (Excel, CSV, JSON).")
        
        data_options = {
            "Excel (.xlsx) para JSON": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "CSV para JSON": ("csv", "text/csv"),
            "JSON para CSV": ("json", "application/json"),
        }
        
        data_option = st.selectbox(
            "Selecione o tipo de conversão:",
            list(data_options.keys())
        )
        
        selected_data_types = data_options[data_option][0]
        
        uploaded_data_file = st.file_uploader(
            f"Faça upload do seu arquivo ({selected_data_types})",
            type=selected_data_types,
            accept_multiple_files=False, # Modo lote não implementado para dados
            label_visibility="collapsed"
        )
        
        if uploaded_data_file:
            with st.spinner("Convertendo dados..."):
                try:
                    data_bytes = uploaded_data_file.getvalue()
                    output_data_bytes = None
                    data_file_name = "dados"
                    data_mime = "application/octet-stream"
                    data_base_name = uploaded_data_file.name.split('.')[0]

                    if data_option == "Excel (.xlsx) para JSON":
                        output_data_bytes = convert_excel_to_json(data_bytes)
                        data_file_name = f"{data_base_name}.json"
                        data_mime = "application/json"
                    elif data_option == "CSV para JSON":
                        output_data_bytes = convert_csv_to_json(data_bytes)
                        data_file_name = f"{data_base_name}.json"
                        data_mime = "application/json"
                    elif data_option == "JSON para CSV":
                        output_data_bytes = convert_json_to_csv(data_bytes)
                        data_file_name = f"{data_base_name}.csv"
                        data_mime = "text/csv"

                    if output_data_bytes:
                        st.success("Conversão de dados concluída!")
                        st.download_button(
                            label="Baixar Arquivo Convertido",
                            data=output_data_bytes,
                            file_name=data_file_name,
                            mime=data_mime,
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Ocorreu um erro ao converter os dados: {e}")
                    st.exception(e) # Mostra o stack trace para depuração


# --- Rodapé Fixo (O mesmo de antes) ---
github_icon_svg = """
<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
<title>GitHub</title>
<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338. willfully-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
</svg>
"""
linkedin_icon_svg = """
<svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
<title>LinkedIn</title>
<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
</svg>
"""

github_url = "https://github.com/caufreitxs026"
linkedin_url = "https://www.linkedin.com/in/cauafreitas"

st.markdown(f"""
<div class="footer">
    <a href="{github_url}" target="_blank">{github_icon_svg}</a>
    <a href="{linkedin_url}" target="_blank">{linkedin_icon_svg}</a>
</div>
""", unsafe_allow_html=True)
