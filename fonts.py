"""Unicode "fonts" for Telegram names.

Telegram cannot use real fonts in a profile name, so every style here is a set of
Unicode look-alike characters (Mathematical Alphanumerics, fullwidth, circled, ...).
Characters a style does not cover are left unchanged.
"""
import string

UP = string.ascii_uppercase
LO = string.ascii_lowercase
DG = string.digits


def _range(start, count):
    return [chr(start + i) for i in range(count)]


def _build(upper=None, lower=None, digits=None, holes=None):
    """upper/lower/digits are the code point of the first character of each run."""
    m = {}
    if upper is not None:
        m.update(zip(UP, _range(upper, 26)))
    if lower is not None:
        m.update(zip(LO, _range(lower, 26)))
    if digits is not None:
        m.update(zip(DG, _range(digits, 10)))
    if holes:
        m.update({k: chr(v) for k, v in holes.items()})
    return m


_ITALIC_HOLES = {"h": 0x210E}
_SCRIPT_HOLES = {
    "B": 0x212C, "E": 0x2130, "F": 0x2131, "H": 0x210B, "I": 0x2110,
    "L": 0x2112, "M": 0x2133, "R": 0x211B, "e": 0x212F, "g": 0x210A, "o": 0x2134,
}
_FRAKTUR_HOLES = {"C": 0x212D, "H": 0x210C, "I": 0x2111, "R": 0x211C, "Z": 0x2128}
_DOUBLE_HOLES = {
    "C": 0x2102, "H": 0x210D, "N": 0x2115, "P": 0x2119,
    "Q": 0x211A, "R": 0x211D, "Z": 0x2124,
}

_SMALL_CAPS = dict(zip(
    LO, "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
))

_SUPERSCRIPT = dict(zip(
    "0123456789abcdefghijklmnoprstuvwxyz",
    "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ",
))

_CIRCLED = {**dict(zip(UP, _range(0x24B6, 26))), **dict(zip(LO, _range(0x24D0, 26)))}
_CIRCLED.update({"0": "⓪", **dict(zip("123456789", _range(0x2460, 9)))})

_NEG_CIRCLED = dict(zip(UP, _range(0x1F150, 26)))
_NEG_CIRCLED.update(dict(zip(LO, _range(0x1F150, 26))))
_NEG_CIRCLED.update({"0": "⓿", **dict(zip("123456789", _range(0x2776, 9)))})

_SQUARED = dict(zip(UP, _range(0x1F130, 26)))
_SQUARED.update(dict(zip(LO, _range(0x1F130, 26))))

_FULLWIDTH = _build(0xFF21, 0xFF41, 0xFF10)

PERSIAN_DIGITS = dict(zip(DG, "۰۱۲۳۴۵۶۷۸۹"))
ARABIC_DIGITS = dict(zip(DG, "٠١٢٣٤٥٦٧٨٩"))

FONTS = {
    "normal": {},
    "bold": _build(0x1D400, 0x1D41A, 0x1D7CE),
    "italic": _build(0x1D434, 0x1D44E, None, _ITALIC_HOLES),
    "bold_italic": _build(0x1D468, 0x1D482),
    "script": _build(0x1D49C, 0x1D4B6, None, _SCRIPT_HOLES),
    "bold_script": _build(0x1D4D0, 0x1D4EA),
    "fraktur": _build(0x1D504, 0x1D51E, None, _FRAKTUR_HOLES),
    "bold_fraktur": _build(0x1D56C, 0x1D586),
    "double_struck": _build(0x1D538, 0x1D552, 0x1D7D8, _DOUBLE_HOLES),
    "sans": _build(0x1D5A0, 0x1D5BA, 0x1D7E2),
    "sans_bold": _build(0x1D5D4, 0x1D5EE, 0x1D7EC),
    "sans_italic": _build(0x1D608, 0x1D622),
    "sans_bold_italic": _build(0x1D63C, 0x1D656),
    "monospace": _build(0x1D670, 0x1D68A, 0x1D7F6),
    "fullwidth": _FULLWIDTH,
    "circled": _CIRCLED,
    "negative_circled": _NEG_CIRCLED,
    "squared": _SQUARED,
    "small_caps": {**_SMALL_CAPS, **{u: _SMALL_CAPS[u.lower()] for u in UP}},
    "superscript": {**_SUPERSCRIPT, **{u: _SUPERSCRIPT[u.lower()] for u in UP if u.lower() in _SUPERSCRIPT}},
    "persian_digits": PERSIAN_DIGITS,
    "arabic_digits": ARABIC_DIGITS,
}

# Python's str.translate wants code points as keys.
_TABLES = {name: {ord(k): v for k, v in m.items()} for name, m in FONTS.items()}


def available():
    return list(FONTS)


def apply(text, font):
    """Convert text to the given style. Unknown style names return the text unchanged."""
    table = _TABLES.get(font)
    if not table:
        return text
    return text.translate(table)


if __name__ == "__main__":
    sample = "Reza | 09:41 0123456789"
    for name in FONTS:
        print(f"{name:18} {apply(sample, name)}")
