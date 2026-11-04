// SPACE must remain usable even if another workbench module fails to load.
function failed(tool, error) {
  console.error(tool + ' startup failed', error);
  const host = document.createElement('div');
  host.className = 'status';
  host.setAttribute('role', 'alert');
  host.textContent = tool + ' could not start. Reload this BRACE window; if the problem persists, restart BRACE from the launcher. ';
  const retry = document.createElement('button');
  retry.textContent = 'Reload BRACE';
  retry.onclick = () => location.reload();
  host.append(retry);
  document.querySelector('#main').prepend(host);
}
import('./space.js').then(module => module.initSpace()).catch(error => failed('SPACE', error));
import('../app.js').catch(error => failed('Workbench', error));
