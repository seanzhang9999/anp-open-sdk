document.addEventListener('DOMContentLoaded', () => {
  // Views
  const loginView = document.getElementById('login-view');
  const mainView = document.getElementById('main-view');

  // Login Elements
  const loginForm = document.getElementById('login-form');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const loginError = document.getElementById('login-error');

  // Main View Elements
  const settingsBtn = document.getElementById('settings-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const configPanel = document.getElementById('config-panel');
  const configForm = document.getElementById('config-form');
  const messageForm = document.getElementById('message-form');
  const messageInput = document.getElementById('message-input');
  const messagesContainer = document.getElementById('messages');
  const userInfo = document.getElementById('user-info');
  const chatModeSwitcher = document.getElementById('chat-mode-switcher');
  const agentDemoPanel = document.getElementById('agent-demo-panel');
  const agentStatus = document.getElementById('agent-status');

  // App State
  let currentUser = null;
  let chatMode = 'generic'; // 'generic', 'agent', or 'agent-demo'
  let llmConfig = {};

  // --- Initialization ---
  const init = async () => {
    // Load LLM config first
    llmConfig = await loadConfig();
    updateConfigForm(llmConfig);

    const closeConfigBtn = document.getElementById('close-config-btn');
    if (closeConfigBtn) {
      closeConfigBtn.addEventListener('click', toggleConfigPanel);
    }
    // Check for logged in user
    const storedUser = await getStoredUser();
    if (storedUser) {
      currentUser = storedUser;
      showMainView();
      await refreshUserDid(); // 加载时刷新did
    } else {
      showLoginView();
    }

    // Add all event listeners
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    settingsBtn.addEventListener('click', toggleConfigPanel);
    configForm.addEventListener('submit', handleConfigSave);
    messageForm.addEventListener('submit', handleSendMessage);
    chatModeSwitcher.addEventListener('click', handleModeSwitch);
    
    // Add demo button listeners
    setupDemoButtonListeners();
  };

  // --- User & Auth ---
  const getStoredUser = () => {
    return new Promise(resolve => {
      chrome.storage.local.get(['currentUser'], result => resolve(result.currentUser));
    });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    loginError.textContent = '';
    const username = usernameInput.value;
    const password = passwordInput.value;

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.message || 'Login failed');
      }

      currentUser = data.user;
      chrome.storage.local.set({ currentUser: data.user }, () => {
        showMainView();
        refreshUserDid(); // 登录后刷新did
      });
    } catch (error) {
      loginError.textContent = error.message;
      console.error('Login error:', error);
    }
  };

  const handleLogout = () => {
    chrome.storage.local.remove('currentUser', () => {
      showLoginView();
    });
  };

  // 新增：刷新did信息
  const refreshUserDid = async () => {
    if (!currentUser || !currentUser.username) return;
    try {
      const response = await fetch('http://localhost:8000/auth/userinfo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: currentUser.username })
    });
    const data = await response.json();
      if (response.ok && data.did) {
        currentUser.did = data.did;
        chrome.storage.local.set({ currentUser });
        // 显示 did
        const didDisplay = document.getElementById('user-did');
        if (didDisplay) {
          didDisplay.textContent = `${data.did}`;
          didDisplay.style.display = 'block';
    }
      }
    } catch (error) {
      console.error('刷新DID失败:', error);
    }
  };

  // --- View Management ---
  const showLoginView = () => {
    currentUser = null;
    mainView.style.display = 'none';
    loginView.style.display = 'block';
    loginError.textContent = '';
  };

  const showMainView = () => {
    if (!currentUser) return;
    userInfo.textContent = `User: ${currentUser.username}`;
    loginView.style.display = 'none';
    mainView.style.display = 'block';
    refreshUserDid(); // 切换到主界面时也刷新did
  };

  // --- Chat Logic ---
  const handleModeSwitch = (e) => {
    if (e.target.classList.contains('chat-mode')) {
      chatMode = e.target.dataset.mode;
      document.querySelector('.chat-mode.active-mode').classList.remove('active-mode');
      e.target.classList.add('active-mode');
      
      // Show/hide agent demo panel
      if (chatMode === 'agent-demo') {
        agentDemoPanel.style.display = 'block';
        updateAgentStatus();
      } else {
        agentDemoPanel.style.display = 'none';
      }
      
      // Optional: Clear chat history on mode switch
      messagesContainer.innerHTML = '';
      if (chatMode === 'generic') {
        addMessage('system', 'Switched to Generic LLM mode.');
      } else if (chatMode === 'agent') {
        addMessage('system', 'Switched to Personal Agent mode.');
      } else if (chatMode === 'agent-demo') {
        addMessage('system', 'Switched to Agent Demos mode. Click the buttons above to run demonstrations.');
      }
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const messageText = messageInput.value.trim();
    if (!messageText) return;

    addMessage('user', messageText);
    messageInput.value = '';
    addMessage('assistant', '...', true); // Show thinking indicator

    try {
      let reply;
      if (chatMode === 'agent') {
        if (!currentUser) throw new Error("Not logged in.");
        reply = await fetchAgentReply(messageText);
      } else {
        reply = await fetchGenericReply(messageText);
      }
      updateLastMessage('assistant', reply);
    } catch (error) {
      console.error('Error sending message:', error);
      updateLastMessage('system', `Error: ${error.message}`);
    }
    };

  const fetchAgentReply = async (message) => {
    const { username, did } = currentUser || {};
    if (!username && !did) {
      throw new Error('用户信息不完整，无法发送消息');
    }

    const body = {
      username,
      did,
      message
  };

    const response = await fetch('http://localhost:8000/agent/chat/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || data.message || 'Agent request failed');
    }
    return data.reply;
  };

  const fetchGenericReply = async (message) => {
    if (!llmConfig.apiBase || !llmConfig.apiKey) {
      throw new Error('API Base URL or API Key is not configured.');
    }
    const response = await fetch(`${llmConfig.apiBase}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${llmConfig.apiKey}`
      },
      body: JSON.stringify({
        model: llmConfig.model,
        messages: [{ role: 'user', content: message }],
        stream: false
      })
    });
    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data.error?.message || 'Failed to fetch response from LLM.';
      throw new Error(errorMsg);
    }
    return data.choices[0].message.content;
  };

  // --- UI & Config Helpers ---
  const addMessage = (role, content, isLoading = false) => {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    if (isLoading) {
      messageDiv.classList.add('loading');
    }
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  };

  const updateLastMessage = (role, content) => {
    const lastMessage = messagesContainer.querySelector('.message.loading');
    if (lastMessage) {
      lastMessage.textContent = content;
      lastMessage.classList.remove('loading');
      lastMessage.className = `message ${role}`;
    }
  };

  const toggleConfigPanel = () => {
    configPanel.style.display = configPanel.style.display === 'none' ? 'block' : 'none';
  };

  const handleConfigSave = async (e) => {
    e.preventDefault();
    const newConfig = {
      apiBase: document.getElementById('api-base').value,
      apiKey: document.getElementById('api-key').value,
      model: document.getElementById('model').value
    };
    await saveConfig(newConfig);
    llmConfig = newConfig;
    alert('Configuration saved!');
    toggleConfigPanel();
  };

  const saveConfig = (config) => {
    return new Promise(resolve => {
      chrome.storage.local.set({ llmConfig: config }, resolve);
});
  };

  const loadConfig = () => {
    return new Promise(resolve => {
      chrome.storage.local.get({
        llmConfig: { apiBase: '', apiKey: '', model: 'gpt-3.5-turbo' }
      }, result => resolve(result.llmConfig));
    });
  };

  const updateConfigForm = (config) => {
    const apiBaseInput = document.getElementById('api-base');
    const apiKeyInput = document.getElementById('api-key');
    const modelInput = document.getElementById('model');
    if (apiBaseInput) apiBaseInput.value = config.apiBase || '';
    if (apiKeyInput) apiKeyInput.value = config.apiKey || '';
    if (modelInput) modelInput.value = config.model || 'gpt-3.5-turbo';
  };

  // --- Agent Demo Functions ---
  const setupDemoButtonListeners = () => {
    const demoButtons = [
      { id: 'demo-discover', endpoint: '/agents/discover', name: '发现智能体' },
      { id: 'demo-calculator', endpoint: '/agents/demo/calculator', name: '计算器演示' },
      { id: 'demo-hello', endpoint: '/agents/demo/hello', name: 'Hello演示' },
      { id: 'demo-ai-crawler', endpoint: '/agents/demo/ai-crawler', name: 'AI爬虫演示' },
      { id: 'demo-ai-root-crawler', endpoint: '/agents/demo/ai-root-crawler', name: 'AI根爬虫演示' },
      { id: 'demo-agent-002', endpoint: '/agents/demo/agent-002', name: 'Agent 002演示' },
      { id: 'demo-agent-002-new', endpoint: '/agents/demo/agent-002-new', name: 'Agent 002新演示' }
    ];

    demoButtons.forEach(({ id, endpoint, name }) => {
      const button = document.getElementById(id);
      if (button) {
        button.addEventListener('click', () => runAgentDemo(endpoint, name));
      }
    });
  };

  const updateAgentStatus = async () => {
    if (!currentUser) {
      agentStatus.textContent = '请先登录';
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/agents/status', {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentUser.username}:${currentUser.password || ''}`
        }
      });

      const data = await response.json();
      if (response.ok) {
        agentStatus.textContent = `状态: ${data.initialized ? '已初始化' : '未初始化'} | 智能体数量: ${data.agents_count}`;
      } else {
        agentStatus.textContent = '获取状态失败';
      }
    } catch (error) {
      console.error('Failed to get agent status:', error);
      agentStatus.textContent = '连接失败';
    }
  };

  const runAgentDemo = async (endpoint, demoName) => {
    if (!currentUser) {
      addMessage('system', '请先登录');
      return;
    }

    addMessage('system', `正在运行 ${demoName}...`);
    addMessage('assistant', '...', true); // Show loading indicator

    try {
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${currentUser.username}:${currentUser.password || ''}`
        }
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        const resultText = typeof data.result === 'object' 
          ? JSON.stringify(data.result, null, 2) 
          : data.result || '演示完成';
        updateLastMessage('assistant', `${demoName} 结果:\n${resultText}`);
      } else {
        const errorText = data.error || data.detail || '演示失败';
        updateLastMessage('system', `${demoName} 失败: ${errorText}`);
      }
    } catch (error) {
      console.error(`${demoName} error:`, error);
      updateLastMessage('system', `${demoName} 错误: ${error.message}`);
    }
  };

  // Start the application
  init();
});
