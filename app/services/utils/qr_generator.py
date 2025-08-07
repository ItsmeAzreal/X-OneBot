"""QR code generation utility."""
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw
import io
import requests
from typing import Optional, Dict


class QRCodeGenerator:
    """Generate QR codes with custom styling."""
    
    def generate_qr_code(
        self,
        data: str,
        size: int = 10,
        logo_url: Optional[str] = None,
        color: str = "#000000",
        bg_color: str = "#FFFFFF"
    ) -> Image:
        """
        Generate a QR code image.
        
        Args:
            data: Data to encode in QR code
            size: Size multiplier (10 = 300x300 pixels)
            logo_url: Optional logo URL to embed
            color: QR code color
            bg_color: Background color
            
        Returns:
            PIL Image object
        """
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H if logo_url else qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        
        # Add data
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create styled image
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(color, bg_color)
        )
        
        # Add logo if provided
        if logo_url:
            img = self._add_logo(img, logo_url)
        
        return img
    
    def _add_logo(self, qr_img: Image, logo_url: str) -> Image:
        """Add logo to center of QR code."""
        try:
            # Download logo
            response = requests.get(logo_url, timeout=5)
            logo = Image.open(io.BytesIO(response.content))
            
            # Calculate logo size (10% of QR code)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 10
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create white background circle for logo
            mask = Image.new('L', (logo_size + 20, logo_size + 20), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size + 20, logo_size + 20), fill=255)
            
            # Paste logo in center
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            qr_img.paste(logo, logo_pos, mask)
            
        except Exception as e:
            # If logo fails, return QR without logo
            print(f"Failed to add logo: {e}")
        
        return qr_img
    
    def generate_batch_qr_codes(
        self,
        tables: list,
        business_slug: str,
        **kwargs
    ) -> Dict[str, Image]:
        """
        Generate QR codes for multiple tables.
        
        Args:
            tables: List of table objects
            business_slug: Business URL slug
            **kwargs: Additional arguments for generate_qr_code
            
        Returns:
            Dictionary mapping table numbers to QR images
        """
        qr_codes = {}
        
        for table in tables:
            chat_url = f"https://xonebot.com/chat?business={business_slug}&table={table.qr_code_id}"
            qr_img = self.generate_qr_code(chat_url, **kwargs)
            qr_codes[table.table_number] = qr_img
        
        return qr_codes