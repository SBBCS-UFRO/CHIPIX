# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline translations, including diagnostics from the host-independent core.

The source messages are retained for compatibility with existing saved logs.
Templates translate dynamic values without changing scientific data or files.
"""
import json
from pathlib import Path
import re
from string import Formatter

LANGUAGES = {"en":"English", "es":"Español", "de":"Deutsch", "fr":"Français",
             "zh":"简体中文", "ja":"日本語", "pt":"Português"}


class Translator:
    def __init__(self, language="en"):
        directory = Path(__file__).parent/"locales"
        self.catalogs = {code:json.loads((directory/f"{code}.json").read_text(encoding="utf-8"))
                         for code in LANGUAGES}
        self.language = language if language in LANGUAGES else "en"
        self.reverse = {}
        for catalog in self.catalogs.values():
            for key,value in catalog.items():
                if "{" not in key:
                    self.reverse.setdefault(value,key)
        self.patterns = []
        for key in self.catalogs["en"]:
            if "{" not in key:
                continue
            parts, fields = [],[]
            for literal,field,_,_ in Formatter().parse(key):
                parts.append(re.escape(literal))
                if field is not None:
                    parts.append("(.*?)")
                    fields.append(field)
            self.patterns.append((re.compile("^"+"".join(parts)+"$",re.DOTALL),key,fields))
        # Prefer the most specific templates over broad '{run}: ...' matches.
        self.patterns.sort(key=lambda item:len(item[1]),reverse=True)

    def __call__(self, message, _depth=0):
        message = str(message)
        catalog = self.catalogs[self.language]
        if message in catalog:
            return catalog[message]
        if message in self.reverse:
            return catalog.get(self.reverse[message],message)
        if _depth >= 8:
            return message
        for pattern,key,fields in self.patterns:
            match = pattern.fullmatch(message)
            if match:
                values = {field:self(value,_depth+1) for field,value in zip(fields,match.groups())}
                return catalog[key].format(**values)
        if " · " in message:
            return " · ".join(self(part,_depth+1) for part in message.split(" · "))
        return message
