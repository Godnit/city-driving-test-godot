from pathlib import Path
import re

path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
s = path.read_text(encoding='utf-8')


def replace_method(text, name, replacement):
    pattern = (r'(?m)^        (?:@Override\s+)?(?:(?:public|protected|private)\s+)?'
               r'(?:static\s+)?(?:void|float(?:\[\])?|int|boolean|short\[\]|String|MediaPlayer|Disc)\s+'
               + re.escape(name) + r'\s*\(')
    m = re.search(pattern, text)
    if not m:
        raise RuntimeError('method declaration not found: ' + name)
    start = m.start()
    brace = text.find('{', m.end())
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[:start] + replacement.rstrip() + text[i+1:]
    raise RuntimeError('unterminated method: ' + name)

# IMPORTANT: gameplay/AI/ball physics stay exactly on the v2.2 stack.
# This patch restores only stadium choices, compact setup UI and modern visual scale.
if 'fieldTheme=0' not in s:
    s = s.replace('int difficulty=1, teamSize=2, targetGoals=5;',
                  'int difficulty=1, teamSize=2, targetGoals=5, fieldTheme=0;', 1)
if 'prefs.getInt("field_theme"' not in s:
    s = s.replace('targetGoals=prefs.getInt("target_goals",5);',
                  'targetGoals=prefs.getInt("target_goals",5);\n            fieldTheme=clampInt(prefs.getInt("field_theme",0),0,4);', 1)

# Same modern sizes/stadium spacing as the later visual versions.
configure = r'''        void configureField(){
            float mxRatio,myRatio;
            if(fieldTheme==4){mxRatio=.040f;myRatio=.070f;}
            else if(fieldTheme==3){mxRatio=.052f;myRatio=.078f;}
            else if(fieldTheme==2){mxRatio=.064f;myRatio=.104f;}
            else{mxRatio=teamSize>=3?.058f:.073f;myRatio=teamSize>=3?.098f:.116f;}
            float mx=Math.max(w*mxRatio,42f*s),my=h*myRatio;
            pitch.set(mx,my,w-mx,h-my);
            goalHalf=pitch.height()*(fieldTheme==4?.195f:.210f);
            if(fieldTheme==4){
                float ts=teamSize>=4?.88f:(teamSize==3?.94f:1f);
                discR=18.4f*s*ts;
                ballR=6.6f*s*(teamSize>=4?.91f:(teamSize==3?.95f:1f));
            }else{
                float ts=teamSize>=4?.83f:(teamSize==3?.90f:1f),fs=fieldTheme==3?.92f:(fieldTheme==2?.96f:1f);
                discR=20.2f*s*ts*fs;
                float bt=teamSize>=4?.86f:(teamSize==3?.92f:1f),bf=fieldTheme==3?.90f:(fieldTheme==2?.95f:1f);
                ballR=8.8f*s*bt*bf;
            }
        }'''
s = replace_method(s, 'configureField', configure)

