// ===== DEMO USERS =====
const DEMO_USERS = [
  { username: 'angel', password: 'angel123' },
  { username: 'keerthu', password: 'keerthu123' }
];

let CURRENT_CAPTCHA = '';

// ===== INITIALIZE =====
document.addEventListener('DOMContentLoaded', function() {
  console.log('App.js loaded!');
  
  // Init CAPTCHA
  refreshCaptcha();
  
  // Attach login form handler
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
    console.log('Login form attached');
  } else {
    console.error('Login form NOT found!');
  }
  
  // Transfer buttons
  const goTransferBtn = document.getElementById('go-transfer');
  if (goTransferBtn) {
    goTransferBtn.addEventListener('click', function() {
      document.getElementById('dashboard-section').style.display = 'none';
      document.getElementById('transfer-section').style.display = 'block';
    });
  }
  
  const backDashboardBtn = document.getElementById('back-dashboard');
  if (backDashboardBtn) {
    backDashboardBtn.addEventListener('click', function() {
      document.getElementById('transfer-section').style.display = 'none';
      document.getElementById('dashboard-section').style.display = 'block';
    });
  }
  
  // Transfer form
  const transferForm = document.getElementById('transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', function(e) {
      e.preventDefault();
      alert('Transfer submitted (demo only)');
      this.reset();
    });
  }
  
  // Start attack polling if on dashboard
  if (document.getElementById('dashboard-section').style.display !== 'none') {
    fetchAttackType();
    setInterval(fetchAttackType, 5000);
  }
});

// ===== LOGIN HANDLER =====
function handleLogin(e) {
  e.preventDefault();
  console.log('Login form submitted');
  
  const userIdInput = document.getElementById('userId');
  const passwordInput = document.getElementById('password');
  const captchaInput = document.getElementById('captcha');
  
  if (!userIdInput || !passwordInput || !captchaInput) {
    console.error('Form inputs not found!');
    alert('Form error - refresh page');
    return;
  }
  
  const userId = userIdInput.value.trim();
  const password = passwordInput.value.trim();
  const captcha = captchaInput.value.trim();
  
  console.log('Inputs:', { userId, password, captcha, expected: CURRENT_CAPTCHA });
  
  // Validate CAPTCHA
  if (captcha !== CURRENT_CAPTCHA) {
    alert('Invalid security code. Please try again.');
    console.log('CAPTCHA mismatch:', captcha, 'vs', CURRENT_CAPTCHA);
    refreshCaptcha();
    return;
  }
  
  // Validate credentials
  const user = DEMO_USERS.find(u => u.username === userId && u.password === password);
  
 if (!user) {
  alert('Invalid User ID or Password. Please try again.');
  return;
}

  
  // Success
  console.log('Login success for:', userId);
  alert('Login successful! Welcome ' + userId);
  
  // Show dashboard
  document.getElementById('login-section').style.display = 'none';
  document.getElementById('dashboard-section').style.display = 'block';
  document.getElementById('transfer-section').style.display = 'none';
  
  // Start polling attack type
  fetchAttackType();
  setInterval(fetchAttackType, 5000);
}

// ===== CAPTCHA =====
function refreshCaptcha() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let captcha = '';
  for (let i = 0; i < 5; i++) {
    captcha += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  CURRENT_CAPTCHA = captcha;
  const captchaEl = document.getElementById('captchaText');
  const captchaInputEl = document.getElementById('captcha');
  
  if (captchaEl) captchaEl.textContent = captcha;
  if (captchaInputEl) captchaInputEl.value = '';
  
  console.log('CAPTCHA refreshed:', captcha);
}

function togglePassword() {
  const passwordInput = document.getElementById('password');
  const toggleBtn = document.querySelector('.stb-pwd-toggle');
  
  if (!passwordInput) return;
  
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    if (toggleBtn) toggleBtn.textContent = '🙈';
  } else {
    passwordInput.type = 'password';
    if (toggleBtn) toggleBtn.textContent = '👁️';
  }
}

// ===== ATTACK TYPE POLLING =====
async function fetchAttackType() {
  try {
    const res = await fetch('http://localhost:8000/api/last-attack-type');
    const data = await res.json();
    const type = data.type || 'normal';
    updateSecurityBanner(type);
  } catch (err) {
    console.log('Backend not connected:', err.message);
  }
}

function updateSecurityBanner(type) {
  const banner = document.getElementById('security-banner');
  const title = document.getElementById('security-title');
  const message = document.getElementById('security-message');
  const transferBtn = document.querySelector('#transfer-form button[type="submit"]');
  
  if (!banner || !title || !message) return;
  
  let bannerClass = 'banner banner-normal';
  let titleText = '✅ All Systems Normal';
  let messageText = 'No suspicious activity detected.';
  let shouldBlock = false;
  
  switch(type) {
    case 'brute_force':
      bannerClass = 'banner banner-danger';
      titleText = '⚠️ Brute Force Attack Detected';
      messageText = 'Multiple failed login attempts detected. System locked.';
      shouldBlock = true;
      break;
    case 'malware':
      bannerClass = 'banner banner-danger';
      titleText = '⚠️ Malware Alert';
      messageText = 'Suspicious file activity detected. Transactions disabled.';
      shouldBlock = true;
      break;
    case 'recon':
      bannerClass = 'banner banner-warning';
      titleText = '⚠️ Reconnaissance Activity';
      messageText = 'Port scanning/probing detected. Proceed with caution.';
      shouldBlock = true;
      break;
    case 'anomaly':
      bannerClass = 'banner banner-danger';
      titleText = '🔒 Anomaly Lockdown Mode';
      messageText = 'Unusual behavior detected. All transactions locked.';
      shouldBlock = true;
      break;
  }
  
  banner.className = bannerClass;
  title.textContent = titleText;
  message.textContent = messageText;
  
  if (transferBtn) {
    transferBtn.disabled = shouldBlock;
  }
  
  console.log('Banner updated:', type);
}
