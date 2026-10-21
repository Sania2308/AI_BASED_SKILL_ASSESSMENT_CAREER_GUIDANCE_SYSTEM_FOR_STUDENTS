async function extractSkills(){
    const text=document.getElementById('resume').value;
    const result=document.getElementById('result');
    if(!text.trim()){result.innerHTML='<span class="empty-tag">Enter resume or skills text first.</span>';return;}
    const body=new URLSearchParams({text});
    const r=await fetch('/api/extract-skills',{method:'POST',body});
    const d=await r.json();
    if(d.error){result.innerHTML='<span class="empty-tag">'+d.error+'</span>';return;}
    result.innerHTML=d.skills.length?d.skills.map(s=>`<span>${s}</span>`).join(''):'<span class="empty-tag">No supported skills found.</span>';
}

async function resetSkills(){
    const r=await fetch('/api/reset-skills',{method:'POST'});
    const d=await r.json();
    document.getElementById('result').innerHTML='<span class="empty-tag">Saved skills cleared.</span>';
}

document.addEventListener('DOMContentLoaded',()=>{
    const form=document.getElementById('assessmentForm');
    if(!form)return;
    form.addEventListener('change',()=>{
        const values=[...form.querySelectorAll('input:checked')].map(x=>Number(x.value));
        if(values.length){document.getElementById('liveScore').textContent=Math.round(values.reduce((a,b)=>a+b,0)/(values.length*5)*100)+'%';}
    });
    form.addEventListener('submit',async(e)=>{
        e.preventDefault();
        const answers={};
        for(let i=1;i<=10;i++){const checked=form.querySelector(`input[name="q${i}"]:checked`);if(!checked){document.getElementById('assessmentMessage').textContent=' Please answer all 10 questions.';return;}answers[i]=checked.value;}
        const r=await fetch('/api/assessment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers})});
        const d=await r.json();
        if(!r.ok){document.getElementById('assessmentMessage').textContent=' '+d.error;return;}
        document.getElementById('liveScore').textContent=d.score+'%';
        document.getElementById('categoryScores').innerHTML=`<p>Technical Skills: <b>${d.categories['Technical Skills']}%</b></p><p>Problem Solving: <b>${d.categories['Problem Solving']}%</b></p><p>Communication: <b>${d.categories['Communication']}%</b></p><p>Domain Knowledge: <b>${d.categories['Domain Knowledge']}%</b></p>`;
        document.getElementById('assessmentMessage').textContent=' '+d.message+' Dashboard updated.';
        window.scrollTo({top:0,behavior:'smooth'});
    });
});


async function startTechnicalAssessment(skill){
    const panel=document.getElementById('technicalAssessmentPanel');
    const form=document.getElementById('technicalAssessmentForm');
    const title=document.getElementById('technicalAssessmentTitle');
    const subtitle=document.getElementById('technicalAssessmentSubtitle');
    const message=document.getElementById('technicalAssessmentMessage');
    message.textContent='';
    const r=await fetch('/api/technical-assessment/'+encodeURIComponent(skill));
    const d=await r.json();
    if(!r.ok){message.textContent=' '+(d.error||'Unable to load assessment.');return;}
    title.textContent=skill+' Skill Assessment';
    subtitle.textContent='Answer all 10 questions. Your score will determine your verified proficiency level.';
    form.dataset.skill=skill;
    form.innerHTML=d.questions.map((q,i)=>`<div class="question-card"><div class="question-title"><span>${q.id}</span><b>${q.text}</b><small>Technical Knowledge</small></div><div class="options">${q.options.map((o,j)=>`<label><input type="radio" name="tq${q.id}" value="${j}" required><span>${o}</span></label>`).join('')}</div></div>`).join('');
    panel.style.display='block';
    panel.scrollIntoView({behavior:'smooth',block:'start'});
}

function closeTechnicalAssessment(){
    const panel=document.getElementById('technicalAssessmentPanel');
    if(panel) panel.style.display='none';
}

async function submitTechnicalAssessment(e){
    e.preventDefault();
    const form=document.getElementById('technicalAssessmentForm');
    const skill=form.dataset.skill;
    const answers={};
    for(let i=1;i<=10;i++){
        const checked=form.querySelector(`input[name="tq${i}"]:checked`);
        if(!checked){document.getElementById('technicalAssessmentMessage').textContent=' Please answer all 10 questions.';return;}
        answers[i]=checked.value;
    }
    const r=await fetch('/api/technical-assessment/'+encodeURIComponent(skill),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers})});
    const d=await r.json();
    const msg=document.getElementById('technicalAssessmentMessage');
    if(!r.ok){msg.textContent=' '+(d.error||'Assessment failed.');return;}
    msg.textContent=` ${d.message} Score: ${d.score}% — ${d.level}.`;
    setTimeout(()=>window.location.reload(),900);
}
