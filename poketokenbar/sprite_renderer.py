import zlib
import struct
from pathlib import Path
from typing import List, Tuple, Optional

class PNGDecoder:
    """Pure Python lightweight PNG decoder for RGBA pixel array extraction."""

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
            idat_data = b""

            while idx < len(data):
                chunk_len = struct.unpack(">I", data[idx:idx+4])[0]
                chunk_type = data[idx+4:idx+8]
                chunk_body = data[idx+8:idx+8+chunk_len]
                idx += 8 + chunk_len + 4

                if chunk_type == b"IHDR":
                    width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_body[:10])
                    # Expecting 8-bit RGBA (6) or RGB (2)
                    if bit_depth != 8:
                        return None
                elif chunk_type == b"IDAT":
                    idat_data += chunk_body
                elif chunk_type == b"IEND":
                    break

            if not idat_data or width == 0 or height == 0:
                return None

            decompressed = zlib.decompress(idat_data)
            bytes_per_pixel = 4  # Assuming RGBA
            stride = width * bytes_per_pixel + 1

            pixels = []
            prev_row = [0] * (width * bytes_per_pixel)

            for y in range(height):
                row_bytes = decompressed[y * stride : (y + 1) * stride]
                filter_type = row_bytes[0]
                raw_pixels = list(row_bytes[1:])
                recon_row = []

                for i in range(width * bytes_per_pixel):
                    x = raw_pixels[i]
                    a = recon_row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                    b = prev_row[i]
                    c = prev_row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0

                    if filter_type == 0:  # None
                        val = x
                    elif filter_type == 1:  # Sub
                        val = (x + a) & 0xFF
                    elif filter_type == 2:  # Up
                        val = (x + b) & 0xFF
                    elif filter_type == 3:  # Average
                        val = (x + (a + b) // 2) & 0xFF
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
                    recon_row.append(val)

                prev_row = recon_row
                row_pixels = []
                for x_idx in range(width):
                    base = x_idx * 4
                    if base + 3 < len(recon_row):
                        row_pixels.append((recon_row[base], recon_row[base+1], recon_row[base+2], recon_row[base+3]))
                    else:
                        row_pixels.append((0, 0, 0, 0))
                pixels.append(row_pixels)

            return width, height, pixels
        except Exception:
            return None

class SpriteRenderer:
    """Renders pixel data into TrueColor ANSI block characters for Linux CLI terminal."""

    _ansi_cache = {}  # (str(file_path), max_cols, mtime) -> ansi_str

    @classmethod
    def render_png_to_ansi(cls, file_path: Path, max_cols: int = 32) -> str:
        try:
            mtime = file_path.stat().st_mtime
            cache_key = (str(file_path.resolve()), max_cols, mtime)
            if cache_key in cls._ansi_cache:
                return cls._ansi_cache[cache_key]
        except Exception:
            cache_key = None

        ansi_res = cls._compute_ansi(file_path, max_cols)
        if cache_key and ansi_res:
            cls._ansi_cache[cache_key] = ansi_res
        return ansi_res

    @classmethod
    def _compute_ansi(cls, file_path: Path, max_cols: int = 32) -> str:
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
            return cls._draw_ansi_blocks(w, h, pixels, max_cols)
        except Exception:
            pass

        # Fall back to pure Python PNG decoder
        res = PNGDecoder.decode_png(file_path)
        if not res:
            return " [Sprite unavailable] "
        w, h, pixels = res
        return cls._draw_ansi_blocks(w, h, pixels, max_cols)

    @classmethod
    def _draw_ansi_blocks(cls, width: int, height: int, pixels: List[List[Tuple[int, int, int, int]]], max_cols: int) -> str:
        # Target scale
        scale_x = max(1, width // max_cols)
        scale_y = scale_x * 2  # 2 vertical pixels per line character

        lines = []
        for y in range(0, height - 1, scale_y):
            line_str = ""
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

        return "\n".join(lines)
