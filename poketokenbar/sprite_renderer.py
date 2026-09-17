import zlib
import struct
from pathlib import Path
from typing import List, Tuple, Optional

class PNGDecoder:
    """Pure Python lightweight PNG decoder for RGBA pixel array extraction.
    Supports 8-bit RGBA (6), 8-bit RGB (2), 4-bit & 8-bit Indexed (3) with PLTE/tRNS, and 8-bit Grayscale (0).
    """

    @staticmethod
    def decode_png(file_path: Path) -> Optional[Tuple[int, int, List[List[Tuple[int, int, int, int]]]]]:
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                return None

            idx = 8
            width = 0
            height = 0
            bit_depth = 0
            color_type = 0
            idat_data = b""
            palette = []
            trns = b""

            while idx < len(data):
                chunk_len = struct.unpack(">I", data[idx:idx+4])[0]
                chunk_type = data[idx+4:idx+8]
                chunk_body = data[idx+8:idx+8+chunk_len]
                idx += 8 + chunk_len + 4

                if chunk_type == b"IHDR":
                    width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_body[:10])
                elif chunk_type == b"PLTE":
                    palette = [(chunk_body[i], chunk_body[i+1], chunk_body[i+2]) for i in range(0, len(chunk_body), 3)]
                elif chunk_type == b"tRNS":
                    trns = chunk_body
                elif chunk_type == b"IDAT":
                    idat_data += chunk_body
                elif chunk_type == b"IEND":
                    break

            if not idat_data or width == 0 or height == 0:
                return None

            try:
                decompressed = zlib.decompress(idat_data)
            except Exception:
                return None

            if color_type == 6 and bit_depth == 8:
                line_bytes = width * 4
                bpp = 4
            elif color_type == 2 and bit_depth == 8:
                line_bytes = width * 3
                bpp = 3
            elif color_type == 3 and bit_depth == 8:
                line_bytes = width
                bpp = 1
            elif color_type == 3 and bit_depth == 4:
                line_bytes = (width + 1) // 2
                bpp = 1
            elif color_type == 0 and bit_depth == 8:
                line_bytes = width
                bpp = 1
            else:
                return None

            stride = line_bytes + 1
            if len(decompressed) < height * stride:
                return None

            pixels = []
            prev_row = [0] * line_bytes

            for y in range(height):
                row_bytes = decompressed[y * stride : (y + 1) * stride]
                filter_type = row_bytes[0]
                raw_pixels = list(row_bytes[1:])
                recon_row = [0] * line_bytes

                for i in range(line_bytes):
                    x = raw_pixels[i]
                    a = recon_row[i - bpp] if i >= bpp else 0
                    b = prev_row[i]
                    c = prev_row[i - bpp] if i >= bpp else 0

                    if filter_type == 0:  # None
                        val = x
                    elif filter_type == 1:  # Sub
                        val = (x + a) & 0xFF
                    elif filter_type == 2:  # Up
                        val = (x + b) & 0xFF
                    elif filter_type == 3:  # Average
                        val = (x + ((a + b) // 2)) & 0xFF
                    elif filter_type == 4:  # Paeth
                        p = a + b - c
                        pa = abs(p - a)
                        pb = abs(p - b)
                        pc = abs(p - c)
                        if pa <= pb and pa <= pc:
                            pr = a
                        elif pb <= pc:
                            pr = b
                        else:
                            pr = c
                        val = (x + pr) & 0xFF
                    else:
                        val = x
                    recon_row[i] = val

                prev_row = recon_row

                row_pixels = []
                for x in range(width):
                    if color_type == 6:
                        base = x * 4
                        row_pixels.append((recon_row[base], recon_row[base+1], recon_row[base+2], recon_row[base+3]))
                    elif color_type == 2:
                        base = x * 3
                        row_pixels.append((recon_row[base], recon_row[base+1], recon_row[base+2], 255))
                    elif color_type == 3 and bit_depth == 8:
                        pal_idx = recon_row[x]
                        if pal_idx < len(palette):
                            r, g, b = palette[pal_idx]
                            a = trns[pal_idx] if pal_idx < len(trns) else 255
                            row_pixels.append((r, g, b, a))
                        else:
                            row_pixels.append((0, 0, 0, 0))
                    elif color_type == 3 and bit_depth == 4:
                        byte_val = recon_row[x // 2]
                        pal_idx = (byte_val >> 4) & 0x0F if x % 2 == 0 else (byte_val & 0x0F)
                        if pal_idx < len(palette):
                            r, g, b = palette[pal_idx]
                            a = trns[pal_idx] if pal_idx < len(trns) else 255
                            row_pixels.append((r, g, b, a))
                        else:
                            row_pixels.append((0, 0, 0, 0))
                    elif color_type == 0 and bit_depth == 8:
                        val = recon_row[x]
                        row_pixels.append((val, val, val, 255))
                pixels.append(row_pixels)

            return width, height, pixels
        except Exception:
            return None

class SpriteRenderer:
    """Renders pixel data into TrueColor ANSI block characters for Linux CLI terminal."""

    _ansi_cache = {}  # (str(file_path), max_cols, mtime) -> ansi_str

    @classmethod
    def render_png_to_ansi(cls, file_path: Path, max_cols: int = 32, center_width: int = 0) -> str:
        try:
            mtime = file_path.stat().st_mtime
            cache_key = (str(file_path.resolve()), max_cols, center_width, mtime)
            if cache_key in cls._ansi_cache:
                return cls._ansi_cache[cache_key]
        except Exception:
            cache_key = None

        ansi_res = cls._compute_ansi(file_path, max_cols, center_width)
        if cache_key and ansi_res:
            cls._ansi_cache[cache_key] = ansi_res
        return ansi_res

    @classmethod
    def _compute_ansi(cls, file_path: Path, max_cols: int = 32, center_width: int = 0) -> str:
        # Try PIL first if available
        try:
            from PIL import Image
            img = Image.open(file_path).convert("RGBA")
            w, h = img.size
            pixels = []
            for y in range(h):
                row = []
                for x in range(w):
                    row.append(img.getpixel((x, y)))
                pixels.append(row)
            return cls._draw_ansi_blocks(w, h, pixels, max_cols, center_width)
        except Exception:
            pass

        # Fall back to pure Python PNG decoder
        res = PNGDecoder.decode_png(file_path)
        if not res:
            return " [Sprite unavailable] "
        w, h, pixels = res
        return cls._draw_ansi_blocks(w, h, pixels, max_cols, center_width)

    @classmethod
    def _draw_ansi_blocks(cls, width: int, height: int, pixels: List[List[Tuple[int, int, int, int]]], max_cols: int, center_width: int = 0) -> str:
        # Target scale
        scale_x = max(1, width // max_cols)
        scale_y = scale_x * 2  # 2 vertical pixels per line character

        visual_width = len(range(0, width, scale_x))
        padding = " " * max(0, (center_width - visual_width) // 2)

        lines = []
        for y in range(0, height - 1, scale_y):
            line_str = padding
            for x in range(0, width, scale_x):
                # Top pixel
                top_p = pixels[y][x]
                # Bottom pixel
                bot_p = pixels[min(y + scale_x, height - 1)][x]

                top_r, top_g, top_b, top_a = top_p
                bot_r, bot_g, bot_b, bot_a = bot_p

                # Handle transparency
                if top_a < 50 and bot_a < 50:
                    line_str += " "
                elif top_a >= 50 and bot_a < 50:
                    # Upper half block
                    line_str += f"\033[38;2;{top_r};{top_g};{top_b}m▀\033[0m"
                elif top_a < 50 and bot_a >= 50:
                    # Lower half block
                    line_str += f"\033[38;2;{bot_r};{bot_g};{bot_b}m▄\033[0m"
                else:
                    # Both visible: foreground top, background bottom
                    line_str += f"\033[38;2;{top_r};{top_g};{top_b}m\033[48;2;{bot_r};{bot_g};{bot_b}m▀\033[0m"
            lines.append(line_str)
            
        # Crop empty transparent padding lines from top and bottom
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)
