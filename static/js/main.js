document.addEventListener('DOMContentLoaded',()=>{const t=document.querySelector('.toast');if(t)setTimeout(()=>t.remove(),4500)});

document.addEventListener("DOMContentLoaded",()=>{
  const tabs=[...document.querySelectorAll(".admin-tab")], panels=[...document.querySelectorAll(".admin-panel")];
  if(tabs.length){
    const activate=(name)=>{tabs.forEach(t=>t.classList.toggle("active",t.dataset.tab===name));panels.forEach(p=>p.classList.toggle("active",p.id==="tab-"+name));};
    tabs.forEach(t=>t.addEventListener("click",()=>activate(t.dataset.tab)));
    const h=location.hash.slice(1); if(h && tabs.some(t=>t.dataset.tab===h)) activate(h);
  }
  const toast=document.querySelector(".toast"); if(toast) setTimeout(()=>toast.remove(),4500);
});