helpers = r'''        String fieldNameV33(){return fieldTheme==0?"CLASSIC":fieldTheme==1?"GRASS":fieldTheme==2?"NIGHT":fieldTheme==3?"WIDE":"VIDEO";}
        String difficultyNameV33(){return difficulty==0?"EASY":difficulty==1?"NORMAL":"HARD";}

        void selectorRowV33(Canvas c,String label,String value,float x,float y,float ww,String leftId,String rightId,int accent){
            float hh=50*s;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(37,43,53));c.drawRoundRect(new RectF(x,y,x+ww,y+hh),13*s,13*s,p);
            p.setTextAlign(Paint.Align.LEFT);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(12*s);p.setColor(Color.rgb(151,166,187));
            c.drawText(label,x+17*s,y+30*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTextSize(17*s);p.setColor(Color.WHITE);
            c.drawText(value,x+ww*.67f,y+31*s,p);
            p.setTextSize(27*s);p.setColor(Color.rgb(200,210,225));
            c.drawText("‹",x+ww-82*s,y+33*s,p);c.drawText("›",x+ww-27*s,y+33*s,p);
            hits.add(new ButtonHit(leftId,new RectF(x+ww-108*s,y,x+ww-55*s,y+hh)));
            hits.add(new ButtonHit(rightId,new RectF(x+ww-54*s,y,x+ww,y+hh)));
            p.setColor(accent);c.drawRoundRect(new RectF(x+ww*.48f,y+hh-3*s,x+ww*.84f,y+hh),2*s,2*s,p);
        }

        void drawFieldPreviewV33(Canvas c,RectF r){
            int outside,a,b,line;
            if(fieldTheme==1){outside=Color.rgb(31,103,37);a=Color.rgb(54,156,56);b=Color.rgb(47,143,50);line=Color.WHITE;}
            else if(fieldTheme==2){outside=Color.rgb(10,22,38);a=Color.rgb(31,57,84);b=Color.rgb(26,48,73);line=Color.rgb(218,234,246);}
            else if(fieldTheme==3){outside=Color.rgb(35,112,42);a=Color.rgb(61,155,65);b=Color.rgb(51,139,57);line=Color.WHITE;}
            else if(fieldTheme==4){outside=Color.rgb(42,42,44);a=Color.rgb(78,78,79);b=Color.rgb(70,70,72);line=Color.WHITE;}
            else{outside=Color.rgb(48,52,56);a=Color.rgb(68,73,78);b=Color.rgb(61,66,71);line=Color.WHITE;}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(28,33,41));c.drawRoundRect(r,16*s,16*s,p);
            RectF f=new RectF(r.left+15*s,r.top+32*s,r.right-15*s,r.bottom-15*s);
            p.setColor(outside);c.drawRoundRect(f,9*s,9*s,p);
            RectF q=new RectF(f.left+9*s,f.top+9*s,f.right-9*s,f.bottom-9*s);
            int bands=fieldTheme==4?9:8;
            for(int i=0;i<bands;i++){p.setColor(i%2==0?a:b);float xx=q.left+q.width()*i/bands;c.drawRect(xx,q.top,xx+q.width()/bands,q.bottom,p);}
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(1.3f*s);stroke.setColor(line);
            c.drawRect(q,stroke);c.drawLine(q.centerX(),q.top,q.centerX(),q.bottom,stroke);c.drawCircle(q.centerX(),q.centerY(),q.height()*.17f,stroke);
            float ar=q.height()*.34f;c.drawArc(new RectF(q.left-ar,q.centerY()-ar,q.left+ar,q.centerY()+ar),-90,180,false,stroke);c.drawArc(new RectF(q.right-ar,q.centerY()-ar,q.right+ar,q.centerY()+ar),90,180,false,stroke);
            float gh=q.height()*.20f,gd=10*s;c.drawRoundRect(new RectF(q.left-gd,q.centerY()-gh,q.left,q.centerY()+gh),3*s,3*s,stroke);c.drawRoundRect(new RectF(q.right,q.centerY()-gh,q.right+gd,q.centerY()+gh),3*s,3*s,stroke);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(14*s);p.setColor(Color.WHITE);c.drawText(fieldNameV33(),r.centerX(),r.top+21*s,p);
        }

        void drawHumanGuideV33(Canvas c){
            Disc d=blue[0];float db=dist(d.x,d.y,bx,by);if(db>kickReach()+25*s)return;
            float dx=bx-d.x,dy=by-d.y,l=len(dx,dy);if(l<1){dx=1;dy=0;l=1;}
            float vx=dx/l,vy=dy/l,bs=len(bvx,bvy);
            if(bs>28*s){vx=vx*.92f+(bvx/bs)*.08f;vy=vy*.92f+(bvy/bs)*.08f;float vl=len(vx,vy);if(vl>0){vx/=vl;vy/=vl;}}
            float maxLen=Math.min(goalHalf*1.18f,112*s),step=13*s,travel=0,px=bx,py=by;
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            p.setStyle(Paint.Style.FILL);
            int n=0;
            while(travel<maxLen&&n<14){
                px+=vx*step;py+=vy*step;travel+=step;n++;
                if(py-ballR<pitch.top){py=pitch.top+ballR;vy=Math.abs(vy);}
                if(py+ballR>pitch.bottom){py=pitch.bottom-ballR;vy=-Math.abs(vy);}
                boolean mouth=py>y1+ballR*.2f&&py<y2-ballR*.2f;
                if(!mouth){if(px-ballR<pitch.left){px=pitch.left+ballR;vx=Math.abs(vx);}if(px+ballR>pitch.right){px=pitch.right-ballR;vx=-Math.abs(vx);}}
                if(n%2==0){int alpha=Math.max(16,54-n*2);p.setColor(Color.argb(alpha,255,255,255));c.drawCircle(px,py,2.0f*s,p);}
            }
        }
'''
if 'String fieldNameV33()' not in s:
    marker='        void drawSetup(Canvas c){'
    if marker not in s: raise RuntimeError('drawSetup marker missing')
    s=s.replace(marker,helpers+'\n'+marker,1)

