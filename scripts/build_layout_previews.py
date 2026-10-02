"""Build gallery previews from the official firmware atlas; illustrative credit data."""
from pathlib import Path
import base64,json,io
from fontTools import subset
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
atlas=base64.b64encode((ROOT/'previews/assets/kiro-ghost/firmware-atlas.png').read_bytes()).decode()
def ghost(x,y,w,h):
 return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 123 150"><image width="492" height="300" href="data:image/png;base64,{atlas}"/></svg>'
def text(x,y,value,size=20,color='#fff',anchor='start',weight=400):
 return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{value}</text>'
def rect(x,y,w,h,color,rx=10):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{color}"/>'
def icon(name,x,y,size=28):
 svg=(ROOT/f'crew-app/ui/art/icons/{name}.svg').read_text()
 svg=svg.replace('currentColor','#fff')
 encoded=base64.b64encode(svg.encode()).decode()
 return f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="data:image/svg+xml;base64,{encoded}"/>'
power=icon('lucide-bluetooth',278,10)+icon('lucide-battery-medium',418,8,32)+text(408,34,'85%',26,'#fff','end')

font_styles=[]
for weight,name in ((400,'Regular'),(700,'Bold')):
 font=TTFont(ROOT/f'firmware/assets/fonts/SpaceGrotesk-{name}.ttf')
 options=subset.Options();subsetter=subset.Subsetter(options=options)
 subsetter.populate(unicodes=list(range(32,127))+[0x2026]);subsetter.subset(font)
 font.flavor='woff2';buffer=io.BytesIO();font.save(buffer)
 encoded=base64.b64encode(buffer.getvalue()).decode()
 font_styles.append(f"@font-face{{font-family:Space Grotesk;font-weight:{weight};src:url(data:font/woff2;base64,{encoded}) format('woff2')}}")
font_style='<style>'+''.join(font_styles)+'</style>'
layouts=[]
for id,title,description in (
 ('ghost','Ghost companion','Activity takes center stage with directional turns, gentle floating, and blinking.'),
 ('usage','Usage dashboard','Large plan usage and reset date, with a separate red overage meter.')):
 if id=='ghost':
  body=power+'<circle cx="24" cy="24" r="5" fill="#78ecb5"/>'+text(38,32,'Connected',19)+text(240,101,'Ready',48,'#c49cff','middle',700)+ghost(162,133,156,190)
  body+=rect(30,364,150,29,'#301443',8)+text(39,385,'KIRO PRO',19,'#c49cff')+text(450,390,'126 / 1,000',30,'#fff','end',700)+rect(30,408,420,12,'#302a39',6)+rect(30,408,53,12,'#9147ff',6)+text(30,456,'874 credits left',19,'#b0adb6')
 else:
  body=power+ghost(25,14,46,56)+rect(20,80,440,42,'#211031')+text(36,115,'KIRO PRO',36,'#c49cff','start',700)
  body+=rect(20,136,440,152,'#101012',12)+text(36,170,'Plan credits',20,'#b0adb6')+text(36,210,'1,250 / 1,000',36,'#fff','start',700)+text(444,214,'125%',25,'#c49cff','end')+rect(36,234,408,14,'#29292d',7)+rect(36,234,408,14,'#9147ff',7)+text(36,281,'Resets Nov 1, 2026',20,'#b0adb6')
  body+=rect(20,302,440,132,'#101012',12)+text(36,336,'Overage credits',20,'#b0adb6')+text(36,370,'250 credits',36,'#ff607a','start',700)+rect(36,387,408,12,'#29292d',6)+rect(36,387,102,12,'#ff607a',6)+text(36,429,'25% of plan allowance',19,'#b0adb6')+'<circle cx="176" cy="459" r="5" fill="#78ecb5"/>'+text(240,470,'Connected',21,'#78ecb5','middle')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" font-family="Space Grotesk,sans-serif"><title>{title} — illustrative preview</title>{rect(0,0,480,480,"#000",0)}{font_style}{body}</svg>'
 (ROOT/f'crew-app/ui/art/layout-{id}.svg').write_text(svg)
 variants={}
 for scenario,used,overage in (('none',0,0),('normal',126,0),('overage',1250,250)):
  if id=='ghost':
   variant=svg.replace('126 / 1,000',f'{used:,} / 1,000').replace('874 credits left',f'{max(1000-used,0):,} credits left')
   variant=variant.replace('width="53"',f'width="{min(used/1000,1)*420:g}"')
  else:
   variant=svg.replace('1,250 / 1,000',f'{used:,} / 1,000').replace('125%',f'{used/10:g}%').replace('250 credits',f'{overage:,} credits').replace('25% of plan allowance',f'{overage/10:g}% of plan allowance')
   variant=variant.replace(rect(36,234,408,14,'#9147ff',7),rect(36,234,min(used/1000,1)*408,14,'#9147ff',7))
   variant=variant.replace(rect(36,387,102,12,'#ff607a',6),rect(36,387,overage/1000*408,12,'#ff607a',6))
  variants[scenario]='data:image/svg+xml;base64,'+base64.b64encode(variant.encode()).decode()
 layouts.append({'id':id,'title':title,'description':description,'preview':variants['normal'],'scenarios':variants,'minimumFirmware':'0.5.9'})

# New face thumbnails are produced from the actual firmware renderer.
for id,title,description in (
 ('orbit','Orbit','Circular plan gauge, a centered ghost, and a separate overage pill.'),
 ('sidekick','Sidekick','Large credits beside your ghost, with a shared plan meter.'),
 ('ticket','Credit ticket','A monthly credit receipt with bold numbers and a mascot stamp.'),
 ('big_number','The big number','Remaining credits at a glance; overage becomes the main number when exceeded.')):
 image=ROOT/f'crew-app/ui/art/layout-{id}.png'
 if not image.exists():raise FileNotFoundError('Run scripts/render_face_previews.py first')
 variants={name:'data:image/png;base64,'+base64.b64encode((ROOT/f'previews/firmware-faces/{id}-{number}.png').read_bytes()).decode() for name,number in (('none',3),('normal',0),('overage',1))}
 layouts.append({'id':id,'title':title,'description':description,'preview':variants['normal'],'scenarios':variants,'minimumFirmware':'0.6.0','capabilityVersion':2})
(ROOT/'crew-app/ui/layouts.mjs').write_text('// Generated by scripts/build_layout_previews.py. Each entry must have a firmware renderer.\nexport const screenLayouts = '+json.dumps(layouts,indent=2)+';\n')
