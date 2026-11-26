import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const RUNTIME_NODE_MODULES='C:\\Program Files\\WindowsApps\\OpenAI.CodexPrimaryRuntime.v26-1123-915-0_26.1123.915.0_x64__3k8sg7r9htsxt\\dependencies\\node\\node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(RUNTIME_NODE_MODULES,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);

const W=1280, H=720;
const C={red:'#E4002B', redDark:'#B50024', pink:'#FFF1F4', navy:'#202844', blue:'#4966F5', green:'#00A878', ink:'#20232C', muted:'#687080', pale:'#F5F6F8', line:'#E2E5EA', white:'#FFFFFF', lightBlue:'#EEF1FF'};
const FONT='Aptos';
process.env.RUNTIME_NODE_MODULES=RUNTIME_NODE_MODULES; process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES=RUNTIME_NODE_MODULES;
const workspaceDir=process.cwd();
const buildDir=path.join(workspaceDir,'ppt_build');
const outputDir=path.join(workspaceDir,'reports','presentations');
const finalPath=path.join(outputDir,'Airtel_Revenue_Story_Final.pptx');
await fs.mkdir(buildDir,{recursive:true}); await fs.mkdir(outputDir,{recursive:true});
const p=Presentation.create({slideSize:{width:W,height:H}});

function shape(slide,geom,x,y,w,h,fill='none',stroke='none',sw=0){return slide.shapes.add({geometry:geom,position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:stroke,width:sw}})}
function txt(slide,text,x,y,w,h,size=20,color=C.ink,bold=false,align='left',opts={}){
 const s=shape(slide,'textbox',x,y,w,h,'none','none',0); s.text=text;
 s.text.style={fontSize:`${size}pt`,fontFamily:FONT,typeface:FONT,color,bold,alignment:align,verticalAlignment:opts.valign||'middle',wrap:true}; return s;
}
function rule(slide,x,y,w,color=C.red,h=5){shape(slide,'rect',x,y,w,h,color,'none',0)}
function base(title, kicker, idx, subtitle=''){
 const s=p.slides.add(); s.background.fill=C.white;
 rule(s,0,0,W,C.red,10);
 txt(s,kicker.toUpperCase(),72,38,700,20,11,C.red,true);
 txt(s,title,72,72,1120,58,32,C.navy,true);
 if(subtitle) txt(s,subtitle,72,134,1120,35,17,C.muted,false);
 shape(s,'line',72,672,1136,1,'none',C.line,1);
 txt(s,'Airtel Telecom Analytics  •  Jan–Jun 2025',72,680,780,20,10,C.muted,false);
 txt(s,String(idx).padStart(2,'0'),1154,678,55,22,11,C.red,true,'right');
 return s;
}
function note(slide,text,x,y,w,h=44){txt(slide,text,x,y,w,h,15,C.muted,false);}
function chart(slide,type,config){return slide.charts.add(type,config)}

// 1. Cover
{
 const s=p.slides.add(); s.background.fill=C.white;
 shape(s,'rect',0,0,24,H,C.red);
 txt(s,'AIRTEL  /  TELECOM ANALYTICS',76,66,760,24,13,C.red,true);
 txt(s,'Revenue\nperformance',76,175,780,150,46,C.navy,true);
 txt(s,'A clear story from two dashboard views',80,350,780,44,23,C.muted,false);
 shape(s,'line',80,430,140,4,'none',C.red,4);
 txt(s,'January–June 2025',80,462,400,32,18,C.ink,true);
 txt(s,'Revenue Overview  +  Revenue Detail',80,505,650,30,17,C.muted,false);
 txt(s,'Group 2  |  Domain B',80,625,450,26,13,C.muted,false);
 txt(s,'AIRTEL',1015,590,190,56,34,C.red,true,'right');
}