setup = r'''        void drawSetup(Canvas c){
            background(c);title(c,"PLAY MATCH",44*s,28);
            float cardW=Math.min(760*s,w*.76f),cardH=Math.min(560*s,h-86*s),x=(w-cardW)/2f,y=68*s;
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(27,32,40));c.drawRoundRect(new RectF(x,y,x+cardW,y+cardH),20*s,20*s,p);
            float leftW=Math.min(330*s,cardW*.46f),lx=x+24*s,top=y+34*s;
            int dL=(difficulty+2)%3,dR=(difficulty+1)%3;
            int tL=teamSize==1?4:teamSize-1,tR=teamSize==4?1:teamSize+1;
            int[] gs={3,5,7};int gi=targetGoals==3?0:targetGoals==5?1:2,gL=gs[(gi+2)%3],gR=gs[(gi+1)%3];
            selectorRowV33(c,"DIFFICULTY",difficultyNameV33(),lx,top,leftW,"diff"+dL,"diff"+dR,Color.rgb(52,132,255));
            selectorRowV33(c,"PLAYERS",teamSize+"v"+teamSize,lx,top+64*s,leftW,"team"+tL,"team"+tR,Color.rgb(44,188,104));
            selectorRowV33(c,"GOALS",""+targetGoals,lx,top+128*s,leftW,"goal"+gL,"goal"+gR,Color.rgb(242,164,40));
            int fL=(fieldTheme+4)%5,fR=(fieldTheme+1)%5;
            float previewSize=Math.min(235*s,cardW-leftW-86*s),px=x+cardW-previewSize-34*s,py=y+47*s;
            drawFieldPreviewV33(c,new RectF(px,py,px+previewSize,py+previewSize));
            RectF prev=new RectF(px-52*s,py+previewSize*.40f,px-8*s,py+previewSize*.62f),next=new RectF(px+previewSize+8*s,py+previewSize*.40f,px+previewSize+52*s,py+previewSize*.62f);
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(45,52,64));c.drawRoundRect(prev,10*s,10*s,p);c.drawRoundRect(next,10*s,10*s,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(27*s);p.setColor(Color.WHITE);c.drawText("‹",prev.centerX(),prev.centerY()+9*s,p);c.drawText("›",next.centerX(),next.centerY()+9*s,p);
            hits.add(new ButtonHit("field"+fL,prev));hits.add(new ButtonHit("field"+fR,next));
            subtitle(c,"STADIUM",py+previewSize+27*s,12,Color.rgb(145,160,180));
            float startY=y+cardH-72*s;menuButton(c,"START MATCH","start",x+cardW*.20f,startY,cardW*.60f,48*s,Color.rgb(29,121,255));
            RectF back=new RectF(18*s,18*s,102*s,54*s);p.setColor(Color.rgb(47,54,66));c.drawRoundRect(back,10*s,10*s,p);p.setTextSize(13*s);p.setColor(Color.WHITE);p.setTextAlign(Paint.Align.CENTER);c.drawText("BACK",back.centerX(),back.centerY()+5*s,p);hits.add(new ButtonHit("home",back));
        }'''
s = replace_method(s, 'drawSetup', setup)

