"""
PDF Image Extractor - Extract images from academic PDF papers.

Supports:
- Extract images from PDF files (using PyMuPDF/fitz)
- Filter by size and quality
- Save with proper naming for academic use
"""

import io
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

import fitz  # PyMuPDF
from PIL import Image

try:
    from config import Config
except ImportError:
    # Fallback if config not available
    class Config:
        MIN_IMAGE_WIDTH = 400
        MIN_IMAGE_HEIGHT = 300
        PDF_MIN_IMAGE_DPI = 150


class PDFImageExtractor:
    """Extract images from PDF documents."""

    def __init__(
        self,
        output_dir: str = "output/images",
        min_width: int = None,
        min_height: int = None,
        min_dpi: int = None
    ):
        """
        Initialize the PDF image extractor.

        Args:
            output_dir: Directory to save extracted images
            min_width: Minimum image width in pixels (default from Config)
            min_height: Minimum image height in pixels (default from Config)
            min_dpi: Minimum DPI for extracted images (default from Config)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use config values if not specified
        self.min_width = min_width or getattr(Config, 'MIN_IMAGE_WIDTH', 400)
        self.min_height = min_height or getattr(Config, 'MIN_IMAGE_HEIGHT', 300)
        self.min_dpi = min_dpi or getattr(Config, 'PDF_MIN_IMAGE_DPI', 150)
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def extract_images_from_pdf(
        self,
        pdf_path: Path,
        paper_id: str,
        max_images: int = 5
    ) -> List[Dict[str, any]]:
        """
        Extract images from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            paper_id: Paper ID for organizing extracted images
            max_images: Maximum number of images to extract

        Returns:
            List of dictionaries with image information
        """
        extracted_images = []

        try:
            # Open the PDF
            pdf_document = fitz.open(str(pdf_path))

            # Create paper-specific directory
            paper_dir = self.output_dir / paper_id / "pdf_extracted"
            paper_dir.mkdir(parents=True, exist_ok=True)

            image_count = 0

            # Iterate through pages
            for page_num in range(len(pdf_document)):
                if image_count >= max_images:
                    break

                page = pdf_document[page_num]

                # Get images on this page
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list):
                    if image_count >= max_images:
                        break

                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Check file size
                    if len(image_bytes) < 1000:  # Skip tiny images
                        continue

                    # Try to open with PIL to check dimensions
                    try:
                        pil_image = Image.open(io.BytesIO(image_bytes))
                    except Exception as e:
                        continue

                    # Check minimum dimensions
                    if pil_image.width < self.min_width or pil_image.height < self.min_height:
                        continue

                    # Convert to RGB if necessary
                    if pil_image.mode in ('RGBA', 'P', 'LA'):
                        pil_image = pil_image.convert('RGB')
                        image_ext = 'png'

                    # Generate filename
                    image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
                    filename = f"pdf_img_{image_count + 1:02d}_{image_hash}.{image_ext}"
                    filepath = paper_dir / filename

                    # Save image
                    if image_ext in ['jpg', 'jpeg']:
                        pil_image.save(filepath, quality=95, optimize=True)
                    else:
                        pil_image.save(filepath)

                    # Store image info
                    extracted_images.append({
                        'number': image_count + 1,
                        'filepath': filepath,
                        'filename': filename,
                        'page': page_num + 1,
                        'width': pil_image.width,
                        'height': pil_image.height,
                        'source': 'pdf_extraction',
                        'type': 'extracted',
                        'title': f'Extracted from page {page_num + 1}'
                    })

                    image_count += 1
                    print(f"  Extracted image {image_count}: {pil_image.width}x{pil_image.height} from page {page_num + 1}")

            pdf_document.close()

        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
            import traceback
            traceback.print_exc()

        return extracted_images

    def extract_images_from_url(
        self,
        url: str,
        paper_id: str,
        max_images: int = 5
    ) -> List[Dict[str, any]]:
        """
        Download PDF from URL and extract images.

        Args:
            url: URL to the PDF
            paper_id: Paper ID for organizing images
            max_images: Maximum number of images to extract

        Returns:
            List of dictionaries with image information
        """
        import requests
        import tempfile

        try:
            # Convert arXiv abstract URL to PDF URL
            if "arxiv.org/abs/" in url:
                arxiv_id = url.split("arxiv.org/abs/")[1].split("/")[0]
                url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # Download PDF
            print(f"  Downloading PDF from {url[:60]}...")
            response = requests.get(url, timeout=60, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = Path(tmp_file.name)

            # Extract images
            images = self.extract_images_from_pdf(tmp_path, paper_id, max_images)

            # Clean up temp file
            tmp_path.unlink()

            return images

        except Exception as e:
            print(f"Error downloading PDF from {url}: {e}")
            return []


def extract_images_from_literature(
    literature: List[Dict[str, any]],
    paper_id: str,
    max_total_images: int = 3,
    output_dir: str = "output/images"
) -> List[Dict[str, any]]:
    """
    Extract images from a list of literature papers (synchronous version).

    Args:
        literature: List of literature dictionaries
        paper_id: Paper ID for the main paper being generated
        max_total_images: Maximum total images to extract
        output_dir: Output directory

    Returns:
        List of extracted image information dictionaries
    """
    extractor = PDFImageExtractor(output_dir=output_dir)
    all_images = []

    print(f"\n[Image Extraction] Looking for images in {len(literature)} literature papers...")

    for i, paper in enumerate(literature):
        if len(all_images) >= max_total_images:
            break

        # Try to get PDF URL
        pdf_url = None

        if 'openAccessPdf' in paper and paper['openAccessPdf']:
            pdf_url = paper['openAccessPdf'].get('url') if isinstance(paper['openAccessPdf'], dict) else paper['openAccessPdf']
        elif 'pdf_url' in paper:
            pdf_url = paper['pdf_url']
        elif 'url' in paper and paper['url'].endswith('.pdf'):
            pdf_url = paper['url']

        if not pdf_url:
            continue

        print(f"\n  [{i+1}] Processing: {paper.get('title', 'Unknown')[:50]}...")

        remaining = max_total_images - len(all_images)
        extracted = extractor.extract_images_from_url(pdf_url, paper_id, max_images=remaining)

        for img in extracted:
            img['source_paper'] = paper.get('title', 'Unknown')
            img['paper_authors'] = paper.get('authors', 'Unknown')
            img['paper_year'] = paper.get('year', 'Unknown')

        all_images.extend(extracted)

    print(f"\n[Image Extraction] Total images extracted: {len(all_images)}")
    return all_images