// 2. Two dashboard views
{
 const s=base('Two views, one revenue story','Start here',2,'The first dashboard gives the full picture. The second lets us look closer at one plan.');
 const img1='C:\\Users\\saali\\Pictures\\Screenshots\\Screenshot 2026-11-26 211317.png';
 const img2='C:\\Users\\saali\\Pictures\\Screenshots\\Screenshot 2026-11-26 211307.png';
 s.images.add({blob:new Uint8Array(await fs.readFile(img1)),contentType:'image/png',alt:'Revenue Overview dashboard',fit:'contain',position:{left:72,top:206,width:535,height:282}});
 s.images.add({blob:new Uint8Array(await fs.readFile(img2)),contentType:'image/png',alt:'Revenue Detail dashboard',fit:'contain',position:{left:673,top:206,width:535,height:282}});
 txt(s,'01  Revenue Overview',72,500,520,30,20,C.navy,true);
 txt(s,'Total revenue, ARPU gaps, revenue mix and subscriber deciles.',72,535,520,52,16,C.muted,false);
 txt(s,'02  Revenue Detail',673,500,520,30,20,C.navy,true);
 txt(s,'One plan at a time: monthly trend, connection mix and payments.',673,535,520,52,16,C.muted,false);
 note(s,'Dashboard period: 1 Jan–27 Jun 2025  |  22,000 subscribers in the overall selection',72,612,1100,34);
}

// 3. Headline revenue
{
 const s=base('₹45.47 million received during the period','The overall picture',3,'The overview dashboard covers January through June 2025.');
 txt(s,'₹45.47M',72,205,570,100,54,C.red,true);
 txt(s,'Total received revenue',76,305,560,34,20,C.navy,true);
 txt(s,'This is recharge and payment received, not billed revenue.',76,347,525,58,17,C.muted,false);
 shape(s,'line',660,205,1,320,'none',C.line,1);
 txt(s,'₹344.46',710,224,390,70,38,C.navy,true);
 txt(s,'Average monthly revenue per subscriber',713,294,430,58,18,C.ink,false);
 txt(s,'22,000',710,410,390,68,38,C.navy,true);
 txt(s,'Subscribers in the overall selection',713,479,430,38,18,C.ink,false);
 note(s,'The dashboard labels received revenue as recharge/payment value.',72,600,1050,38);
}

// 4. Revenue and subscriber share
{
 const s=base('Postpaid earns more revenue from a smaller base','Connection mix',4,'Compare each connection type’s revenue share with its subscriber share.');
 chart(s,'bar',{position:{left:92,top:205,width:730,height:380},categories:['Postpaid','Prepaid'],series:[
  {name:'Revenue share (%)',values:[62.1,37.9],fill:C.red},
  {name:'Subscriber share (%)',values:[22.1,77.9],fill:C.blue}],
  hasLegend:true,legend:{position:'bottom',textStyle:{typeface:FONT,fontSize:14}},
  barOptions:{direction:'column',grouping:'clustered',gapWidth:90},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0"%"',textStyle:{typeface:FONT,fontSize:14,bold:true}},
  yAxis:{min:0,max:100,majorUnit:20,numberFormatCode:'0"%"',textStyle:{typeface:FONT,fontSize:12},majorGridlines:{style:'solid',fill:C.line,width:1}},
  xAxis:{textStyle:{typeface:FONT,fontSize:14}},chartFill:C.white,plotAreaFill:C.white});
 txt(s,'62.1%',888,238,300,65,34,C.red,true);
 txt(s,'of revenue comes from Postpaid',888,296,295,52,18,C.ink,false);
 txt(s,'22.1%',888,400,300,65,34,C.blue,true);
 txt(s,'of subscribers are Postpaid',888,458,295,52,18,C.ink,false);
 note(s,'Prepaid is 78% of subscribers and contributes 37.9% of revenue.',888,548,300,70);
}

