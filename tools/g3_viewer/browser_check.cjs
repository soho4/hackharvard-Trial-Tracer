// Actual HTTP navigation, native file input uploads and browser downloads.
// No application functions or fixture responses are injected into the page.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {spawn} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '/Users/yisak/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'docs/trialtrace/review/g3_viewer');
const fixture = name => path.join(__dirname, 'native_snapshot/fixtures', name);
const engine = name => path.join(root, 'examples/execution', name, 'bundle.json');
const input = name => path.join(output, 'inputs', name);
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = [];
const errors = [];
const consoleMessages = [];
let browser;
const port = Number(process.env.VIEWER_PORT || 18765);
const serverLog = fs.openSync(path.join(output, 'server.log'), 'w');
const server = spawn(path.join(root, '.venv/bin/python'), ['-m','http.server',String(port),'--bind','127.0.0.1','--directory',path.join(__dirname,'candidate')], {stdio:['ignore',serverLog,serverLog]});

(async () => {
  let ready = false;
  for (let i=0; i<50; i++) {
    try { ready=(await fetch(`http://127.0.0.1:${port}/`,{signal:AbortSignal.timeout(1500)})).ok; } catch {}
    if(ready) break;
    await sleep(100);
  }
  assert.equal(ready,true,'localhost viewer did not start');
  browser=await chromium.launch({headless:true, executablePath:process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const context=await browser.newContext({acceptDownloads:true,viewport:{width:1365,height:1000}});
  const page=await context.newPage();
  page.on('pageerror', e=>errors.push(String(e)));
  page.on('console', m=>{if(m.type()==='error') consoleMessages.push(m.text());});
  await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'networkidle'});
  assert.equal(await page.title(),'TrialTrace Evidence Viewer');
  assert.equal(await page.locator('#downloadButton').isDisabled(),true);
  const upload=async file=>{
    await page.locator('#fileInput').setInputFiles(file);
    await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Loaded ') || document.querySelector('#status').textContent.startsWith('The selected file was rejected.'));
  };
  const counts=async()=>await page.locator('.count-value').allTextContents();
  const expectCounts=async expected=>assert.deepEqual(await counts(),expected.map(String));

  await upload(engine('before'));
  await expectCounts([1,1,0,0,0]);
  assert.equal(await page.locator('#report').isVisible(),true);
  await page.locator('.finding').click();
  assert.match(await page.locator('#detail').innerText(),/2032-01-03 to 2032-01-06/);
  assert.match(await page.locator('#detail').innerText(),/SYNTH-RIVER-41/);
  assert.match(await page.locator('#detail').innerText(),/assignments.csv/);
  const expected=JSON.parse(fs.readFileSync(engine('before'),'utf8'));
  for(const file of expected.input_files) assert.ok((await page.locator('#inputFiles').innerText()).includes(file.sha256));
  assert.match(await page.locator('#provenance').innerText(),/declared, not verified/);
  results.push({case:'actual CLI before report and selected raw evidence',pass:true,counts:[1,1,0,0,0]});
  const engineDownloadEvent=page.waitForEvent('download');
  await page.locator('#downloadButton').click();
  const engineDownload=await engineDownloadEvent;
  const engineDownloaded=path.join(output,'downloaded-engine-original.json');
  await engineDownload.saveAs(engineDownloaded);
  assert.deepEqual(fs.readFileSync(engineDownloaded),fs.readFileSync(engine('before')));
  results.push({case:'actual CLI original-byte download',pass:true,sha256:hash(fs.readFileSync(engineDownloaded))});
  await page.screenshot({path:path.join(output,'viewer-engine-wide.png'),fullPage:true});

  await upload(engine('after'));
  await expectCounts([1,0,1,0,0]);
  await page.locator('.finding').click();
  assert.match(await page.locator('#detail').innerText(),/2032-01-07/);
  results.push({case:'actual CLI changed-date report',pass:true,counts:[1,0,1,0,0]});

  for(const [name,values] of [['missing_anchor',[1,0,0,1,0]],['wrong_person',[1,0,0,1,0]],['unknown_event',[1,0,0,0,1]],['empty_visits',[0,0,0,0,0]]]) {
    await upload(engine(name)); await expectCounts(values);
    if(name==='empty_visits') assert.match(await page.locator('#findingList').innerText(),/does not establish trial compliance/);
    else {await page.locator('.finding').click(); assert.match(await page.locator('#detail').innerText(),/No timing conclusion supplied/);}
    results.push({case:'actual CLI '+name,pass:true,counts:values});
  }

  for(const [name,values,date] of [['early0001',[1,1,0,0,0],'0001-01-11'],['leap0004',[1,1,0,0,0],'0004-02-29'],['early0099',[1,0,1,0,0],'0099-12-31']]) {
    await upload(input(name+'/bundle.json')); await expectCounts(values);
    await page.locator('.finding').click();
    assert.ok((await page.locator('#detail').innerText()).includes(date));
    results.push({case:'new real CLI '+name,pass:true,counts:values});
  }

  await upload(fixture('mixed.json')); await expectCounts([4,1,1,1,1]);
  await page.locator('#statusFilter').selectOption('DATA_QUERY');
  assert.equal(await page.locator('.finding').count(),1);
  assert.equal(await page.locator('#shownLine').innerText(),'1 shown / 4 findings in report');
  await expectCounts([4,1,1,1,1]);
  await page.locator('#statusFilter').selectOption('ALL');
  await page.locator('#searchInput').fill('demo-p002');
  assert.equal(await page.locator('.finding').count(),1);
  assert.match(await page.locator('.finding').innerText(),/fixture-f-2/);
  const downloadEvent=page.waitForEvent('download');
  await page.locator('#downloadButton').click();
  const download=await downloadEvent;
  const downloaded=path.join(output,'downloaded-original.json');
  await download.saveAs(downloaded);
  assert.deepEqual(fs.readFileSync(downloaded),fs.readFileSync(fixture('mixed.json')));
  results.push({case:'filter, search and original-byte download',pass:true,sha256:hash(fs.readFileSync(downloaded))});

  const rejects=[fixture('invalid_status.json'),fixture('invalid_duplicate_id.json'),fixture('invalid_evidence_hash.json'),input('unknown_schema.json'),input('broken.json'),input('oversized.json')];
  for(const file of rejects) {
    await upload(engine('before')); await expectCounts([1,1,0,0,0]);
    await upload(file);
    assert.equal(await page.locator('#report').isVisible(),false);
    assert.equal(await page.locator('#downloadButton').isDisabled(),true);
    assert.equal(await page.locator('#runId').innerText(),'');
    assert.equal(await page.locator('.count-value').count(),0);
    assert.equal(await page.locator('#errorBox').isVisible(),true);
    results.push({case:'invalid replacement '+path.basename(file),pass:true,error:await page.locator('#errorList').innerText()});
  }

  await upload(fixture('markup.json'));
  await page.locator('.finding').first().click();
  assert.match(await page.locator('#detail').innerText(),/<script>window.__unexpected_script_ran=true<\/script>/);
  assert.equal(await page.locator('#detail img').count(),0);
  assert.equal(await page.evaluate(()=>typeof window.__unexpected_script_ran),'undefined');
  assert.equal(await page.locator('#provenance a').count(),0);
  assert.match(await page.locator('#provenance').innerText(),/Link disabled/);
  results.push({case:'markup remains literal and unsafe source link disabled',pass:true});

  await upload(engine('before')); await page.locator('.finding').click();
  await page.setViewportSize({width:390,height:844});
  const narrow=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflowing:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth).map(el=>({tag:el.tagName,id:el.id,class:el.className,width:el.getBoundingClientRect().width,right:el.getBoundingClientRect().right,text:el.textContent.slice(0,120)}))}));
  await page.screenshot({path:path.join(output,'viewer-engine-narrow.png'),fullPage:true});
  fs.writeFileSync(path.join(output,'narrow_layout.json'),JSON.stringify(narrow,null,2)+'\n');
  assert.ok(narrow.scroll<=narrow.viewport,JSON.stringify(narrow));
  results.push({case:'native 390-pixel viewport',pass:true,...narrow});
  const longName='long-report-name-'+ 'x'.repeat(210) + '.json';
  fs.copyFileSync(engine('before'),input(longName));
  await upload(input(longName)); await page.locator('.finding').click();
  const longNameLayout=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert.ok(longNameLayout.scroll<=longNameLayout.viewport,JSON.stringify(longNameLayout));
  results.push({case:'long filename and 64-character engine IDs at narrow viewport',pass:true,...longNameLayout});
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('#downloadButton').isVisible(),false);
  await page.pdf({path:path.join(output,'viewer-print.pdf'),format:'A4',printBackground:true});
  results.push({case:'Chrome print media and PDF rendering',pass:true,limitation:'OS print dialog not opened'});
  assert.deepEqual(errors,[]);
  const result={status:'PASS',browser:await browser.version(),browser_mode:'headless isolated context; actual HTTP navigation and filesystem uploads',cases:results,page_errors:errors,console_errors:consoleMessages,limits:['This run tests the separate viewer, not the Streamlit main upload UI.','No source interpretation or human review acceptance.','Print output generated by Chrome PDF API; no OS dialog was opened.']};
  fs.writeFileSync(path.join(output,'browser_results.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
})().catch(error=>{
  fs.writeFileSync(path.join(output,'browser_results_failed_'+Date.now()+'.json'),JSON.stringify({status:'FAIL',completed_cases:results,error:String(error),stack:error.stack,page_errors:errors,console_errors:consoleMessages},null,2)+'\n');
  console.error(error); process.exitCode=1;
}).finally(async()=>{if(browser) await browser.close(); server.kill('SIGTERM'); fs.closeSync(serverLog);});
