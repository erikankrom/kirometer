// Background-only photo preparation. Device RGB pixels are copied, never generated.
import {execFileSync} from 'node:child_process';
import {writeFileSync, copyFileSync} from 'node:fs';
import path from 'node:path';
const root=path.resolve('exports/makerworld-photos');
const work=path.join(root,'work');
const magick=(...args)=>execFileSync('/opt/homebrew/bin/magick',args,{maxBuffer:1024*1024*4});
const shots=[
 {id:'3148',name:'front',size:[5712,3213],trace:[2100,450,2],crop:[1850,460],
  outline:'M210 178 Q246 120 310 92 Q315 89 314 100 L314 142 Q515 92 752 136 L754 85 Q755 77 764 82 Q844 108 875 158 L895 207 Q930 252 936 302 L933 450 L919 677 Q914 817 882 923 Q857 1042 802 1111 Q784 1133 755 1137 L637 1137 Q599 1134 569 1100 L535 1054 Q530 1047 524 1054 L469 1102 Q444 1122 418 1129 L289 1130 Q236 1128 213 1105 Q193 1082 196 1040 L205 951 Q139 978 79 958 Q38 945 47 922 L69 819 Q90 699 128 656 L128 472 Q125 354 150 278 Q175 206 210 178 Z'},
 {id:'3149',name:'rear',size:[5712,3213],trace:[2180,800,2],crop:[1975,600],
  outline:'M57 273 C58 189 142 143 238 118 C382 80 514 69 653 72 C713 70 748 89 770 132 C789 167 822 262 849 330 C907 382 925 443 912 520 C907 573 884 623 881 651 C874 703 896 729 924 776 C943 810 922 834 884 845 C848 857 811 858 782 856 L780 883 Q778 901 761 903 Q742 905 745 881 L748 859 L608 882 L596 873 L590 856 L571 854 L558 872 L415 902 L406 937 L398 970 L247 1004 L233 1004 Q214 1004 198 979 Q175 945 160 883 L130 680 L87 464 Q67 366 57 273 Z'},
 {id:'3146',name:'three-quarter',size:[4032,2268],trace:[1360,100,5/3],crop:[900,-90],
  outline:'M144 136 L306 162 Q402 89 512 80 L509 55 Q510 50 527 53 L531 80 Q617 54 697 66 Q807 72 833 132 Q848 167 849 216 L850 337 Q863 519 866 638 Q866 823 845 898 Q827 962 800 982 L719 1015 Q698 1024 677 1016 L645 998 L621 975 Q617 969 613 980 L577 1039 Q552 1074 528 1083 L435 1114 Q409 1126 381 1111 L257 1031 Q173 983 55 898 Q23 883 27 839 Q27 808 43 762 Q92 631 75 550 Q52 442 52 327 Q49 209 108 163 Z'},
];
magick(path.join(root,'studio-backdrop.png'),'-resize','2400x2400!','-strip',path.join(work,'backdrop.png'));
for(const s of shots){
 const [w,h]=s.size, [tx,ty,scale]=s.trace, [cx,cy]=s.crop;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="100%" height="100%" fill="black"/><g transform="translate(${tx} ${ty}) scale(${scale})"><path d="${s.outline}" fill="white" stroke="white" stroke-width="3" stroke-linejoin="round"/></g></svg>`;
 writeFileSync(path.join(work,`${s.name}-mask.svg`),svg);
 magick(path.join(work,`${s.name}-mask.svg`),'-colorspace','Gray',path.join(work,`${s.name}-mask.png`));
 magick(path.join(root,`originals/IMG_${s.id}.jpeg`),'-auto-orient','-strip',path.join(work,`${s.name}-source.png`));
 magick(path.join(work,`${s.name}-source.png`),path.join(work,`${s.name}-mask.png`),'-alpha','off','-compose','CopyOpacity','-composite',path.join(work,`${s.name}-cutout.png`));
 // Position without resizing or rotating the product. Only the empty backdrop is resized.
 magick('-size','2400x2400','xc:none',path.join(work,`${s.name}-cutout.png`),'-geometry',`${-cx>=0?'+':''}${-cx}${-cy>=0?'+':''}${-cy}`,'-compose','Over','-composite',path.join(work,`${s.name}-placed.png`));
 // A subtle studio contact shadow on the replacement floor, behind the real photograph.
 const shadowY=s.name==='front'?2218:s.name==='rear'?2180:2070;
 magick('-size','2400x2400','xc:none','-fill','rgba(45,39,32,0.23)','-draw',`ellipse 1220,${shadowY} 655,42 0,360`,'-blur','0x36',path.join(work,`${s.name}-shadow.png`));
 magick(path.join(work,'backdrop.png'),path.join(work,`${s.name}-shadow.png`),'-compose','Over','-composite',path.join(work,`${s.name}-placed.png`),'-compose','Over','-composite','-strip',path.join(root,`kirometer-${s.name}-square.png`));
 // Every fully opaque foreground pixel must match the original decoded JPEG exactly.
 magick(path.join(work,`${s.name}-placed.png`),'-alpha','extract','-threshold','99.9%',path.join(work,`${s.name}-check-mask.png`));
 magick(path.join(root,`kirometer-${s.name}-square.png`),path.join(work,`${s.name}-placed.png`),'-alpha','off','-compose','Difference','-composite',path.join(work,`${s.name}-check-mask.png`),'-compose','Multiply','-composite','-format','%[fx:maxima]','info:');
 const difference=magick(path.join(root,`kirometer-${s.name}-square.png`),path.join(work,`${s.name}-placed.png`),'-alpha','off','-compose','Difference','-composite',path.join(work,`${s.name}-check-mask.png`),'-compose','Multiply','-composite','-format','%[fx:maxima]','info:').toString();
 if(Number(difference)!==0)throw new Error(`${s.name}: foreground changed ${difference}`);
 console.log(`${s.name}: 2400 x 2400; unchanged foreground verified (maximum RGB difference 0)`);
}