draw_game = r'''        void drawGame(Canvas c){
            int outside,a,b,line;
            if(fieldTheme==1){outside=Color.rgb(38,119,43);a=Color.rgb(54,156,56);b=Color.rgb(48,145,51);line=Color.rgb(244,247,242);}
            else if(fieldTheme==2){outside=Color.rgb(16,32,50);a=Color.rgb(31,57,84);b=Color.rgb(27,50,76);line=Color.rgb(215,232,246);}
            else if(fieldTheme==3){outside=Color.rgb(42,122,47);a=Color.rgb(60,153,64);b=Color.rgb(51,139,57);line=Color.rgb(244,247,242);}
            else if(fieldTheme==4){outside=Color.rgb(45,45,47);a=Color.rgb(76,76,78);b=Color.rgb(69,69,71);line=Color.WHITE;}
            else{outside=Color.rgb(52,56,60);a=Color.rgb(68,73,78);b=Color.rgb(61,66,71);line=Color.WHITE;}
            c.drawColor(outside);p.setStyle(Paint.Style.FILL);p.setColor(a);c.drawRect(pitch,p);
            int bands=fieldTheme==4?9:(fieldTheme==3?12:10);
            for(int i=0;i<bands;i++){p.setColor(i%2==0?a:b);float xx=pitch.left+pitch.width()*i/bands;c.drawRect(xx,pitch.top,xx+pitch.width()/bands,pitch.bottom,p);}
            if(fieldTheme==1||fieldTheme==3){p.setColor(Color.argb(15,255,255,255));for(int i=0;i<7;i++)c.drawRect(pitch.left,pitch.top+i*pitch.height()/7f,pitch.right,pitch.top+(i+.11f)*pitch.height()/7f,p);}
            stroke.setStyle(Paint.Style.STROKE);stroke.setColor(line);stroke.setStrokeWidth(3*s);c.drawRect(pitch,stroke);c.drawLine(pitch.centerX(),pitch.top,pitch.centerX(),pitch.bottom,stroke);
            c.drawCircle(pitch.centerX(),pitch.centerY(),Math.min(74*s,pitch.height()*.14f),stroke);c.drawCircle(pitch.centerX(),pitch.centerY(),3.5f*s,stroke);
            float areaR=Math.min(pitch.height()*.34f,pitch.width()*.19f);c.drawArc(new RectF(pitch.left-areaR,pitch.centerY()-areaR,pitch.left+areaR,pitch.centerY()+areaR),-90f,180f,false,stroke);c.drawArc(new RectF(pitch.right-areaR,pitch.centerY()-areaR,pitch.right+areaR,pitch.centerY()+areaR),90f,180f,false,stroke);
            drawGoals(c);drawHumanGuideV33(c);drawParticles(c);
            for(int i=0;i<teamSize;i++)drawDisc(c,blue[i]);for(int i=0;i<teamSize;i++)drawDisc(c,red[i]);
            drawFootball(c,bx,by,ballR,ballAngle);drawScoreHud(c);drawJoystick(c,false);drawKick(c,false);
        }'''
s = replace_method(s, 'drawGame', draw_game)

