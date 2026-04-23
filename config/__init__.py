"""Configuration package for Tendly Chat.

Contains:
  config.icons   — SVG icon strings
  config.i18n    — internationalization, translations
  config/translations/ — JSON translation files
"""

COUNTRY_FLAGS = {
    "EE": "\U0001f1ea\U0001f1ea",
    "GB": "\U0001f1ec\U0001f1e7",
    "LV": "\U0001f1f1\U0001f1fb",
    "PL": "\U0001f1f5\U0001f1f1",
    "LT": "\U0001f1f1\U0001f1f9",
    "FR": "\U0001f1eb\U0001f1f7",
}

COUNTRY_NAMES = {
    "EE": "Estonia", "GB": "United Kingdom", "LV": "Latvia",
    "PL": "Poland", "LT": "Lithuania", "FR": "France",
}

CURRENCY_SYMBOLS = {"EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142"}