// 5. ARPU gap
{
 const s=base('A few prepaid plans sit well below stated ARPU','Plan performance',5,'The overview compares received ARPU with each plan’s stated ARPU.');
 chart(s,'bar',{position:{left:86,top:208,width:760,height:390},categories:['Quarterly 719','Annual 1799','Entertainment 399','Max 479'],series:[{name:'Below stated ARPU (₹)',values:[140,132,114,105],fill:C.red}],
  hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:65},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'₹#,##0',textStyle:{typeface:FONT,fontSize:14,bold:true}},
  xAxis:{min:0,max:160,majorUnit:40,numberFormatCode:'₹#,##0',textStyle:{typeface:FONT,fontSize:12},majorGridlines:{style:'solid',fill:C.line,width:1}},
  yAxis:{textStyle:{typeface:FONT,fontSize:13}},chartFill:C.white,plotAreaFill:C.white});
 txt(s,'₹140',905,245,260,55,30,C.red,true);
 txt(s,'Largest shortfall',905,295,260,33,18,C.navy,true);
 txt(s,'Prepaid Quarterly 719',905,331,270,42,17,C.ink,false);
 shape(s,'line',905,398,220,1,'none',C.line,1);
 txt(s,'₹9',905,430,260,55,30,C.green,true);
 txt(s,'Smallest gap highlighted',905,480,280,34,18,C.navy,true);
 txt(s,'Postpaid Infinity 1499',905,518,275,42,17,C.ink,false);
 note(s,'The chart shows the four largest below-stated gaps shown in the overview.',86,610,1100,30);
}

// 6. Decile contribution
{
 const s=base('The highest-value customers drive most revenue','Subscriber contribution',6,'The dashboard ranks customers by period ARPU and groups them into ten deciles.');
 chart(s,'bar',{position:{left:90,top:208,width:780,height:385},categories:['Decile 1','Decile 2','Decile 3','Decile 4','Decile 5'],series:[{name:'Share of received revenue (%)',values:[41.1,19.5,10.6,8.6,6.7],fill:C.red}],
  hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:75},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0"%"',textStyle:{typeface:FONT,fontSize:14,bold:true}},
  xAxis:{min:0,max:50,majorUnit:10,numberFormatCode:'0"%"',textStyle:{typeface:FONT,fontSize:12},majorGridlines:{style:'solid',fill:C.line,width:1}},
  yAxis:{textStyle:{typeface:FONT,fontSize:13}},chartFill:C.white,plotAreaFill:C.white});
 txt(s,'41.1%',935,260,240,65,36,C.red,true);
 txt(s,'from the top decile',938,325,260,34,18,C.ink,false);
 shape(s,'line',935,390,210,1,'none',C.line,1);
 txt(s,'71.2%',935,420,240,65,36,C.navy,true);
 txt(s,'from the top three deciles',938,485,280,52,18,C.ink,false);
 note(s,'The top three deciles are the first three groups in the dashboard ranking.',90,610,1090,32);
}

// 7. Monthly trend selected plan
{
 const s=base('Postpaid 399 revenue moved up and down each month','A closer look at one plan',7,'Monthly values follow the starting amount and month-to-month changes in Revenue Detail.');
 chart(s,'line',{position:{left:84,top:204,width:790,height:390},categories:['Jan','Feb','Mar','Apr','May','Jun'],series:[{name:'Received revenue (₹)',values:[228851,206298,225624,212854,214434,182842],line:{fill:C.red,width:3},marker:{symbol:'circle',size:8,fill:C.red}}],
  hasLegend:false,lineOptions:{smooth:false},
  dataLabels:{showValue:true,position:'top',numberFormatCode:'₹#,##0',textStyle:{typeface:FONT,fontSize:11}},
  yAxis:{min:160000,max:240000,majorUnit:20000,numberFormatCode:'₹#,##0',textStyle:{typeface:FONT,fontSize:11},majorGridlines:{style:'solid',fill:C.line,width:1}},
  xAxis:{textStyle:{typeface:FONT,fontSize:13}},chartFill:C.white,plotAreaFill:C.white});
 txt(s,'Selected plan',930,240,255,24,13,C.red,true);
 txt(s,'Postpaid 399',930,274,260,45,24,C.navy,true);
 txt(s,'Highest month',930,370,255,24,13,C.muted,true);
 txt(s,'January',930,399,260,38,20,C.ink,true);
 txt(s,'Lowest month',930,465,255,24,13,C.muted,true);
 txt(s,'June',930,494,260,38,20,C.ink,true);
 note(s,'Monthly values are reconstructed from the dashboard’s January amount and displayed monthly changes.',84,610,1110,35);
}

