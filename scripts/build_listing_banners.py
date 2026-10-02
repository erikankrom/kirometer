"""Render listing banner text as Space Grotesk paths, independent of host fonts."""
from pathlib import Path
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
fonts={name:TTFont(ROOT/f'firmware/assets/fonts/SpaceGrotesk-{name}.ttf') for name in ('Regular','Bold')}
for theme in ('light','dark'):
    tree=ET.parse(ROOT/f'scripts/artwork/banner-kiro-{theme}.svg')
    for parent in list(tree.iter()):
        for element in list(parent):
            if element.tag!=f'{{{NS}}}text':continue
            label=element.text or ''
            font=fonts['Bold' if int(element.get('font-weight','400'))>=600 else 'Regular']
            glyphs=font.getGlyphSet();cmap=font.getBestCmap()
            scale=float(element.get('font-size'))/font['head'].unitsPerEm
            spacing=float(element.get('letter-spacing','0'))/scale
            group=ET.Element(f'{{{NS}}}g',{'fill':element.get('fill'),'aria-label':label,'transform':f"translate({element.get('x','0')} {element.get('y','0')}) scale({scale} {-scale})"})
            offset=0
            for char in label:
                glyph=glyphs[cmap[ord(char)]];pen=SVGPathPen(glyphs);glyph.draw(pen)
                if pen.getCommands():ET.SubElement(group,f'{{{NS}}}path',{'d':pen.getCommands(),'transform':f'translate({offset} 0)'})
                offset+=glyph.width+spacing
            parent.insert(list(parent).index(element),group);parent.remove(element)
    tree.write(ROOT/f'crew-app/ui/art/banner-kiro-{theme}.svg',encoding='unicode')
