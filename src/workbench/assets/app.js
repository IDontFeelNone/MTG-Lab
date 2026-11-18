'use strict';
// Presentation and caller-local identity ownership only. The Python owner does all probability work.
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="mtg-lab-token"]').content;
let cards = {}, nextCard = 1, revision = 0, report = null, busy = false;
const blankDeck = id => ({deck_id:id, complete:false, section:'main', entries:[],
  groups:[{group_id:'Key cards', members:[], minimum:1}], schedule:[{label:'Opening hand assumption',cards_seen:7}]});
let decks = [blankDeck('baseline')];
function node(tag, text, attrs = {}) {
  const el = document.createElement(tag);
  if (text !== null) el.textContent = text;
  for (const [k,v] of Object.entries(attrs)) el.setAttribute(k,v);
  return el;
}
function button(text, action) { const b=node('button',text,{type:'button'});b.addEventListener('click',action);return b; }
function field(parent, title, value, action, type='text', attrs={}) {
  const label=node('label',title);const input=node('input',null,{type,...attrs});
  if(type==='checkbox') input.checked=value; else input.value=value;
  input.addEventListener('input',()=>{action(type==='checkbox'?input.checked:type==='number'?input.valueAsNumber:input.value);invalidate();derived();});
  label.append(input);parent.append(label);return input;
}
function invalidate() {
  revision++;report=null;$('download').disabled=true;$('results').replaceChildren();
  $('freshness').textContent='Inputs changed — recalculate to obtain a current report.';
  $('freshness').className='stale';
}
function selected(deck) {return deck.entries.filter(e=>e.section===deck.section);}
function freshLabel(prefix, labels) {
  let n=labels.length+1;while(labels.includes(prefix+' '+n))n++;return prefix+' '+n;
}
function derived() {
  for (let di=0;di<decks.length;di++) {
    const deck=decks[di], size=selected(deck).reduce((n,e)=>n+e.quantity,0);
    const out=$('size-'+di); if(out)out.textContent='Selected population: '+size+' cards (supported: 1–120).';
    deck.groups.forEach((g,gi)=>{const target=$('count-'+di+'-'+gi);if(target)target.textContent='Derived copies: '+selected(deck).filter(e=>g.members.includes(e.card_id)).reduce((n,e)=>n+e.quantity,0);});
  }
  document.querySelectorAll('[data-card-label]').forEach(el=>{el.textContent=cards[el.dataset.cardLabel]||el.dataset.cardLabel;});
  document.querySelectorAll('[data-card-input]').forEach(el=>{if(el!==document.activeElement)el.value=cards[el.dataset.cardInput];});
  document.querySelectorAll('[data-card-option]').forEach(el=>{el.textContent=cards[el.dataset.cardOption]+' ['+el.dataset.cardOption+']';});
}
function selectSection(parent, title, value, action) {
  // Standard sections plus an explicit named other: section; no hidden population union.
  const label=node('label',title), input=node('input',null,{list:'sections',maxlength:'48'});input.value=value;
  input.addEventListener('input',()=>{action(input.value);invalidate();derived();});
  input.addEventListener('change',()=>{action(input.value);invalidate();render();});label.append(input);parent.append(label);
}
function render() {
  $('decks').replaceChildren();
  const list=node('datalist',null,{id:'sections'});['main','sideboard','commander','companion','other:custom'].forEach(v=>list.append(node('option',null,{value:v})));$('decks').append(list);
  decks.forEach((deck,di)=>{
    const section=node('section',null,{class:'deck','aria-label':di?'Alternative deck':'Baseline deck'});
    section.append(node('h2',di?'Alternative configuration':'Baseline configuration'));
    selectSection(section,'Selected draw section',deck.section,v=>deck.section=v);
    section.append(node('p','',{class:'size',id:'size-'+di}));
    const complete=node('div',null,{class:'complete'});
    field(complete,'I have listed the complete selected population.',deck.complete,v=>deck.complete=v,'checkbox');section.append(complete);
    section.append(node('h3','Deck entries'));
    for (const [ei,entry] of deck.entries.entries()) {
      const row=node('div',null,{class:'row','data-entry-id':entry.card_id});
      field(row,'Card label',cards[entry.card_id],v=>cards[entry.card_id]=v,'text',{maxlength:'128',class:'card-label','data-card-input':entry.card_id});
      row.append(node('span',entry.card_id+' · caller-local, not canonical',{class:'identity'}));
      field(row,'Copies',entry.quantity,v=>entry.quantity=v,'number',{min:'0',max:'120',step:'1'});
      selectSection(row,'Section',entry.section,v=>entry.section=v);
      row.append(button('Remove entry',()=>{deck.entries.splice(ei,1);invalidate();render();}));section.append(row);
    }
    const tools=node('div',null,{class:'toolbar'});
    tools.append(button('Add new card',()=>{if(deck.entries.length>=512)return;const id='local-card-'+nextCard++;cards[id]='Card '+(nextCard-1);deck.entries.push({card_id:id,section:deck.section,quantity:1});invalidate();render();}));
    const reuse=node('select',null,{'aria-label':'Existing caller-local card'});reuse.append(node('option','Select existing card',{value:''}));
    Object.keys(cards).forEach(id=>reuse.append(node('option',cards[id]+' ['+id+']',{value:id,'data-card-option':id})));
    tools.append(reuse,button('Add existing card row',()=>{if(!reuse.value||deck.entries.length>=512)return;deck.entries.push({card_id:reuse.value,section:deck.section,quantity:1});invalidate();render();}));section.append(tools);
    section.append(node('h3','Required card groups'));
    section.append(node('p','All group minima must be met together. Select interchangeable members yourself; groups must not overlap.'));
    deck.groups.forEach((g,gi)=>{
      const group=node('fieldset');group.append(node('legend','Group '+(gi+1)));
      field(group,'Group label',g.group_id,v=>g.group_id=v,'text',{maxlength:'64'});
      field(group,'Minimum cards required',g.minimum,v=>g.minimum=v,'number',{min:'0',max:'120',step:'1'});
      group.append(node('p','',{id:'count-'+di+'-'+gi,class:'muted'}));const members=node('div',null,{class:'members'});
      const eligible=[...new Set([...selected(deck).map(e=>e.card_id),...g.members])];
      eligible.forEach(id=>{const label=node('label');const check=node('input',null,{type:'checkbox','aria-label':'Group '+(gi+1)+' member '+id});check.checked=g.members.includes(id);
        check.addEventListener('input',()=>{g.members=check.checked?[...g.members,id]:g.members.filter(x=>x!==id);invalidate();derived();});
        label.append(check,node('span',null,{'data-card-label':id}));if(!selected(deck).some(e=>e.card_id===id))label.append(node('span',' (not in selected population)'));members.append(label);});
      group.append(members,button('Remove group',()=>{deck.groups.splice(gi,1);invalidate();render();}));section.append(group);
    });
    const addGroup=button('Add group',()=>{deck.groups.push({group_id:freshLabel('Group',deck.groups.map(g=>g.group_id)),members:[],minimum:1});invalidate();render();});addGroup.disabled=deck.groups.length>=3;section.append(addGroup);
    section.append(node('h3','Cumulative cards seen'));
    section.append(node('p','Enter nondecreasing counts, 0–20 and no more than the selected deck size. Labels do not establish Magic turn rules.'));
    deck.schedule.forEach((s,si)=>{const row=node('div',null,{class:'row'});
      field(row,'Observation label',s.label,v=>s.label=v,'text',{maxlength:'80'});
      field(row,'Cards seen',s.cards_seen,v=>s.cards_seen=v,'number',{min:'0',max:'20',step:'1'});
      row.append(button('Remove observation',()=>{deck.schedule.splice(si,1);invalidate();render();}));section.append(row);});
    const addObservation=button('Add observation',()=>{deck.schedule.push({label:freshLabel('Observation',deck.schedule.map(s=>s.label)),cards_seen:deck.schedule.at(-1)?.cards_seen??0});invalidate();render();});addObservation.disabled=deck.schedule.length>=21;section.append(addObservation);
    $('decks').append(section);
  });
  $('duplicate').hidden=decks.length===2;$('remove-alternative').hidden=decks.length===1;derived();
}
function request() {
  const ids=new Set(decks.flatMap(d=>d.entries.map(e=>e.card_id)));
  return {schema_version:'deck-workbench-input-v1',labels:[...ids].sort().map(id=>({card_id:id,label:cards[id]})),analysis:{schema_version:'supplied-deck-consistency-input-v1',decks:decks.map(d=>({
    deck_id:d.deck_id, identity_authority:'CALLER_DECLARED',complete:d.complete,
    draw_population:{section:d.section,declared_size:selected(d).reduce((n,e)=>n+e.quantity,0)},
    entries:d.entries,groups:d.groups,schedule:d.schedule,
    assumptions:{sampling:'uniform-without-replacement',group_disjointness:'caller_declared'}
  }))}};
}
function showReport(value) {
  const root=$('results');root.replaceChildren();const a=value.analysis, labels=Object.fromEntries(value.input.labels.map(x=>[x.card_id,x.label]));
  for(const [i,d] of a.configurations.entries()) {
    const box=node('section',null,{class:'result'});box.append(node('h2',d.deck_id+': '+d.deck_size+' cards from '+d.selected_section));
    for(const g of d.derived_groups)box.append(node('p',g.group_id+': '+g.copies+' copies; minimum '+g.minimum+'; members '+value.input.analysis.decks[i].groups.find(x=>x.group_id===g.group_id).members.map(id=>labels[id]+' ['+id+']').join(', ')));
    if(d.impossible_group_ids.length)box.append(node('p','Valid deck, impossible requirement: '+d.impossible_group_ids.join(', ')+'. The declared groups do not contain enough copies.',{class:'notice'}));
    const table=node('table');const head=node('tr');['Observation','Cards seen','Exact access probability','Percent'].forEach(t=>head.append(node('th',t,{scope:'col'})));table.append(head);
    d.results.forEach((row,j)=>{const tr=node('tr');[row.label,String(row.cards_seen),row.probability.numerator+'/'+row.probability.denominator,value.presentation.configurations[i].observations[j].percent+'%'].forEach(t=>tr.append(node('td',t)));table.append(tr);});
    const scroll=node('div',null,{class:'scroll'});scroll.append(table);box.append(scroll);root.append(box);
    d.results.filter(row=>row.probability.numerator==='0').forEach(row=>box.append(node('p',
      'Exact zero at '+row.label+': no draw of this declared size satisfies all group requirements.')));
    box.append(node('p','Percentages are rounded for display; exact fractions determine zero and certainty.',{class:'muted'}));
  }
  const c=a.comparison;root.append(node('h3','Comparison: '+c.status));
  if(c.status==='ABSTAINED')root.append(node('p','No direct improvement claim: '+c.reasons.join('; ')));
  c.differences.forEach((row,i)=>{const p=row.candidate_minus_baseline;root.append(node('p',row.label+': candidate minus baseline '+p.numerator+'/'+p.denominator+' = '+value.presentation.differences[i].percentage_points+' percentage points.'));});
  a.limitations.forEach(text=>root.append(node('p',text,{class:'muted'})));
  root.append(node('p','Input: '+value.input_id),node('p','Analytical report: '+a.report_id),node('p','Workbench report: '+value.report_id));
}
$('duplicate').addEventListener('click',()=>{if(decks.length!==1)return;const d=structuredClone(decks[0]);d.deck_id='candidate';decks.push(d);invalidate();render();});
$('remove-alternative').addEventListener('click',()=>{decks=decks.slice(0,1);invalidate();render();});
$('example').addEventListener('click',()=>{cards={'local-card-1':'Fictional target','local-card-2':'Fictional remainder'};nextCard=3;
  const a=blankDeck('baseline');a.complete=true;a.entries=[{card_id:'local-card-1',section:'main',quantity:3},{card_id:'local-card-2',section:'main',quantity:57}];a.groups[0].members=['local-card-1'];decks=[a];invalidate();render();});
$('calculate').addEventListener('click',async()=>{
  if(busy)return;const version=revision;busy=true;$('calculate').disabled=true;report=null;$('download').disabled=true;$('results').replaceChildren();$('freshness').textContent='Calculating exact access…';
  try {
    const response=await fetch('/assess',{method:'POST',headers:{'Content-Type':'application/json','X-MTG-Lab-Token':token},body:JSON.stringify(request()),credentials:'omit',cache:'no-store'});
    const result=await response.json();if(version!==revision)return;
    if(!response.ok||result.status!=='ASSESSED')throw new Error(result.reason||'Local calculation refused.');
    report=result;showReport(result);$('freshness').textContent='Current result for these exact inputs. Download is optional.';$('freshness').className='';$('download').disabled=false;
  } catch(error) {if(version===revision){$('freshness').textContent='REFUSED: '+error.message;$('freshness').className='error';}}
  finally {busy=false;$('calculate').disabled=false;}
});
$('download').addEventListener('click',()=>{
  if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)+'\n'],{type:'application/json'}));
  const a=node('a',null,{href:url,download:'mtg-lab-deck-access.json'});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
render();