// 8. Plan detail
{
 const s=base('Postpaid 399 is slightly above its stated ARPU','Selected plan detail',8,'This is one selected plan from the Revenue Detail dashboard.');
 txt(s,'524',88,220,280,80,44,C.blue,true);
 txt(s,'subscribers',92,300,260,30,18,C.muted,false);
 txt(s,'₹1.27M',430,220,360,80,44,C.red,true);
 txt(s,'received revenue',434,300,320,30,18,C.muted,false);
 txt(s,'₹404.23',855,220,330,80,42,C.green,true);
 txt(s,'actual monthly ARPU',859,300,300,30,18,C.muted,false);
 shape(s,'line',88,374,1100,1,'none',C.line,1);
 txt(s,'ARPU comparison',90,408,400,32,20,C.navy,true);
 txt(s,'Stated',90,470,135,28,15,C.muted,true);
 shape(s,'rect',230,472,430,26,C.line,'none',0);
 txt(s,'₹399',675,466,105,36,17,C.ink,true);
 txt(s,'Actual',90,528,135,28,15,C.muted,true);
 shape(s,'rect',230,530,436,26,C.green,'none',0);
 txt(s,'₹404.23',680,524,160,36,17,C.green,true);
 note(s,'The plan detail dashboard reports ₹399 as the stated ARPU reference.',90,610,1050,34);
}

// 9. Payment journeys
{
 const s=base('Customers use several routes to make payments','Recharge and payment view',9,'The detail dashboard connects recharge channels to transaction types.');
 txt(s,'Recharge channel',84,217,400,34,22,C.navy,true);
 txt(s,'Airtel App',94,300,300,34,20,C.red,true);
 txt(s,'AutoPay',94,388,300,34,20,C.blue,true);
 txt(s,'Website',94,476,300,34,20,'#E18A1A',true);
 shape(s,'line',430,318,260,1,'none',C.line,2);
 shape(s,'line',430,406,260,1,'none',C.line,2);
 shape(s,'line',430,494,260,1,'none',C.line,2);
 txt(s,'Bill payment',740,370,300,44,24,C.navy,true);
 txt(s,'The dashboard lets you filter by connection, region, device and plan.',84,565,1080,34,18,C.ink,false);
 note(s,'The screenshot shows channel names but no exact channel totals, so this slide does not assign amounts.',84,610,1100,34);
}

// 10. Takeaways
{
 const s=base('What stands out','Summary',10,'A few clear points from the two dashboard views.');
 const ys=[218,305,392,479];
 const points=[
  ['Revenue is concentrated','The top 10% of subscribers bring in 41.1% of received revenue.'],
  ['Postpaid has a strong revenue share','It earns 62.1% of revenue from 22.1% of subscribers.'],
  ['Review the biggest plan gap','Prepaid Quarterly 719 is ₹140 below stated ARPU.'],
  ['T5 is still pending','The dashboard marks the statistical test as not validated.']
 ];
 for(let i=0;i<points.length;i++){
  txt(s,String(i+1).padStart(2,'0'),88,ys[i],70,32,16,C.red,true);
  txt(s,points[i][0],175,ys[i]-2,380,32,19,C.navy,true);
  txt(s,points[i][1],560,ys[i]-2,600,52,18,C.ink,false);
 }
 note(s,'Source: Airtel Telecom Analytics dashboard screenshots. Data period: 1 Jan–27 Jun 2025.',88,610,1090,34);
}

// Save slide previews for layout review and a draft for final validation.
for(let i=0;i<p.slides.items.length;i++){
 const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(buildDir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const draft=path.join(buildDir,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(draft);
const SKILL_DIR='C:\\Users\\saali\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1123.11515\\skills\\presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({explicitTotalSlideCount:10,requiredNativeChartOwnerSlides:[4,5,6,7],materializeLiteralChartWorkbooks:true,workspaceDir,candidatePath:draft,finalPath,pythonExecutable:'C:\\Program Files\\WindowsApps\\OpenAI.CodexPrimaryRuntime.v26-1123-915-0_26.1123.915.0_x64__3k8sg7r9htsxt\\dependencies\\python\\python.exe',integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(buildDir,'validation-final.json')});
console.log(JSON.stringify({finalPath,result,slides:p.slides.items.length},null,2));






