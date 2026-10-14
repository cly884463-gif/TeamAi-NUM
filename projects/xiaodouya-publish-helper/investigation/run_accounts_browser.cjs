const {chromium}=require('C:/Users/20435/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{spawn}=require('child_process');
(async()=>{
 const profile=fs.mkdtempSync(path.resolve(__dirname,'../build/account-profile-'));
 const context=await chromium.launchPersistentContext(profile,{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--remote-debugging-port=0']});
 try{
  const page=await context.newPage();await page.setContent(fs.readFileSync(path.join(__dirname,'account_fixture.html'),'utf8'));
  const port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];
  const script=process.argv[3]==='loading'?'verify_account_loading.py':'verify_accounts_browser.py';
  const child=spawn('F:/AI/CosyVoice3/venv/Scripts/python.exe',[path.join(__dirname,script),`http://127.0.0.1:${port}/json`,process.argv[2]||'r11',process.argv[4]||'normal'],{env:{...process.env,PYTHONUTF8:'1',XCL_PUBLISH_DATA_DIR:path.resolve(__dirname,'../build/account-diagnostics')},windowsHide:true,stdio:'inherit'});
  const code=await new Promise(r=>child.on('exit',r));if(code!==0)throw Error('Verification failed: '+code);
 }finally{await context.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
