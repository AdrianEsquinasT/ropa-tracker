/* Botón "+ A mi cesta": se ejecuta en la ficha de producto que ya tienes abierta.
   Solo lee lo que la página muestra (datos estructurados, metaetiquetas y el propio
   contenido visible). No hace peticiones a la tienda ni a terceros: abre tu cesta
   con los datos en el fragmento (#) de la URL, que tampoco viaja a ningún servidor. */
(function(){
var APP="__APP__";
function T(e){return((e&&(e.innerText||e.textContent))||"").replace(/\s+/g," ").trim()}
function M(k){var m=document.querySelector('meta[property="'+k+'"],meta[name="'+k+'"],meta[itemprop="'+k+'"]');return m?(m.getAttribute("content")||""):""}
function N(v){if(v==null)return null;v=String(v).replace(/[^\d,.]/g,"");if(!v)return null;
 if(v.indexOf(",")>-1&&v.indexOf(".")>-1)v=v.lastIndexOf(",")>v.lastIndexOf(".")?v.replace(/\./g,"").replace(",","."):v.replace(/,/g,"");
 else v=v.replace(",",".");var n=parseFloat(v);return isFinite(n)&&n>0&&n<100000?Math.round(n*100)/100:null}
/* 1. Datos estructurados (schema.org Product), los que usan la mayoría de tiendas */
var LD=[];[].forEach.call(document.querySelectorAll('script[type="application/ld+json"]'),function(s){try{
 (function w(o){if(!o||typeof o!="object")return;if(Array.isArray(o))return o.forEach(w);
  var t=[].concat(o["@type"]||[]);if(t.indexOf("Product")>-1||t.indexOf("ProductGroup")>-1)LD.push(o);
  if(o["@graph"])w(o["@graph"])})(JSON.parse(s.textContent))}catch(e){}});
var P=LD[0]||{};
function offers(o){var f=o&&o.offers;if(!f)return[];f=[].concat(f);var r=[];
 f.forEach(function(x){if(x&&x.offers)r=r.concat([].concat(x.offers));r.push(x)});return r}
function avail(x){var a=String((x&&x.availability)||"");return a?!/OutOfStock|SoldOut|Discontinued/i.test(a):true}
var OF=offers(P);
/* 2. Nombre, precio, foto y descripción */
var name=P.name||M("og:title")||T(document.querySelector("h1"))||document.title;
name=String(name).split(" | ")[0].trim();
var up=(name.match(/[A-ZÁÉÍÓÚÑ]/g)||[]).length,lo=(name.match(/[a-záéíóúñ]/g)||[]).length;
if(name.length>3&&up>lo*2)name=name.charAt(0).toUpperCase()+name.slice(1).toLowerCase();
var price=null;OF.some(function(x){price=N(x.price!=null?x.price:x.lowPrice);return price});
if(!price)price=N(M("product:price:amount")||M("og:price:amount")||M("price"));
if(!price){var pe=document.querySelector('[itemprop="price"]');if(pe)price=N(pe.getAttribute("content")||T(pe))}
var PRE=/\d{1,5}(?:[.,]\d{3})*[.,]\d{2}/;
function cls(e){var c=e.className;return String(c&&c.baseVal!=null?c.baseVal:c||"")}
function struck(e){for(var i=0;e&&i<3;i++,e=e.parentElement){var cs=getComputedStyle(e);
 if(/line-through/.test(cs.textDecorationLine||cs.textDecoration||""))return true;
 if(/^(DEL|S|STRIKE)$/.test(e.tagName)||/old|original|crossed|before|compare|strike|tachad|anterior|was/i.test(cls(e)))return true}return false}
var LEAF=[];[].forEach.call(document.querySelectorAll('[class*="price" i],[class*="precio" i],[data-qa*="price" i],[itemprop="price"],del,s,strike'),function(e){
 [e].concat([].slice.call(e.querySelectorAll("*"))).forEach(function(k){
  if(LEAF.indexOf(k)<0&&PRE.test(T(k))&&![].some.call(k.querySelectorAll("*"),function(z){return PRE.test(T(z))}))LEAF.push(k)})});
var now=null,orig=null;
LEAF.forEach(function(e){var n=N(T(e).match(PRE)[0]);if(!n)return;if(struck(e)){if(!orig)orig=n}else if(!now)now=n});
if(!price)price=now;
if(orig&&!(price&&orig>price))orig=null;
var img=P.image;if(Array.isArray(img))img=img[0];if(img&&typeof img=="object")img=img.url||img.contentUrl;
var ogi=M("og:image")||M("twitter:image");if(/\.svg(\?|$)|logo/i.test(ogi))ogi="";   /* algunas tiendas anuncian su logo */
if(!img){var ip=document.querySelector('[itemprop="image"]');if(ip)img=ip.getAttribute("content")||ip.getAttribute("data-src")||ip.currentSrc||ip.getAttribute("src")}
img=img||ogi;
if(!img){var big=null,a=0;[].forEach.call(document.images,function(i){var s=i.naturalWidth*i.naturalHeight;if(s>a&&i.offsetParent){a=s;big=i}});img=big&&(big.currentSrc||big.src)}
try{img=img?new URL(img,location.href).href:""}catch(e){img=""}
var desc=(P.description||M("og:description")||M("description")||"").replace(/\s+/g," ").trim();
if(desc.length>220)desc=desc.slice(0,217).replace(/\s\S*$/,"")+"…";
/* 3. Tallas (o ml / mm) y si quedan */
var RE=/^(XXXS|XXS|XS|S|M|L|XL|XXL|XXXL|\d{2}(?:[.,]5)?|\d{2,3}\s?ml|\d{2}\s?mm|T\.?U\.?|U)$/i,SZ=[],seen={};
function add(v,ok,pr,strict){v=String(v||"").replace(/\s+/g," ").trim();if(!v||!RE.test(v))return;var k=v.toUpperCase().replace(",",".");
 if(seen[k]){seen[k][1]=strict?seen[k][1]&&!!ok:seen[k][1]||!!ok;return}seen[k]=[v.replace(",","."),!!ok,pr||null];SZ.push(seen[k])}
LD.forEach(function(o){[].concat(o.hasVariant||[]).forEach(function(v){var s=v.size&&(v.size.name||v.size)||"";
  if(!s&&v.name){var m=String(v.name).match(/(?:^|[\s\-\/])((?:X{0,3}S|M|X{0,3}L|\d{2}(?:[.,]5)?|\d{2,3}\s?ml))\s*$/i);s=m&&m[1]}
  var o=offers(v);add(s,o.some(avail)||!o.length,o.length?N(o[0].price):null)})});
OF.forEach(function(x){var s=x.size||(x.itemOffered&&x.itemOffered.size)||x.name;if(s&&typeof s=="object")s=s.name;add(s,avail(x))});
function isBad(e){if(!e||e.nodeType!==1)return false;
 return !!(e.disabled||e.getAttribute("aria-disabled")=="true"||e.getAttribute("data-disabled")=="true"||
  /no disponible|agotad|sin stock|out of stock|unavailable/i.test(e.getAttribute("data-stock")||e.getAttribute("data-availability")||"")||
  /disabled|unavailable|out-?of-?stock|sold|agotad|no-?stock/i.test(cls(e)))}
if(!SZ.length)[].forEach.call(document.querySelectorAll('[class*="size" i],[class*="talla" i],[id*="size" i],[data-qa*="size" i],[aria-label*="talla" i]'),function(box){
 [].forEach.call(box.querySelectorAll("button,li,label,option,a,span,div"),function(e){
  if(e.children.length>2)return;var t=T(e).replace(/\b(agotad[oa]s?|pocas unidades|últimas unidades|avísame|sin stock|out of stock|disponible)\b.*$/i,"").trim();
  if(!RE.test(t))return;
  var bad=isBad(e)||isBad(e.parentElement)||[].some.call(e.querySelectorAll("*"),isBad)||/agotad|avísame|sin stock|out of stock/i.test(T(e));
  add(t,!bad,null,true)})});
/* selectores de talla marcados por atributo (p. ej. data-type="select-size"), con su disponibilidad */
[].forEach.call(document.querySelectorAll('[data-type*="size" i],[data-attr-value][data-attr-display-value]'),function(e){
 var v=e.getAttribute("data-attr-value")||T(e);if(!RE.test(String(v).trim()))return;
 add(v,!(isBad(e)||isBad(e.parentElement)),null,true)});
SZ=SZ.slice(0,30);
var all=(name+" "+desc+" "+T(document.body).slice(0,30000));
var ml=(name+" "+desc).match(/(\d{2,3})\s?ml\b/i);ml=ml?ml[1]:(SZ.filter(function(s){return/ml$/i.test(s[0])}).map(function(s){return s[0].replace(/\s?ml/i,"")}).join("/")||"");
var mm=all.match(/(\d{2}(?:[.,]\d)?)\s?mm\b/i);mm=mm?mm[1].replace(",","."):"";
var canon=document.querySelector('link[rel="canonical"]');
function clean(u){try{var x=new URL(u);["fbclid","gclid","igshid","media_type","mc_cid","mc_eid"].forEach(function(k){x.searchParams.delete(k)});
 Array.from(x.searchParams.keys()).forEach(function(k){if(/^utm_/i.test(k))x.searchParams.delete(k)});x.hash="";return x.href}catch(e){return u}}
var D={u:clean(location.href),c:canon&&canon.href||"",n:name.slice(0,140),p:price,op:orig,img:img,d:desc,sz:SZ,ml:ml,mm:mm,
 k:/\b(eau de|parfum|perfume|colonia|edt|edp|eau fra[iî]che|fragancia)\b/i.test(name+" "+desc)?"perfumes":
  /\b(reloj|watch|cron[oó]grafo|smartwatch)\b/i.test(name+" "+desc)?"relojes":""};
var url=APP+"#add="+encodeURIComponent(JSON.stringify(D));
var w=window.open(url,"_blank");if(!w)location.href=url;
})();
