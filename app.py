
import streamlit as st
import fitz
import io
import zipfile
from PIL import Image

st.set_page_config(
    page_title="PDF to PNG Converter",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF to PNG Converter")
st.write("Convert PDF pages into high-quality PNG images for free.")

uploaded_file = st.file_uploader(
    "Upload your PDF file",
    type=["pdf"]
)

dpi = st.select_slider(
    "Image quality (DPI)",
    options=[72, 100, 150, 200, 300, 400, 600],
    value=200
)

page_option = st.radio(
    "Pages to convert",
    ["All pages", "Specific page range"]
)

page_range = ""

if page_option == "Specific page range":
    page_range = st.text_input(
        "Enter pages (e.g. 1-3 or 1,3,5)",
        value="1"
    )

if uploaded_file is not None:
    st.info(f"Uploaded file: {uploaded_file.name}")

    if st.button("Convert PDF to PNG", type="primary"):

        try:
            pdf_bytes = uploaded_file.getvalue()
            pdf_document = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            total_pages = len(pdf_document)

            if total_pages == 0:
                st.error("This PDF contains no pages.")
                st.stop()

            if page_option == "All pages":
                pages = list(range(total_pages))

            else:
                pages = []

                try:
                    parts = page_range.replace(" ", "").split(",")

                    for part in parts:
                        if "-" in part:
                            start, end = map(int, part.split("-"))

                            if start > end:
                                raise ValueError(
                                    "Page range must be in ascending order."
                                )

                            pages.extend(
                                range(start - 1, end)
                            )
                        else:
                            pages.append(int(part) - 1)

                    if not pages:
                        raise ValueError("No pages selected.")

                    if any(
                        p < 0 or p >= total_pages for p in pages
                    ):
                        raise ValueError(
                            f"Choose pages between 1 and {total_pages}."
                        )

                    pages = sorted(set(pages))

                except ValueError as error:
                    st.error(f"Invalid page range: {error}")
                    st.stop()

            scale = dpi / 72
            matrix = fitz.Matrix(scale, scale)

            png_files = []

            progress = st.progress(0)
            status = st.empty()

            for count, page_number in enumerate(pages):
                page = pdf_document.load_page(page_number)

                pixmap = page.get_pixmap(
                    matrix=matrix,
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pixmap.width, pixmap.height],
                    pixmap.samples
                )

                image_bytes = io.BytesIO()
                image.save(image_bytes, format="PNG")

                filename = (
                    f"{uploaded_file.name.rsplit('.', 1)[0]}"
                    f"_page_{page_number + 1}.png"
                )

                png_files.append(
                    (filename, image_bytes.getvalue())
                )

                progress.progress(
                    (count + 1) / len(pages)
                )

                status.text(
                    f"Converting page {page_number + 1} "
                    f"of {len(pages)}..."
                )

            pdf_document.close()

            st.session_state["png_files"] = png_files
            st.session_state["source_name"] = uploaded_file.name

            status.success("Conversion completed successfully!")

        except Exception as error:
            st.error(f"Conversion failed: {error}")

if "png_files" in st.session_state:
    png_files = st.session_state["png_files"]

    st.subheader("🖼️ Converted Images")
    st.write(f"Successfully converted {len(png_files)} page(s).")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:
        for filename, image_data in png_files:
            zip_file.writestr(filename, image_data)

    st.download_button(
        label="📦 Download All Images as ZIP",
        data=zip_buffer.getvalue(),
        file_name="converted_png_images.zip",
        mime="application/zip",
        type="primary"
    )

    st.divider()

    for filename, image_data in png_files:
        with st.expander(f"🖼️ {filename}"):
            st.image(image_data, use_container_width=True)

            st.download_button(
                label=f"Download {filename}",
                data=image_data,
                file_name=filename,
                mime="image/png",
                key=f"download_{filename}"
            )

st.divider()
st.caption("Free PDF-to-PNG Converter | Powered by Streamlit")
