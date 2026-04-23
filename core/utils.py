"""Helper utilities for Tendly Chat."""

__all__ = ["_raw", "_get_file_type_info", "_format_file_size", "_FILE_TYPE_MAP"]

from fasthtml.common import NotStr
from config.icons import (
    _ICON_DOC_PDF, _ICON_DOC_WORD, _ICON_DOC_EXCEL, _ICON_DOC_ZIP,
    _ICON_DOC_IMG, _ICON_DOC_DEFAULT,
)


def _raw(html_str):
    """Wrap a raw HTML string so FastHTML renders it unescaped.
    Used only for trusted SVG icon strings defined in this file."""
    return NotStr(html_str)


_FILE_TYPE_MAP = {
    '.pdf': ('pdf', _ICON_DOC_PDF, 'detail-doc-icon-pdf'),
    '.doc': ('doc', _ICON_DOC_WORD, 'detail-doc-icon-doc'),
    '.docx': ('docx', _ICON_DOC_WORD, 'detail-doc-icon-doc'),
    '.odt': ('odt', _ICON_DOC_WORD, 'detail-doc-icon-doc'),
    '.rtf': ('rtf', _ICON_DOC_WORD, 'detail-doc-icon-doc'),
    '.xls': ('xls', _ICON_DOC_EXCEL, 'detail-doc-icon-xls'),
    '.xlsx': ('xlsx', _ICON_DOC_EXCEL, 'detail-doc-icon-xls'),
    '.csv': ('csv', _ICON_DOC_EXCEL, 'detail-doc-icon-xls'),
    '.zip': ('zip', _ICON_DOC_ZIP, 'detail-doc-icon-zip'),
    '.rar': ('rar', _ICON_DOC_ZIP, 'detail-doc-icon-zip'),
    '.7z': ('7z', _ICON_DOC_ZIP, 'detail-doc-icon-zip'),
    '.tar': ('tar', _ICON_DOC_ZIP, 'detail-doc-icon-zip'),
    '.gz': ('gz', _ICON_DOC_ZIP, 'detail-doc-icon-zip'),
    '.png': ('png', _ICON_DOC_IMG, 'detail-doc-icon-img'),
    '.jpg': ('jpg', _ICON_DOC_IMG, 'detail-doc-icon-img'),
    '.jpeg': ('jpeg', _ICON_DOC_IMG, 'detail-doc-icon-img'),
    '.gif': ('gif', _ICON_DOC_IMG, 'detail-doc-icon-img'),
    '.svg': ('svg', _ICON_DOC_IMG, 'detail-doc-icon-img'),
    '.bmp': ('bmp', _ICON_DOC_IMG, 'detail-doc-icon-img'),
}


def _get_file_type_info(filename):
    """Return (extension_label, svg_icon, css_class) for a filename."""
    name_lower = (filename or '').lower()
    for ext, info in _FILE_TYPE_MAP.items():
        if name_lower.endswith(ext):
            return info
    return ('file', _ICON_DOC_DEFAULT, 'detail-doc-icon-default')


def _format_file_size(size_bytes):
    """Format bytes into human-readable KB/MB."""
    if not size_bytes:
        return None
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
