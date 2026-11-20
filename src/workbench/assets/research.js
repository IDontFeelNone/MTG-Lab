'use strict';
// Additive composition over the unchanged editor. No model, storage or provider access.
let investigation = null, loadedResearchRevision = null, researchDirty = false, researchEpoch = 0, researchBusy = false;
let retainedReferences = [];
const researchFields = ['assumptions','notes','counterexamples','rejected_alternatives','unresolved_questions'];
const researchStamp = () => new Date().toISOString().slice(0,19)+'Z';
function researchStatus(text) { $('research-status').textContent=text; }
function researchButtons() {
  $('research-save').disabled=!investigation||researchDirty||researchBusy;
  $('research-export').disabled=!investigation||researchDirty||researchBusy;
  $('research-replay').disabled=!investigation||researchBusy;
}
function markResearchDirty() { researchDirty=true;researchEpoch++;researchButtons();researchStatus('Unsaved changes. Record a revision before saving or exporting; prior results remain historical.'); }
async function researchCall(value) {
  const response=await fetch('/research',{method:'POST',headers:{'Content-Type':'application/json','X-MTG-Lab-Token':token},body:JSON.stringify(value),credentials:'omit',cache:'no-store'});
  const result=await response.json();if(!response.ok)throw new Error(result.reason||'Research request refused.');return result;
}
async function researchAction(action) {
  if(researchBusy||busy)return;researchBusy=true;researchButtons();const epoch=researchEpoch;
  try {await action(epoch);}catch(error){researchStatus('REFUSED: '+error.message);}
  finally{researchBusy=false;researchButtons();}
}
function researchDownload(name, text, type) {
  const url=URL.createObjectURL(new Blob([text],{type}));const a=node('a',null,{href:url,download:name});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function restoreResearchEditor(row) {
  const input=row?.analytical_input;cards=Object.create(null);nextCard=1;
  if(input) {
    input.labels.forEach(x=>{cards[x.card_id]=x.label;const match=/^local-card-(\d+)$/.exec(x.card_id);if(match)nextCard=Math.max(nextCard,Number(match[1])+1);});
    decks=input.analysis.decks.map(d=>({deck_id:d.deck_id,complete:d.complete,section:d.draw_population.section,
      entries:structuredClone(d.entries),groups:structuredClone(d.groups),schedule:structuredClone(d.schedule)}));
  } else decks=[blankDeck('baseline')];
  invalidate();render();report=row?.result?structuredClone(row.result):null;
  if(report){showReport(report);$('download').disabled=false;$('freshness').textContent='Verified saved experiment for these exact inputs. Changes require recalculation.';}
}
function loadResearchRevision(row) {
  loadedResearchRevision=row?.revision_id||null;
  $('research-branch').value=row?.branch_id||'baseline';
  const metadata=row?.metadata;
  $('research-hypothesis').value=metadata?.hypothesis||'';$('research-outcome').value=metadata?.outcome||'exploring';
  researchFields.forEach(k=>{$('research-'+k).value=(metadata?.[k]||[]).join('\n');});
  retainedReferences=structuredClone(metadata?.evidence_references||[]);$('research-reference').value='';
  $('research-notes-only').checked=!row?.analytical_input;
  restoreResearchEditor(row);researchDirty=false;researchEpoch++;researchButtons();
  researchStatus(row?'Loaded saved revision '+row.revision_id+'. Historical siblings are independent.':'Question opened; no calculation yet.');
}
function renderResearchHistory() {
  const root=$('research-history');root.replaceChildren();
  $('research-question').value=investigation.question;$('research-question').readOnly=true;
  $('research-id').textContent=investigation.investigation_id+' · '+investigation.artifact_id;
  investigation.revisions.forEach(r=>{const box=node('section',null,{class:'result'}), label=node('label');
    const check=node('input',null,{type:'checkbox','data-research-selection':r.revision_id});check.checked=true;
    label.append(check,node('span','Include '+r.branch_id+' · '+r.revision_id+' · '+r.metadata.outcome));box.append(label);
    box.append(node('p','Parent: '+(r.parent_id||'root')+'; '+(r.result?'verified saved calculation':'NOT CALCULATED')),
      button('Load revision '+r.branch_id,()=>{if(researchBusy||busy)return;if(researchDirty&&!confirm('Discard unsaved editor changes and load this saved revision?'))return;loadResearchRevision(r);}));root.append(box);
  });
}
function acceptResearch(value, row=null) { investigation=value;renderResearchHistory();loadResearchRevision(row||value.revisions.at(-1)); }
$('research-new').addEventListener('click',()=>researchAction(async epoch=>{
  if(investigation&&!confirm('Start a separate investigation? Download your current history first if needed.'))return;
  const result=await researchCall({operation:'create',key:'research:'+crypto.randomUUID(),question:$('research-question').value,created_at:researchStamp()});
  if(epoch!==researchEpoch)throw new Error('Inputs changed during request; try again.');acceptResearch(result.artifact);
}));
$('research-reset').addEventListener('click',()=>{
  if(researchBusy||busy)return;if(investigation&&!confirm('Clear working memory? Save your investigation first if needed.'))return;
  investigation=null;$('research-question').readOnly=false;$('research-question').value='';$('research-id').textContent='';
  $('research-history').replaceChildren();loadResearchRevision(null);
});
$('research-example').addEventListener('click',()=>researchAction(async epoch=>{
  if(investigation&&!confirm('Replace the in-memory investigation with the original example?'))return;
  const result=await researchCall({operation:'example'});if(epoch!==researchEpoch)throw new Error('Inputs changed during request; try again.');acceptResearch(result.artifact);
}));
$('research-record').addEventListener('click',()=>researchAction(async epoch=>{
  if(!investigation)throw new Error('Start a research question first.');
  const branch=$('research-branch').value, head=investigation.revisions.filter(r=>r.branch_id===branch).at(-1);
  if(head&&loadedResearchRevision!==head.revision_id)throw new Error('Load this branch’s latest saved revision before extending it, or use a new branch identity.');
  const notesOnly=$('research-notes-only').checked;
  if(!notesOnly&&!report)throw new Error('Calculate current deck inputs first, or explicitly save a notes-only revision.');
  const metadata={created_at:researchStamp(),hypothesis:$('research-hypothesis').value,outcome:$('research-outcome').value,evidence_references:structuredClone(retainedReferences)};
  researchFields.forEach(k=>metadata[k]=$('research-'+k).value.split('\n').filter(s=>s.trim()));
  const ref=$('research-reference').value;if(ref)metadata.evidence_references.push({relation:'supporting',label:'User-declared reference',reference:ref});
  const result=await researchCall({operation:'append',artifact:investigation,branch_id:branch,parent_id:head?.revision_id||loadedResearchRevision,
    metadata,analytical_input:notesOnly?null:report.input,calculate:!notesOnly});
  if(epoch!==researchEpoch)throw new Error('Inputs changed during request; no revision was installed.');acceptResearch(result.artifact);
}));
$('research-save').addEventListener('click',()=>{if(!investigation||researchDirty||researchBusy)return;
  researchDownload('mtg-lab-investigation-'+investigation.artifact_id.slice(7,19)+'.json',JSON.stringify(investigation),'application/json');
  researchStatus('Explicit download requested. Keep this file to reopen the complete history; nothing was saved on the server.');});
$('research-replay').addEventListener('click',()=>researchAction(async()=>{
  const result=await researchCall({operation:'replay',artifact:investigation});researchStatus(result.status+': '+result.calculations_verified+' stored calculations. '+(researchDirty?'The edited working copy is still unsaved.':''));
}));
$('research-export').addEventListener('click',()=>researchAction(async epoch=>{
  if(researchDirty)throw new Error('Record current changes before export.');
  const ids=[...document.querySelectorAll('[data-research-selection]:checked')].map(x=>x.dataset.researchSelection);
  const result=await researchCall({operation:'export',artifact:investigation,revision_ids:ids});
  if(epoch!==researchEpoch)throw new Error('Inputs changed during export; no file was downloaded.');
  researchDownload('mtg-lab-research-handoff.txt',result.handoff,'text/plain;charset=utf-8');
  researchStatus('Selected handoff download requested. Review privacy and permissions before manually sharing; no AI connection was used.');
}));
$('research-open').addEventListener('change',()=>researchAction(async epoch=>{
  const file=$('research-open').files[0];if(!file)return;if(file.size>2097152)throw new Error('Investigation exceeds 2 MiB.');
  // Send exact file bytes wrapped as a JSON string; Python performs strict duplicate-key decoding.
  const raw=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer());
  const response=await fetch('/research',{method:'POST',headers:{'Content-Type':'application/json','X-MTG-Lab-Token':token},
    body:JSON.stringify({operation:'open',artifact:raw}),credentials:'omit',cache:'no-store'});
  const result=await response.json();if(!response.ok)throw new Error(result.reason||'Invalid investigation.');
  if(epoch!==researchEpoch)throw new Error('Inputs changed during reopen; working state was retained.');acceptResearch(result.artifact);
}));
document.addEventListener('input',event=>{if(event.target.closest('main')||event.target.closest('#research-panel')&&!event.target.hasAttribute('data-research-selection'))markResearchDirty();});
document.querySelector('main').addEventListener('click',event=>{const b=event.target.closest('button');if(b&&!['calculate','download'].includes(b.id))markResearchDirty();});
// A new investigation may start from exploratory notes, before the deck is valid.
$('research-notes-only').checked=true;
