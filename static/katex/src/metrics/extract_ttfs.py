#!/usr/bin/env python3

from fontTools.ttLib import TTFont
import sys
import json

# map of characters to extract
metrics_to_extract = {
    # Font name
    "AMS-Regular": {
        "\u21e2": None,  # \dashrightarrow
        "\u21e0": None,  # \dashleftarrow
    },
    "Main-Regular": {
        # Skew and italic metrics can't be easily parsed from the TTF. Instead,
        # we map each character to a "base character", which is a character
        # from the same font with correct italic and skew metrics. A character
        # maps to None if it doesn't have a base.
        # u"\u2209": None,  # \notin
        # u"\u2260": None,  # \neq
        "\u2245": None,  # \cong
        "\u2026": None,  # \ldots
        "\u22ef": None,  # \cdots
        "\u22f1": None,  # \ddots
        "\u22ee": None,  # \vdots
        "\u22ee": None,  # \vdots
        "\u22a8": None,  # \models
        "\u22c8": None,  # \bowtie
        "\u2250": None,  # \doteq
        "\u23b0": None,  # \lmoustache
        "\u23b1": None,  # \rmoustache
        "\u27ee": None,  # \lgroup
        "\u27ef": None,  # \rgroup
        "\u27f5": None,  # \longleftarrow
        "\u27f8": None,  # \Longleftarrow
        "\u27f6": None,  # \longrightarrow
        "\u27f9": None,  # \Longrightarrow
        "\u27f7": None,  # \longleftrightarrow
        "\u27fa": None,  # \Longleftrightarrow
        "\u21a6": None,  # \mapsto
        "\u27fc": None,  # \longmapsto
        "\u21a9": None,  # \hookleftarrow
        "\u21aa": None,  # \hookrightarrow
        "\u21cc": None,  # \rightleftharpoons
    },
    "Main-Bold": {
        "\u2245": None,  # \cong
    },
    "Size1-Regular": {
        "\u222c": "\u222b",  # \iint, based on \int
        "\u222d": "\u222b",  # \iiint, based on \int
    },
    "Size2-Regular": {
        "\u222c": "\u222b",  # \iint, based on \int
        "\u222d": "\u222b",  # \iiint, based on \int
    },
}


def main():
    start_json = json.load(sys.stdin)

    for font in start_json:
        fontInfo = TTFont("../../fonts/KaTeX_" + font + ".ttf")
        glyf = fontInfo["glyf"]
        widths = fontInfo.getGlyphSet()
        unitsPerEm = float(fontInfo["head"].unitsPerEm)

        # We keep ALL Unicode cmaps, not just fontInfo["cmap"].getcmap(3, 1).
        # This is playing it extra safe, since it reports inconsistencies.
        # Platform 0 is Unicode, platform 3 is Windows. For platform 3,
        # encoding 1 is UCS-2 and encoding 10 is UCS-4.
        cmap = [
            t.cmap
            for t in fontInfo["cmap"].tables
            if (t.platformID == 0) or (t.platformID == 3 and t.platEncID in (1, 10))
        ]

        chars = metrics_to_extract.get(font, {})
        chars["\u0020"] = None  # space
        chars["\u00a0"] = None  # nbsp

        for char, base_char in chars.items():
            code = ord(char)
            names = set(t.get(code) for t in cmap)
            if not names:
                sys.stderr.write(
                    "Codepoint {} of font {} maps to no name\n".format(code, font)
                )
                continue
            if len(names) != 1:
                sys.stderr.write(
                    "Codepoint {} of font {} maps to multiple names: {}\n".format(
                        code, font, ", ".join(sorted(names))
                    )
                )
                continue
            name = names.pop()

            height = depth = italic = skew = width = 0
            glyph = glyf[name]
            if glyph.numberOfContours:
                height = glyph.yMax / unitsPerEm
                depth = -glyph.yMin / unitsPerEm
            width = widths[name].width / unitsPerEm
            if base_char:
                base_char_str = str(ord(base_char))
                base_metrics = start_json[font][base_char_str]
                italic = base_metrics["italic"]
                skew = base_metrics["skew"]
                width = base_metrics["width"]

            start_json[font][str(code)] = {
                "height": height,
                "depth": depth,
                "italic": italic,
                "skew": skew,
                "width": width,
            }

    sys.stdout.write(json.dumps(start_json, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
