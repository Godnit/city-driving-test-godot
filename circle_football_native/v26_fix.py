from pathlib import Path

p = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = p.read_text(encoding='utf-8')
old = 'subtitle(c,"STADIUM",275*s,11,Color.rgb(145,160,180));String[] fs={"CLASSIC","GRASS","NIGHT","WIDE"};float fw=132*s,fg=9*s,ft=fw*4+fg*3,fs=(w-ft)/2f;for(int i=0;i<4;i++)menuButton(c,fs[i],"field"+i,fs+i*(fw+fg),286*s,fw,39*s,i==fieldTheme?Color.rgb(102,82,205):Color.rgb(48,56,70));'
new = 'subtitle(c,"STADIUM",275*s,11,Color.rgb(145,160,180));String[] fieldLabels={"CLASSIC","GRASS","NIGHT","WIDE"};float fw=132*s,fg=9*s,ft=fw*4+fg*3,fStart=(w-ft)/2f;for(int i=0;i<4;i++)menuButton(c,fieldLabels[i],"field"+i,fStart+i*(fw+fg),286*s,fw,39*s,i==fieldTheme?Color.rgb(102,82,205):Color.rgb(48,56,70));'
if old not in s:
    raise RuntimeError('v2.6 stadium selector segment not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Fixed v2.6 stadium selector variable names')
