const video = document.querySelector('#video');
const canvas = document.querySelector('#canvas');
const statusBox = document.querySelector('#status');
const action = document.querySelector('#action');
const username = document.querySelector('#username');
const instructions = document.querySelector('#instructions');
let mode = 'login';

function status(message, bad = false) {
  statusBox.textContent = message;
  statusBox.className = bad ? 'bad' : 'good';
}

async function camera() {
  try {
    video.srcObject = await navigator.mediaDevices.getUserMedia({video: {width: 640, height: 480}, audio: false});
  } catch (_) {
    status('Camera access was blocked. Allow camera permission and reload.', true);
  }
}

function frame() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.82);
}

function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function post(url, data = {}) {
  const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Request failed.');
  return body;
}

function showDashboard(name) {
  document.querySelector('#auth-card').hidden = true;
  document.querySelector('#dashboard').hidden = false;
  document.querySelector('#who').textContent = name;
}

document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
  mode = tab.dataset.mode;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x === tab));
  action.textContent = mode === 'login' ? 'Start login' : 'Enroll face';
  instructions.textContent = mode === 'login' ? 'Look straight at the camera with your eyes open.' : 'Keep one face centered. We will capture three frames.';
  status('');
}));

action.addEventListener('click', async () => {
  if (!username.value.trim()) return status('Enter a username first.', true);
  action.disabled = true;
  try {
    if (mode === 'enroll') {
      const frames = [];
      for (let i = 3; i > 0; i--) {
        status(`Capturing frame ${4 - i} of 3…`);
        await wait(700);
        frames.push(frame());
      }
      const result = await post('/api/enroll', {username: username.value, frames});
      status(result.message);
    } else {
      status('Capturing open-eyes frame…');
      await wait(800);
      const openFrame = frame();
      instructions.textContent = 'Blink now and hold your eyes closed briefly.';
      status('Blink now…');
      await wait(1000);
      const blinkFrame = frame();
      const result = await post('/api/login', {username: username.value, open_frame: openFrame, blink_frame: blinkFrame});
      status(result.message);
      showDashboard(result.username);
    }
  } catch (error) {
    status(error.message, true);
  } finally {
    action.disabled = false;
    if (mode === 'login') instructions.textContent = 'Look straight at the camera with your eyes open.';
  }
});

document.querySelector('#logout').addEventListener('click', async () => {
  await post('/api/logout');
  document.querySelector('#dashboard').hidden = true;
  document.querySelector('#auth-card').hidden = false;
  status('Logged out.');
});

fetch('/api/session').then(r => r.json()).then(s => { if (s.authenticated) showDashboard(s.username); });
camera();
