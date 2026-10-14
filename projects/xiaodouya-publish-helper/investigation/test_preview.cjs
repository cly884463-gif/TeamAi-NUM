const {chromium} = require('C:/Users/20435/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const assert = require('assert/strict');
(async () => {
 const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  const page = await browser.newPage();
  await page.route('**/*', route => route.fulfill({contentType:'text/html',body:'<div data-slate-editor="true" contenteditable="true"></div><video muted></video>'}));
  await page.goto('https://creator.douyin.com/creator-micro/content/post/video');
  const original=fs.readFileSync(__dirname+'/recovered/preview_original.js','utf8');
  const fixed=fs.readFileSync(__dirname+'/recovered/preview_fixed.js','utf8');
  const media=fs.readFileSync(__dirname+'/fixture.mp4').toString('base64');
  await page.evaluate(async data => {
    const video=document.querySelector('video');
    const bytes=Uint8Array.from(atob(data),c=>c.charCodeAt(0));
    video.src=URL.createObjectURL(new Blob([bytes],{type:'video/mp4'}));
    await video.play(); video.pause();
  },media);
  const before=await page.evaluate(original), after=await page.evaluate(fixed);
  assert.equal(before.ready,0);assert.equal(after.ready,1);
  assert.equal(after.editors,1);assert.equal(after.route,'/creator-micro/content/post/video');
  const cases=[
   ['https://example.invalid/video',2,1,1],
   ['blob:https://creator.douyin.com/example',2,1,1],
   ['blob:https://other.invalid/example',2,1,0],
   ['blob:null/example',2,1,0],
   ['file:///test.mp4',2,1,0],
   ['blob:https://creator.douyin.com/example',1,1,0],
   ['blob:https://creator.douyin.com/example',2,0,0],
   ['',2,1,0]
  ];
  for(const [src,ready,duration,expected] of cases){
   await page.evaluate(({src,ready,duration})=>{
    const v=document.querySelector('video');
    for(const [key,value] of Object.entries({currentSrc:src,readyState:ready,duration}))Object.defineProperty(v,key,{configurable:true,value});
   },{src,ready,duration});
   assert.equal((await page.evaluate(fixed)).ready,expected,src);
  }
  await page.evaluate(()=>{const v=document.querySelector('video');for(const k of ['currentSrc','readyState','duration'])delete v[k];document.body.append(v.cloneNode(true));});
  await page.evaluate(async()=>{await Promise.all([...document.querySelectorAll('video')].map(async v=>{await v.play();v.pause();}));});
  assert.equal((await page.evaluate(fixed)).ready,2,'ambiguous preview must not satisfy ready===1');
  fs.writeFileSync(__dirname+'/browser_test_result.json',JSON.stringify({browser:await browser.version(),realBlobPreview:{before:before.ready,after:after.ready},simulatedBoundaryCases:cases.length,multipleRealPreviews:2,livePlatformTest:false},null,2));
  console.log('PASS: real blob video old=0/fixed=1; 8 boundary cases; two-preview ambiguity retained');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
