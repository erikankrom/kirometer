import { sprites } from './animation-assets.mjs';
const { react: React } = window.__kirocrew_modules;
const {createElement:h,useEffect,useRef}=React;
const tau=2*Math.PI;
// Mirror firmware/src/ghost_motion.h. Coordinates are device pixels (480 × 480).
export function ghostPose(state,t){
  let facing=0,x=162,y=133+Math.round(Math.sin((t%4000)*tau/4000)*3),blink=t%5000>=4750;
  if(state==='Working'){
    const p=t%6000;facing=p<450?0:p<2200?1:p<3000?2:p<4750?3:0;
    x+=Math.round(Math.sin(p*tau/6000)*10);y+=Math.round(Math.sin((t%1200)*tau/1200)*5);
  }else if(state==='Needs attention'){
    const p=t%4800;facing=p<800?1:p<1600?3:0;y-=p<1600?3:0;blink=p>=3800&&p<4050;
  }else if(state==='Complete'){
    if(t<2000)facing=Math.floor(t/400)%4;
    const p=t%6000;if(p<1800)y-=Math.round(Math.abs(Math.sin(p*tau/1800))*11);
  }else if(state==='Error'){
    const p=t%5000;if(p<900){x+=Math.round(Math.sin(p*tau/300)*7);facing=Math.floor(p/300)%2?1:3;}
  }else if(state==='Ready'){
    const p=t%16000;if(p>=11000&&p<12000)facing=1;if(p>=12000&&p<13000)facing=3;
  }else facing=Math.floor(t/1600)%4;
  return {facing,x,y,blink};
}
const regions={orbit:[187,95,108,126,94,115],sidekick:[295,113,130,155,115,140],ticket:[316,88,108,130,92,112],big_number:[350,263,84,94,70,86]};
const directions=['SOUTH','EAST','NORTH','WEST'];
const images=new Map();
function load(src){if(!images.has(src))images.set(src,new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=src;}));return images.get(src);}
export function AnimatedPreview({id,src,activity='Ready',playing=true,active=true,title}){
 const canvas=useRef(null),elapsed=useRef(id==='idle'?1800:0);
 useEffect(()=>{elapsed.current=id==='idle'?1800:0;},[activity,id]);
 useEffect(()=>{
   let cancelled=false,timer,last=performance.now();
   Promise.all([src?load(src):Promise.resolve(null),...Object.values(sprites).map(load)]).then(([base,...loaded])=>{
     if(cancelled)return;
     const sheet=Object.fromEntries(Object.keys(sprites).map((k,i)=>[k,loaded[i]]));
     const ctx=canvas.current.getContext('2d');ctx.imageSmoothingEnabled=false;
     function paint(){
       const now=performance.now();if(playing&&active&&!document.hidden)elapsed.current+=Math.min(now-last,100);last=now;
       const t=Math.floor(elapsed.current/50)*50;
       ctx.fillStyle='#000';ctx.fillRect(0,0,480,480);if(base&&id!=='idle')ctx.drawImage(base,0,0,480,480);
       function ghost(facing,blink,x,y,w,hh){ctx.drawImage(sheet['GHOST_'+directions[facing]+(blink?'_BLINK':'')],Math.round(x),Math.round(y),w,hh);}
       if(id==='idle'){
         const phase=t%20000,edge=Math.floor(t/20000)%4;
         if(phase<5500){
           const reveal=Math.trunc(Math.sin(phase/5500*Math.PI)*105),sprite=sheet[t%5000>=4800?'GHOST_BLINK':'GHOST'];
           ctx.save();
           if(edge===0){ctx.translate(reveal,178);ctx.rotate(Math.PI/2);}
           if(edge===1){ctx.translate(480-reveal,301);ctx.rotate(-Math.PI/2);}
           if(edge===2)ctx.translate(178,480-reveal);
           if(edge===3){ctx.translate(301,reveal);ctx.rotate(Math.PI);}
           ctx.drawImage(sprite,0,0);ctx.restore();
         }
       }else if(id==='usage'){
         ctx.fillRect(18,8,60,66);ghost(0,t%5000>=4750,25,14+Math.round(Math.sin(t*.0015707963)*2),46,56);
       }else{
         const p=ghostPose(activity,t),r=regions[id];
         if(r){
           ctx.fillRect(...r.slice(0,4));let f=p.facing;
           if(activity==='Ready'&&f===0)f=id==='sidekick'?1:id==='ticket'?3:0;
           ghost(f,p.blink,r[0]+Math.floor((r[2]-r[4])/2),r[1]+Math.floor((r[3]-r[5])/2)+Math.round(Math.sin(t*.00157)*3),r[4],r[5]);
           if(id==='sidekick'){ctx.fillStyle='#000';ctx.fillRect(280,45,175,50);ctx.fillStyle='#c49cff';ctx.font='22px "Space Grotesk", sans-serif';ctx.fillText(activity,283,83,168);}
         }else{
           ctx.fillRect(152,118,176,234);ghost(p.facing,p.blink,p.x,p.y,156,190);
           ctx.fillStyle='#000';ctx.fillRect(12,55,456,58);ctx.fillStyle='#c49cff';ctx.font='bold 48px "Space Grotesk", sans-serif';ctx.textAlign='center';ctx.fillText(activity,240,101,450);ctx.textAlign='start';
           if(activity==='Working')for(let i=0;i<3;i++){const pulse=(Math.sin(t*.0062831853-i*2.0944)+1)*.5;ctx.fillStyle=pulse>.45?'#9147ff':'#393539';ctx.beginPath();ctx.arc(225+i*15,343,3+Math.round(pulse*2),0,tau);ctx.fill();}
         }
       }
     }
     paint();if(playing&&active)timer=setInterval(paint,50);
   }).catch(()=>{if(!cancelled&&canvas.current)canvas.current.setAttribute('aria-label',title+' — preview unavailable');});
   return()=>{cancelled=true;clearInterval(timer);};
 },[src,id,activity,playing,active,title]);
 return h('canvas',{ref:canvas,width:480,height:480,role:'img','aria-label':title+' animated preview',style:{display:'block',width:'100%',height:'auto',aspectRatio:'1',borderRadius:12,background:'#000'}});
}
