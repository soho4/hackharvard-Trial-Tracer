// Real main-app HTTP navigation, CSV upload, server download, native saved-report
// iframe upload, and original File download in an isolated standard Chrome session.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '/Users/yisak/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '../..');
const review = path.join(root, 'docs/trialtrace/review/g3_viewer');
const runId = new Date().toISOString().replaceAll(':','-')+'-'+crypto.randomBytes(4).toString('hex');
const output = path.join(review, 'embedded_runs', runId);
fs.mkdirSync(output,{recursive:true});
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const url = process.env.TRIALTRACE_URL || 'http://127.0.0.1:8501/';
const inputs = path.join(root,'docs/trialtrace/review/g3_challenge/actual_run/inputs');
const roles = [['anchors.csv','unfamiliar-upload-31.csv'],['visits.csv','unfamiliar-upload-32.csv'],['assignments.csv','unfamiliar-upload-33.csv']];
const sourcePdf = process.env.SOURCE_PDF || path.join(root,'../source_check/.sources/Prot_000.pdf');
const sourceHashes = Object.fromEntries(['app.py','features/evidence_viewer/app.js','features/evidence_viewer/contract.js','features/evidence_viewer/style.css'].map(name=>[name,sha(fs.readFileSync(path.join(root,name)))]));
const results = [];
const pageErrors = [];
const consoleErrors = [];
const downloadEvents = [];
let browser;
let page;
let iframeDownloadFailure;

