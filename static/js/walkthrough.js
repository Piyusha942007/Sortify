// --- CONFIG ---------------------------------------------------
const EMAILS = [
  { from: "Amit Verma",   email: "amit@workcorp.com",     subject: "Sprint Update & Next Steps",       time: "10:12 AM", domain: "workcorp.com" },
  { from: "Your College", email: "office@univ.edu",       subject: "Exam Schedule – Semester 1",       time: "09:01 AM", domain: "univ.edu" },
  { from: "Figma",        email: "noreply@figma.com",     subject: "Your weekly design digest",        time: "Yesterday", domain: "figma.com" },
  { from: "HR Team",      email: "hr@workcorp.com",       subject: "Policy acknowledgement reminder",  time: "Mon",      domain: "workcorp.com" },
  { from: "YouTube",      email: "digest@youtube.com",    subject: "New videos you may like",          time: "Sun",      domain: "youtube.com" },
  { from: "Prof. Rao",    email: "rao@univ.edu",          subject: "Lab assignment feedback",          time: "11:44 AM", domain: "univ.edu" },
  { from: "GitHub",       email: "noreply@github.com",    subject: "Security alert on repo",           time: "08:20 AM", domain: "github.com" },
  { from: "WorkCorp IT",  email: "it@workcorp.com",       subject: "VPN maintenance window",           time: "Sat",      domain: "workcorp.com" },
  { from: "Medium",       email: "news@medium.com",       subject: "Top tech stories this week",       time: "Fri",      domain: "medium.com" }
];

// Folders we will render + the domains that drop in
const FOLDER_DEFS = [
  { name: "Work",          color: 0xffd166, domains: ["workcorp.com"] },
  { name: "College",       color: 0x8ecae6, domains: ["univ.edu"] },
  { name: "Subscriptions", color: 0xcdb4db, domains: ["figma.com", "youtube.com", "github.com", "medium.com"] },
];

// Animation timings
const FLOAT_TIME   = 2500;   // milliseconds before organizing starts
const MOVE_TIME    = 1400;   // fly time to folder
const STACK_OFFSET = 0.12;   // stacking offset inside folder

// --- THREE CORE -----------------------------------------------
let scene, camera, renderer;
let emails = [];   // {mesh, data}
let folders = [];  // {group, mouth, stackCount, def}

// EASING
function easeOutCubic(t){ return 1 - Math.pow(1 - t, 3); }

function initThree() {
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    200
  );
  camera.position.set(0, 2.2, 16);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x000000, 0); // transparent, we use CSS gradient bg
  document.getElementById("walkthrough-container").appendChild(renderer.domElement);

  // Lights: soft + directional for a clean, airy look
  const ambient = new THREE.AmbientLight(0xffffff, 0.85);
  scene.add(ambient);
  const dir = new THREE.DirectionalLight(0xffffff, 0.95);
  dir.position.set(5, 10, 7);
  scene.add(dir);

  // Subtle environment box (very faint)
  const env = new THREE.Mesh(
    new THREE.BoxGeometry(60, 30, 60),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.02, side: THREE.BackSide })
  );
  scene.add(env);
}

// --- EMAIL CARD TEXTURE ---------------------------------------
function makeEmailTexture({from, email, subject, time}) {
  const w = 600, h = 280;
  const cvs = document.createElement('canvas');
  cvs.width = w; cvs.height = h;
  const ctx = cvs.getContext('2d');

  // card bg
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);
  // subtle border + shadow-ish edge
  ctx.strokeStyle = "#e6eaf5";
  ctx.lineWidth = 4;
  ctx.strokeRect(2, 2, w-4, h-4);

  // left accent bar (domain-ish)
  ctx.fillStyle = "#4169e1";
  ctx.fillRect(0, 0, 10, h);

  // text
  ctx.fillStyle = "#111827";
  ctx.font = "bold 42px Inter, Arial";
  ctx.fillText(from, 26, 70);

  ctx.fillStyle = "#6b7280";
  ctx.font = "28px Inter, Arial";
  ctx.fillText(email, 26, 112);

  ctx.fillStyle = "#111827";
  ctx.font = "32px Inter, Arial";
  const subj = subject.length > 40 ? subject.slice(0, 37) + "…" : subject;
  ctx.fillText(subj, 26, 170);

  ctx.fillStyle = "#6b7280";
  ctx.font = "26px Inter, Arial";
  ctx.fillText(time, w-130, 50);

  return new THREE.CanvasTexture(cvs);
}

function createEmailCard(data) {
  const tex = makeEmailTexture(data);
  tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.55, metalness: 0.08 });
  const geo = new THREE.PlaneGeometry(2.6, 1.2); // aspect like a mail card
  const mesh = new THREE.Mesh(geo, mat);

  // random start positions (inbox chaos)
  mesh.position.set(
    (Math.random() - 0.5) * 14,
    (Math.random() - 0.5) * 6 + 1,
    (Math.random() - 0.5) * 10
  );
  mesh.rotation.set(
    (Math.random() - 0.5) * 0.35,
    (Math.random() - 0.5) * 0.35,
    (Math.random() - 0.5) * 0.35
  );

  scene.add(mesh);
  return { mesh, data };
}

