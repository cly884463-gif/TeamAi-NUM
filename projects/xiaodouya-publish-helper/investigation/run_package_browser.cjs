const {chromium}=require('C:/Users/20435/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const http=require('http'),fs=require('fs'),path=require('path'),{spawn}=require('child_process');
(async()=>{
 const server=http.createServer((req,res)=>{res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(fs.readFileSync(path.join(__dirname,'browser_fixture.html')));});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const profile=fs.mkdtempSync(path.resolve(__dirname,'../build/cdp-profile-'));
 let context;
 try{
  context=await chromium.launchPersistentContext(profile,{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--remote-debugging-port=0']});
  const page=await context.newPage();await page.goto(`http://127.0.0.1:${server.address().port}/creator-micro/content/upload`);
  const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];
  const proc=spawn('F:/AI/CosyVoice3/venv/Scripts/python.exe',[path.join(__dirname,'verify_package_browser.py'),`http://127.0.0.1:${port}/json`],{env:{...process.env,PYTHONUTF8:'1',XCL_PUBLISH_DATA_DIR:path.resolve(__dirname,'../build/component-diagnostics')},windowsHide:true,stdio:'inherit'});
  const code=await new Promise(r=>proc.on('exit',r));if(code!==0)throw Error('Package browser verification failed: '+code);
 }finally{if(context)await context.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
