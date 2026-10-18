/* Python stays in a separate worker; no user data is sent to a server. */
let boot;
async function init() {
  postMessage({type:'progress', message:'Starting the Python engine…'});
  const {loadPyodide} = await import('./pyodide/pyodide.mjs');
  const py = await loadPyodide({indexURL:new URL('./pyodide/',self.location.href).href});
  postMessage({type:'progress', message:'Loading validation rules…'});
  await py.loadPackage('jsonschema');
  const [archiveResponse, bridgeResponse] = await Promise.all([fetch('./engine.zip'), fetch('./bridge.py')]);
  if (!archiveResponse.ok || !bridgeResponse.ok) throw Error('The engine files could not be loaded. Reload and try again.');
  py.unpackArchive(await archiveResponse.arrayBuffer(), 'zip', {extractDir:'/trialtrace-runtime'});
  await py.runPythonAsync("import sys\nsys.path.insert(0, '/trialtrace-runtime')");
  await py.runPythonAsync(await bridgeResponse.text());
  postMessage({type:'ready', runtime:py.version});
  return py;
}
let queue = Promise.resolve();
async function processMessage(data) {
  try {
    boot ??= init();
    const py = await boot;
    if (data.action === 'boot') return;
    py.globals.set('_request_json', JSON.stringify(data.payload));
    const result = JSON.parse(await py.runPythonAsync('handle_json(_request_json)'));
    py.globals.delete('_request_json');
    postMessage({id:data.id,result});
  } catch (error) {
    postMessage({id:data.id, fatal:true, error:String(error.message || error)});
  }
}
self.onmessage = ({data}) => { queue = queue.then(() => processMessage(data)); };
