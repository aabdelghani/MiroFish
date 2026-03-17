"""
文件解析工具
支持PDF、Markdown、TXT、XML文件的文本提取
File parsing utilities.
Extract text from PDF, Markdown, and TXT files.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional


def _read_text_with_fallback(file_path: str) -> str:
    """
    Read text file; on UTF-8 failure, detect encoding.
    Fallback order: UTF-8 -> charset_normalizer -> chardet -> UTF-8 with replace.
    """
    data = Path(file_path).read_bytes()

    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass

    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass

    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass

    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """File parser."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt', '.xml'}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from file. Args: file_path. Returns extracted text."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        elif suffix == '.xml':
            return cls._extract_from_xml(file_path)

        raise ValueError(f"无法处理的文件格式: {suffix}")
    
        
        raise ValueError(f"Unhandled file format: {suffix}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF required: pip install PyMuPDF")
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """Extract text from Markdown with encoding detection."""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from TXT with encoding detection."""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _extract_from_xml(file_path: str) -> str:
        """
        从XML文件提取文本，使用流式解析支持大文件。
        自动检测Wikipedia XML dump格式，提取文章标题和正文。
        对于普通XML，递归提取所有文本内容。
        """
        is_mediawiki = False
        try:
            for event, elem in ET.iterparse(file_path, events=('start',)):
                local_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if local_tag == 'mediawiki':
                    is_mediawiki = True
                break
        except ET.ParseError:
            pass

        if is_mediawiki:
            return FileParser._extract_mediawiki_xml(file_path)
        else:
            return FileParser._extract_generic_xml(file_path)

    @staticmethod
    def _extract_mediawiki_xml(file_path: str) -> str:
        """
        流式解析Wikipedia/MediaWiki XML dump。
        提取每篇文章的标题和正文，适合1GB+大文件。
        """
        parts = []
        current_title = None

        for event, elem in ET.iterparse(file_path, events=('end',)):
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if tag == 'title':
                current_title = (elem.text or '').strip()
            elif tag == 'text':
                raw = (elem.text or '').strip()
                if current_title and raw:
                    parts.append(f"=== {current_title} ===\n{raw}")
                elem.clear()
            elif tag == 'page':
                current_title = None
                elem.clear()

        return "\n\n".join(parts)

    @staticmethod
    def _extract_generic_xml(file_path: str) -> str:
        """
        解析普通XML文件，递归提取所有文本节点内容。
        """
        try:
            tree = ET.parse(file_path)
        except ET.ParseError as e:
            raise ValueError(f"XML解析失败: {e}")

        parts = []

        def collect_text(elem):
            text = (elem.text or '').strip()
            tail = (elem.tail or '').strip()
            if text:
                parts.append(text)
            for child in elem:
                collect_text(child)
            if tail:
                parts.append(tail)

        collect_text(tree.getroot())
        return "\n".join(parts)

    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """Extract and concatenate text from multiple files. Args: file_paths. Returns concatenated text."""
        all_texts = []

        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== Document {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== Document {i}: {file_path} (extraction failed: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """Split text into chunks. Args: text, chunk_size, overlap. Returns list of chunks."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Prefer splitting at sentence boundaries
        if end < len(text):
            for sep in ['。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else len(text)
    
    return chunks

