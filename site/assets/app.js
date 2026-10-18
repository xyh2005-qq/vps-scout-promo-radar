'use strict';
(()=>{
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const plans=JSON.parse($('#plan-data')?.textContent||'[]'), byId=new Map(plans.map(p=>[p.id,p]));
  const announce=message=>{$('#announcement').textContent=message};
  const currency=value=>'$'+Number(value).toFixed(2);
  const params=new URLSearchParams(location.search);
  let selected=(params.get('plans')||'').split(',').filter(id=>byId.has(id)).slice(0,3);
  selected=[...new Set(selected)];
  const setQuery=(key,value)=>{const u=new URL(location.href);if(value)u.searchParams.set(key,value);else u.searchParams.delete(key);history.replaceState(null,'',u.pathname+u.search+u.hash)};
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
  const dialog=$('#compare-dialog');
  function renderComparison(){
    const root=$('#compare-content');root.replaceChildren();
    const hint=node('p','Swipe sideways to compare →','compare-hint');root.append(hint);
    const grid=node('div',undefined,'compare-grid');grid.tabIndex=0;grid.setAttribute('role','region');grid.setAttribute('aria-label','Selected plans comparison; scroll horizontally on smaller screens');grid.style.setProperty('--columns',selected.length);
    selected.forEach(id=>{
      const p=byId.get(id),col=node('article',undefined,'compare-column');
      col.append(node('span',p.provider,'micro'),node('h3',p.name));
      const price=node('div',currency(p.price),'price');price.append(node('span',' / '+p.billing));
      col.append(price,node('p',currency(p.monthly)+'/mo equivalent'+(p.billing==='year'?' · full year upfront':p.billing==='quarter'?' · full quarter upfront':' · published monthly rate')));
      const specs=node('ul');p.specs.slice(0,4).forEach(s=>specs.append(node('li',s)));
      if(p.specs.some(s=>s.includes('IPv6 only')))specs.append(node('li','IPv6 only — no IPv4'));
      const link=node('a','Inspect source & terms ↗');link.href=p.url;
      const remove=node('button','Remove plan','compare-remove');remove.type='button';remove.setAttribute('aria-label','Remove '+p.provider+' '+p.name);remove.onclick=()=>{selected=selected.filter(x=>x!==id);updateSelected();if(selected.length){renderComparison();$('#compare-close').focus()}else dialog.close()};
      col.append(specs,link,remove);grid.append(col);
    });root.append(grid);
  }
  function updateSelected(){
    $$('#compare-tray').forEach(t=>t.hidden=!selected.length);
    document.body.classList.toggle('has-comparison',!!selected.length);
    $('#tray-count').textContent=selected.length+' '+(selected.length===1?'plan':'plans');
    $('#tray-names').replaceChildren(...selected.map(id=>node('span',byId.get(id).name)));
    $$('[data-compare]').forEach(b=>{const active=selected.includes(b.dataset.compare);b.setAttribute('aria-pressed',String(active));b.disabled=!active&&selected.length===3;b.querySelector('span')&&(b.querySelector('span').textContent=active?'✓':'+');b.closest('.card')?.classList.toggle('is-selected',active)});
    $('#compare-open').disabled=selected.length<2;
    $('#compare-open').firstChild.nodeValue=selected.length<2?'Add one more ':'Compare ';
    $('#compare-open').setAttribute('aria-label',selected.length<2?'Select at least two plans to compare':'Compare '+selected.length+' selected plans');
    setQuery('plans',selected.join(','));
  }
  $$('[data-compare]').forEach(b=>b.addEventListener('click',()=>{
    const id=b.dataset.compare;
    if(selected.includes(id))selected=selected.filter(x=>x!==id);
    else if(selected.length<3)selected.push(id);
    updateSelected();announce(selected.length+' plans selected. '+(selected.length===3?'Comparison limit reached. Remove a plan to choose another.':selected.length===1?'Select one more to compare.':'Ready to compare.'));
  }));
  $('#compare-open').onclick=()=>{renderComparison();dialog.showModal();document.body.style.overflow='hidden'};
  $('#compare-close').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{document.body.style.overflow='';$('#compare-open').focus()});
  dialog.addEventListener('click',ev=>{if(ev.target===dialog){const r=dialog.getBoundingClientRect();if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom)dialog.close()}});
  $('#compare-clear').onclick=()=>{selected=[];updateSelected();document.querySelector('[data-compare]')?.focus({preventScroll:true});announce('Comparison cleared.')};
  updateSelected();
  $$('nav a').forEach(a=>{if(location.pathname!=='/'&&new URL(a.href).pathname===location.pathname)a.setAttribute('aria-current','page')});
  // The atlas presents the same source-backed data as the list; no synthetic measurements.
  const points=$$('.map-point');
  function selectPoint(button,focus=false){
    const p=byId.get(button.dataset.plan);if(!p)return;
    points.forEach(b=>{const active=b===button;b.classList.toggle('is-active',active);b.setAttribute('aria-pressed',String(active));b.tabIndex=active?0:-1});
    $('#map-provider').textContent=p.provider;const link=$('#map-name');link.replaceChildren(document.createTextNode(p.name+' '),node('span','↗'));link.href=p.url;
    $('#map-billing').textContent=currency(p.price)+' / '+p.billing+' published price';$('#map-price').replaceChildren(document.createTextNode(currency(p.monthly)),node('small','/mo equiv.'));
    if(focus)button.focus();
  }
  points.forEach((b,i)=>{b.addEventListener('click',()=>selectPoint(b));b.addEventListener('keydown',ev=>{let j;if(['ArrowRight','ArrowDown'].includes(ev.key))j=(i+1)%points.length;else if(['ArrowLeft','ArrowUp'].includes(ev.key))j=(i-1+points.length)%points.length;else if(ev.key==='Home')j=0;else if(ev.key==='End')j=points.length-1;if(j!==undefined){ev.preventDefault();selectPoint(points[j],true)}})});
  $('#map-prev')?.addEventListener('click',()=>{if(points.length)selectPoint(points[(points.findIndex(p=>p.classList.contains('is-active'))-1+points.length)%points.length])});
  $('#map-next')?.addEventListener('click',()=>{if(points.length)selectPoint(points[(points.findIndex(p=>p.classList.contains('is-active'))+1)%points.length])});
  const container=$('#cards');
  if(container){
    const cards=$$('.card',container),provider=$('#provider'),kind=$('#kind'),sort=$('#sort'),search=$('#search');let shown=9,preset=params.get('lens')||'all';
    if(!['all','special','budget','memory'].includes(preset))preset='all';
    for(const [field,key] of [[provider,'provider'],[kind,'kind'],[sort,'sort']]){const value=params.get(key);if(value&&[...field.options].some(o=>o.value===value))field.value=value}
    search.value=params.get('q')||'';
    function update(reset=true){
      if(reset)shown=9;
      const q=search.value.trim().toLowerCase();
      const matches=cards.filter(c=>(provider.value==='all'||c.dataset.provider===provider.value)&&(kind.value==='all'||c.dataset.kind===kind.value)&&(!q||c.dataset.search.toLowerCase().includes(q))&&(preset!=='budget'||Math.round(Number(c.dataset.monthly)*100)/100<5)&&(preset!=='memory'||Number(c.dataset.ram)>=4)&&(preset!=='special'||c.dataset.kind==='special'));
      matches.sort((a,b)=>sort.value==='price'?Number(a.dataset.monthly)-Number(b.dataset.monthly):sort.value==='memory'?Number(b.dataset.ram)-Number(a.dataset.ram)||Number(a.dataset.monthly)-Number(b.dataset.monthly):Number(a.dataset.index)-Number(b.dataset.index));
      cards.forEach(c=>c.hidden=true);matches.forEach((c,i)=>{c.hidden=i>=shown;container.append(c)});
      $('#result-count').textContent=matches.length+' '+(matches.length===1?'plan matches':'plans match')+' your view';$('#empty').hidden=matches.length!==0;
      $('#load-more-wrap').hidden=matches.length<=shown;$('#visible-count').textContent=Math.min(shown,matches.length)+' OF '+matches.length+' PLANS';
      $$('[data-preset]').forEach(b=>{const active=b.dataset.preset===preset;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))});
      setQuery('q',search.value.trim());setQuery('provider',provider.value==='all'?'':provider.value);setQuery('kind',kind.value==='all'?'':kind.value);setQuery('sort',sort.value==='default'?'':sort.value);setQuery('lens',preset==='all'?'':preset);
    }
    function reset(){provider.value=kind.value='all';sort.value='default';search.value='';preset='all';update();announce('All filters cleared.')}
    $('#filter-form').addEventListener('submit',ev=>ev.preventDefault());
    [provider,kind,sort].forEach(x=>x.addEventListener('change',()=>{if(x===kind&&preset==='special')preset='all';update()}));
    search.addEventListener('input',()=>update());
    $$('[data-preset]').forEach(b=>b.addEventListener('click',()=>{preset=b.dataset.preset;kind.value='all';update()}));
    $('#reset-filters').onclick=reset;$('#reset-empty').onclick=()=>{reset();search.focus()};
    $('#load-more').onclick=()=>{const previous=shown;shown+=9;update(false);const visible=$$('.card:not([hidden])',container);announce('Showing '+visible.length+' plans.');visible[previous]?.querySelector('h3 a')?.focus({preventScroll:true})};
    update();
  }
  if(!matchMedia('(prefers-reduced-motion: reduce)').matches&&'IntersectionObserver'in window){
    const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('revealed');io.unobserve(e.target)}}),{threshold:.07});
    $$('.field-notes,.footer-top').forEach(el=>{if(el.getBoundingClientRect().top>innerHeight){el.classList.add('reveal-ready');io.observe(el)}});
  }
})();