// --- FOLDER (box + tab + label sprite) ------------------------
function makeLabelSprite(text) {
  const w = 512, h = 192;
  const cvs = document.createElement('canvas');
  cvs.width = w; cvs.height = h;
  const ctx = cvs.getContext('2d');

  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#111827";
  ctx.font = "bold 64px Inter, Arial";
  const tw = ctx.measureText(text).width;
  ctx.fillText(text, (w - tw)/2, 120);

  const tex = new THREE.CanvasTexture(cvs);
  const mat = new THREE.SpriteMaterial({ map: tex, depthWrite: false });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(3.2, 1.2, 1);
  return sprite;
}

function createFolder(def, x) {
  const group = new THREE.Group();

  // main box
  const box = new THREE.Mesh(
    new THREE.BoxGeometry(4.0, 2.2, 2.2),
    new THREE.MeshStandardMaterial({
      color: def.color,
      roughness: 0.4,
      metalness: 0.3,
      transparent: true,
      opacity: 0.92
    })
  );
  // tab
  const tab = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, 0.5, 0.2),
    new THREE.MeshStandardMaterial({
      color: def.color,
      roughness: 0.35,
      metalness: 0.35
    })
  );
  tab.position.set(-1.0, 1.4, 1.1);

  // label above
  const label = makeLabelSprite(def.name);
  label.position.set(0, 2.3, 0);

  group.add(box);
  group.add(tab);
  group.add(label);

  group.position.set(x, -2.8, -4.5);
  scene.add(group);

  // "mouth" position where emails should fly to
  const mouth = new THREE.Vector3(x, -2.1, -3.5);

  return { group, mouth, stackCount: 0, def };
}

// Pick folder by email domain
function getFolderForDomain(domain) {
  return folders.find(f => f.def.domains.includes(domain)) || folders[folders.length-1];
}

// --- ANIMATION HELPERS ----------------------------------------
function tweenPosition(mesh, from, to, duration, onDone) {
  const start = performance.now();
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const e = easeOutCubic(t);
    mesh.position.lerpVectors(from, to, e);
    if (t < 1) { requestAnimationFrame(step); }
    else if (onDone) onDone();
  }
  requestAnimationFrame(step);
}

function floatEmails(dt) {
  // small idle float
  emails.forEach((e, i) => {
    e.mesh.rotation.z += 0.002;
    e.mesh.position.y += Math.sin(performance.now() * 0.001 + i) * 0.0009;
  });
}

// --- SETUP SCENE CONTENT --------------------------------------
function buildScene() {
  // emails
  EMAILS.forEach(data => emails.push(createEmailCard(data)));

  // folders (left-center-right)
  const spacing = 6.4;
  const startX = -spacing;
  FOLDER_DEFS.forEach((def, i) => {
    folders.push(createFolder(def, startX + i * spacing));
  });

  // titles progression
  setTimeout(() => {
    document.getElementById("title").textContent = "Applying Rules ⚡";
    document.getElementById("subtitle").textContent = "Sorting by domains into folders…";
    organizeAll();
  }, FLOAT_TIME);

  setTimeout(() => {
    document.getElementById("title").textContent = "Organized 📂";
    document.getElementById("subtitle").textContent = "Neat stacks by Work, College & Subscriptions";
  }, FLOAT_TIME + MOVE_TIME + 500);
}

// Move each email to its folder mouth, then slide inside & stack
function organizeAll() {
  emails.forEach((e, idx) => {
    const folder = getFolderForDomain(e.data.domain);
    const mouth  = folder.mouth.clone();

    // slight staggering
    const delay = 80 * idx;
    setTimeout(() => {
      const startPos = e.mesh.position.clone();
      // fly to mouth
      tweenPosition(e.mesh, startPos, mouth, MOVE_TIME, () => {
        // rotate flat and slide in a bit
        e.mesh.rotation.set(0, 0, 0);
        const inPos = mouth.clone();
        const layer = folder.stackCount++;
        inPos.z -= 0.7 + layer * STACK_OFFSET;
        inPos.y -= Math.min(0.9, layer * 0.03);
        tweenPosition(e.mesh, mouth, inPos, 500);
      });
    }, delay);
  });
}

// --- RENDER LOOP & RESIZE -------------------------------------
function animate() {
  requestAnimationFrame(animate);
  floatEmails();
  renderer.render(scene, camera);
}

function onResize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // crisp but safe
}

// --- BOOT -----------------------------------------------------
function boot() {
  initThree();
  buildScene();
  animate();
  window.addEventListener('resize', onResize);
}

boot();

// Enter Site button → go to main site
document.getElementById("enter-site").addEventListener("click", () => {
  window.location.href = "/dashboard";  // Flask route to index.html
});

