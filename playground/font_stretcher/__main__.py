import argparse
import os

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph


def stretch_glyph(glyph: Glyph, factor: float) -> None:
    """Stretch the given glyph vertically by the specified factor."""
    if glyph.isComposite():
        # ignore composite glyphs
        return
    else:
        # Handle simple glyphs
        coordinates, __, __ = glyph.getCoordinates(glyph)
        for i, (x, y) in enumerate(coordinates):
            coordinates[i] = (x / factor, y * factor)
        if not coordinates:  # ignore empty glyphs
            return
        glyph.xMax = max(x for x, _ in coordinates)
        glyph.yMax = max(y for _, y in coordinates)
        glyph.xMin = min(x for x, _ in coordinates)
        glyph.yMin = min(y for _, y in coordinates)
        glyph.coordinates = coordinates


def stretch_font(input_path, output_path, factor):
    # Load the font
    font = TTFont(input_path)

    # Stretch each glyph
    glyf_table = font["glyf"]
    for glyph_name in glyf_table.keys():
        glyph = glyf_table[glyph_name]
        if isinstance(glyph, Glyph):
            stretch_glyph(glyph, factor)

    # Save the modified font
    font.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Stretch glyphs in a font vertically."
    )
    parser.add_argument("input", help="Input font file (TTF/OTF)")
    parser.add_argument("output", help="Output font file (TTF/OTF)")
    parser.add_argument(
        "--factor",
        type=float,
        default=2.0,
        help="Vertical stretch factor (default: 2.0)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return

    stretch_font(args.input, args.output, args.factor)
    print(
        f"Stretched font saved as '{args.output}' with a vertical stretch factor of {args.factor}."
    )


if __name__ == "__main__":
    main()