draw_goals = r'''        void drawGoals(Canvas c){
            float y1=pitch.centerY()-goalHalf,y2=pitch.centerY()+goalHalf;
            float available=Math.max(25*s,pitch.left-10*s),depth=Math.min(56*s,available),curve=Math.min(14*s,(y2-y1)*.12f);
            int frame=fieldTheme==2?Color.rgb(197,223,239):Color.rgb(246,247,245),net=fieldTheme==2?Color.argb(105,148,184,207):Color.argb(92,190,198,202);
            stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(3*s);stroke.setColor(frame);
            path.reset();path.moveTo(pitch.left,y1);path.lineTo(pitch.left-depth*.62f,y1);path.quadTo(pitch.left-depth,y1,pitch.left-depth,y1+curve);path.lineTo(pitch.left-depth,y2-curve);path.quadTo(pitch.left-depth,y2,pitch.left-depth*.62f,y2);path.lineTo(pitch.left,y2);c.drawPath(path,stroke);
            path.reset();path.moveTo(pitch.right,y1);path.lineTo(pitch.right+depth*.62f,y1);path.quadTo(pitch.right+depth,y1,pitch.right+depth,y1+curve);path.lineTo(pitch.right+depth,y2-curve);path.quadTo(pitch.right+depth,y2,pitch.right+depth*.62f,y2);path.lineTo(pitch.right,y2);c.drawPath(path,stroke);
            stroke.setStrokeWidth(1*s);stroke.setColor(net);for(int i=1;i<4;i++){float yy=y1+(y2-y1)*i/4f;c.drawLine(pitch.left-depth*.94f,yy,pitch.left,yy,stroke);c.drawLine(pitch.right,yy,pitch.right+depth*.94f,yy,stroke);}for(int i=1;i<3;i++){float t=i/3f,lx=pitch.left-depth*(1f-t),rx=pitch.right+depth*(1f-t);c.drawLine(lx,y1+curve*.25f,lx,y2-curve*.25f,stroke);c.drawLine(rx,y1+curve*.25f,rx,y2-curve*.25f,stroke);}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(19,21,23));c.drawCircle(pitch.left,y1,5.7f*s,p);c.drawCircle(pitch.left,y2,5.7f*s,p);c.drawCircle(pitch.right,y1,5.7f*s,p);c.drawCircle(pitch.right,y2,5.7f*s,p);p.setColor(frame);c.drawCircle(pitch.left,y1,4*s,p);c.drawCircle(pitch.left,y2,4*s,p);c.drawCircle(pitch.right,y1,4*s,p);c.drawCircle(pitch.right,y2,4*s,p);
        }'''
s = replace_method(s, 'drawGoals', draw_goals)

draw_disc = r'''        void drawDisc(Canvas c,Disc d){
            int col=d.team==0?Color.rgb(35,103,235):Color.rgb(239,57,61);
            if(d==blue[0]){stroke.setStyle(Paint.Style.STROKE);stroke.setColor(Color.argb(48,255,255,255));stroke.setStrokeWidth(1.5f*s);c.drawCircle(d.x,d.y,discR+4.5f*s,stroke);}
            p.setStyle(Paint.Style.FILL);p.setColor(Color.BLACK);c.drawCircle(d.x,d.y,discR+2.5f*s,p);p.setColor(col);c.drawCircle(d.x,d.y,discR,p);p.setColor(Color.argb(76,255,255,255));c.drawCircle(d.x-discR*.28f,d.y-discR*.30f,discR*.20f,p);
            p.setTextAlign(Paint.Align.CENTER);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(10.5f*s);p.setColor(Color.WHITE);c.drawText(d.name,d.x,d.y+discR+14*s,p);
        }'''
s = replace_method(s, 'drawDisc', draw_disc)

# Add stadium selection without touching gameplay decisions.
needle='            if(id.equals("sounds")){'
if 'id.startsWith("field")' not in s:
    if needle not in s: raise RuntimeError('click insertion point missing')
    s=s.replace(needle,'            if(id.startsWith("field")){fieldTheme=clampInt(Integer.parseInt(id.substring(5)),0,4);prefs.edit().putInt("field_theme",fieldTheme).apply();playSfx(SFX_MENU);return;}\n'+needle,1)

# Recompute geometry only when a new match starts; movement/AI methods remain untouched.
s=s.replace('prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).apply();',
            'prefs.edit().putInt("difficulty",difficulty).putInt("team_size",teamSize).putInt("target_goals",targetGoals).putInt("field_theme",fieldTheme).apply();',1)
s=s.replace('            resetPositions();playSfx(SFX_MENU);','            configureField();resetPositions();playSfx(SFX_MENU);',1)

# Separate identity for side-by-side testing.
s=s.replace('circle_football_v22','circle_football_v33')
path.write_text(s,encoding='utf-8')

m=Path('AndroidManifest.xml');x=m.read_text(encoding='utf-8');x=x.replace('com.godnit.circlefootballlite.v22','com.godnit.circlefootballlite.v33');x=re.sub(r'android:versionCode="\d+"','android:versionCode="23"',x,count=1);x=re.sub(r'android:versionName="[^"]+"','android:versionName="3.3.0"',x,count=1);m.write_text(x,encoding='utf-8')
print('Applied v3.3 modern stadium visuals on exact v2.2 gameplay')