(async()=>{
  browser = await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const context = await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1100}});
  page = await context.newPage();
  page.setDefaultTimeout(30000);
  page.on('pageerror',e=>pageErrors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text());});
  page.on('download',d=>downloadEvents.push({url:d.url(),suggested_filename:d.suggestedFilename()}));
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:'TrialTrace timing checks'}).waitFor();
  await page.getByTestId('stFileUploader').first().waitFor();
  assert.equal(await page.getByTestId('stFileUploader').count(),3);
  for(const [role,name] of roles) {
    const uploader=page.getByTestId('stFileUploader').filter({hasText:role});
    assert.equal(await uploader.count(),1,role+' uploader should be unique');
    await uploader.locator('input[type=file]').setInputFiles(path.join(inputs,name));
    await page.getByRole('button',{name:'Clear '+role,exact:true}).waitFor();
  }
  // Streamlit's styled checkbox covers its native input; click the visible label
  // as a user would, then assert the native checked state (no forced click).
  const confirmation='These are synthetic records; run the unreviewed draft timing check.';
  await page.getByText(confirmation,{exact:true}).click();
  assert.equal(await page.getByRole('checkbox',{name:confirmation,exact:true}).isChecked(),true);
  await page.getByRole('button',{name:'Run timing check',exact:true}).click();
  await page.getByRole('button',{name:'Download evidence JSON',exact:true}).waitFor();
  assert.deepEqual(await page.getByTestId('stMetricValue').allTextContents(),['9','5','7','3']);
  const mainDownloadEvent=page.waitForEvent('download',{timeout:15000});
  await page.getByRole('button',{name:'Download evidence JSON',exact:true}).click();
  const mainDownload=await mainDownloadEvent;
  const mainPath=path.join(output,'main-downloaded.json');
  await mainDownload.saveAs(mainPath); // Preserve bytes immediately; browser tmp files are transient.
  const raw=fs.readFileSync(mainPath);
  const bundle=JSON.parse(raw);
  assert.equal(bundle.findings.length,24);
  assert.deepEqual(bundle.summary.statuses,{PASS:9,POTENTIAL_DEVIATION:5,DATA_QUERY:7,NOT_EVALUABLE:3});
  assert.equal(bundle.review_status,'PENDING_TEAM_SOURCE_REVIEW');
  assert.equal(bundle.clinical_validation,false);
  for(const [role,name] of roles) assert.equal(bundle.input_files.find(f=>f.name===role).sha256,sha(fs.readFileSync(path.join(inputs,name))));
  const cliArgs=['-I','-m','trialtrace.cli','--draft-synthetic'];
  for(const [role,name] of roles) cliArgs.push('--'+role.replace('.csv',''),path.join(inputs,name));
  const cliPath=path.join(output,'cli-generated.json');
  cliArgs.push('--rule',path.join(root,'rules/candidate_rule.json'),'--output',cliPath);
  if(bundle.source.pdf_sha256!==null) cliArgs.push('--source-pdf',sourcePdf);
  const cli=spawnSync(path.join(root,'.venv/bin/python'),cliArgs,{cwd:path.dirname(root),timeout:30000});
  fs.writeFileSync(path.join(output,'cli.stdout.log'),cli.stdout || '');
  fs.writeFileSync(path.join(output,'cli.stderr.log'),cli.stderr || '');
  fs.writeFileSync(path.join(output,'cli.command.json'),JSON.stringify({command:[path.join(root,'.venv/bin/python'),...cliArgs],cwd:path.dirname(root),exit_code:cli.status},null,2)+'\n');
  assert.equal(cli.status,0,cli.stderr?.toString());
  assert.deepEqual(raw,fs.readFileSync(cliPath));
  results.push({case:'Main app uploads 24 synthetic records from actual CSV files, computes and downloads exact CLI bytes',pass:true,counts:[9,5,7,3],output_sha256:sha(raw),bytes:raw.length});
  await page.screenshot({path:path.join(output,'main-24.png'),fullPage:true});

  await page.getByRole('tab',{name:'Open saved evidence report',exact:true}).click();
  const iframeElement=page.locator('iframe[title="st.iframe"]');
  await iframeElement.waitFor();
  assert.equal(await iframeElement.count(),1);
  const frame=page.frameLocator('iframe[title="st.iframe"]');
  const sandbox=await iframeElement.getAttribute('sandbox');
  await frame.locator('#fileInput').setInputFiles(mainPath);
  await frame.locator('#report').waitFor({state:'visible'});
  assert.deepEqual(await frame.locator('.count-value').allTextContents(),['24','9','5','7','3']);
  await frame.locator('.finding').first().click();
  assert.ok((await frame.locator('#detail').innerText()).includes(bundle.findings[0].participant_id));
  assert.ok((await frame.locator('#detail').innerText()).includes('0001-01-08'));
  results.push({case:'Embedded native viewer uploads actual downloaded report and displays all 24 findings',pass:true,sandbox});
  const nativeDownloadEvent=page.waitForEvent('download',{timeout:12000});
  await frame.locator('#downloadButton').click();
  try {
    const nativeDownload=await nativeDownloadEvent;
    const nativePath=path.join(output,'iframe-downloaded.json');
    await nativeDownload.saveAs(nativePath);
    assert.deepEqual(fs.readFileSync(nativePath),raw);
    results.push({case:'Embedded original File download byte matches main app and CLI',pass:true,output_sha256:sha(fs.readFileSync(nativePath)),bytes:fs.statSync(nativePath).size});
  } catch(error) {
    iframeDownloadFailure=String(error);
    results.push({case:'Embedded original File download',pass:false,error:iframeDownloadFailure});
  }
  await page.screenshot({path:path.join(output,'iframe-24.png'),fullPage:true});

  // Dismiss the desktop sidebar through its real control before narrowing; an
  // open drawer intentionally overlays mobile content and is not a layout test.
  await page.getByTestId('stSidebar').hover();
  await page.getByTestId('stSidebarCollapseButton').getByRole('button').click();
  await page.getByRole('button',{name:'Expand sidebar',exact:true}).waitFor({state:'visible'});
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(()=>{
    const sidebar=document.querySelector('[data-testid="stSidebar"]');
    return !sidebar || sidebar.getBoundingClientRect().right<=1;
  });
  await frame.locator('h1').scrollIntoViewIfNeeded();
  const narrow=await frame.locator('body').evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth}));
  assert.ok(narrow.scroll<=narrow.viewport,JSON.stringify(narrow));
  results.push({case:'Embedded iframe at narrow main-app viewport',pass:true,...narrow});
  await page.screenshot({path:path.join(output,'iframe-narrow.png'),fullPage:true});
  await page.emulateMedia({media:'print'});
  assert.equal(await frame.locator('#downloadButton').isVisible(),false);
  const print=await frame.locator('.columns').evaluate(el=>({columns:getComputedStyle(el).gridTemplateColumns,controls:getComputedStyle(document.querySelector('.no-print')).display,printMedia:matchMedia('print').matches}));
  assert.equal(print.printMedia,true);
  assert.equal(print.controls,'none');
  assert.equal(print.columns.trim().split(/\s+/).length,1);
  results.push({case:'Embedded print media applies one-column layout and hides controls',pass:true,...print,limitation:'OS/native print dialog not exercised; no claim iframe PDF pagination is complete'});
  await page.emulateMedia({media:'screen'});
  await page.setViewportSize({width:1440,height:1100});

  for(const name of ['invalid_status.json','invalid_duplicate_id.json','invalid_evidence_hash.json']) {
    await frame.locator('#fileInput').setInputFiles(mainPath);
    await frame.locator('#report').waitFor({state:'visible'});
    await frame.locator('#fileInput').setInputFiles(path.join(root,'features/evidence_viewer/fixtures',name));
    await frame.locator('#errorBox').waitFor({state:'visible'});
    assert.equal(await frame.locator('#report').isVisible(),false);
    assert.equal(await frame.locator('#downloadButton').isDisabled(),true);
    assert.equal(await frame.locator('#runId').innerText(),'');
    assert.equal(await frame.locator('.count-value').count(),0);
    results.push({case:'Embedded invalid replacement '+name,pass:true,error:await frame.locator('#errorList').innerText()});
  }
  assert.deepEqual(pageErrors,[]);
  for(const [name,digest] of Object.entries(sourceHashes)) assert.equal(sha(fs.readFileSync(path.join(root,name))),digest,'Source changed during embedded browser check');
  const result={status:iframeDownloadFailure?'FAIL':'PASS',run_id:runId,url,browser:await browser.version(),browser_mode:'Separate headless Chrome context, actual served main app and real uploads/downloads',source_sha256:sourceHashes,cases:results,download_events:downloadEvents,page_errors:pageErrors,console_errors:consoleErrors,scope:'Standard installed Chrome only; IAB platform behavior is separately recorded by root.',artifacts:path.relative(root,output)};
  const text=JSON.stringify(result,null,2)+'\n';
  fs.writeFileSync(path.join(output,'result.json'),text);
  fs.writeFileSync(path.join(review,'embedded_result.json'),text);
  console.log(text);
  assert.equal(iframeDownloadFailure,undefined,iframeDownloadFailure);
})().catch(async error=>{
  if(page) {try{await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});}catch{}}
  fs.writeFileSync(path.join(output,'failure.json'),JSON.stringify({status:'FAIL',error:String(error),stack:error.stack,cases:results,page_errors:pageErrors,console_errors:consoleErrors,download_events:downloadEvents},null,2)+'\n');
  console.error(error); process.exitCode=1;
}).finally(async()=>{if(browser) await browser.close();});
