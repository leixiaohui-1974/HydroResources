// HydroNet 主JavaScript文件

let conversationId = null;

// 发送消息
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 显示用户消息
    addMessage('user', message);
    input.value = '';
    
    // 显示加载状态
    const loadingId = addMessage('assistant', '正在思考中...');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });
        
        const data = await response.json();
        
        // 移除加载消息
        removeMessage(loadingId);
        
        if (data.success) {
            // 显示AI响应
            addMessage('assistant', data.message, data.mcp_data);
            conversationId = data.conversation_id;
        } else {
            addMessage('assistant', '抱歉，处理您的请求时出现了错误：' + data.error);
        }
        
    } catch (error) {
        removeMessage(loadingId);
        addMessage('assistant', '抱歉，网络连接出现问题，请稍后再试。');
        console.error('发送消息失败:', error);
    }
}

// 添加消息到聊天界面
function addMessage(role, content, mcpData = null) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 处理内容格式
    const formattedContent = formatContent(content);
    contentDiv.innerHTML = formattedContent;
    
    // 如果有MCP数据，添加额外信息
    if (mcpData) {
        const mcpInfo = document.createElement('div');
        mcpInfo.style.marginTop = '10px';
        mcpInfo.style.padding = '10px';
        mcpInfo.style.background = 'rgba(0, 88, 202, 0.1)';
        mcpInfo.style.borderRadius = '8px';
        mcpInfo.style.fontSize = '13px';
        
        mcpInfo.innerHTML = `
            <strong>📊 MCP服务调用: ${mcpData.service}</strong><br>
            <em>已为您调用 ${mcpData.service} 服务获取数据</em>
        `;
        
        contentDiv.appendChild(mcpInfo);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // 滚动到底部
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageId;
}

// 移除消息
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// 格式化消息内容
function formatContent(content) {
    // 转换换行符
    content = content.replace(/\n/g, '<br>');
    
    // 转换列表
    content = content.replace(/^([•\-\*])\s(.+)$/gm, '<li>$2</li>');
    if (content.includes('<li>')) {
        content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }
    
    // 转换粗体
    content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // 转换代码块
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    return content;
}

// 快速查询
function quickQuery(query) {
    document.getElementById('userInput').value = `帮我做一个${query}分析`;
    sendMessage();
}

// 清空对话
function clearChat() {
    if (confirm('确定要清空对话历史吗？')) {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p><strong>HydroNet AI助手</strong></p>
                    <p>对话已清空。请输入您的新问题！</p>
                </div>
            </div>
        `;
        conversationId = null;
    }
}

// 显示系统信息
async function showSystemInfo() {
    const modal = document.getElementById('systemModal');
    const modalBody = document.getElementById('systemModalBody');
    
    modal.classList.add('active');
    modalBody.innerHTML = '<p>加载中...</p>';
    
    try {
        // 获取系统信息
        const infoResponse = await fetch('/api/system/info');
        const info = await infoResponse.json();
        
        // 获取健康状态
        const healthResponse = await fetch('/api/health');
        const health = await healthResponse.json();
        
        modalBody.innerHTML = `
            <div style="line-height: 1.8;">
                <h3>💧 ${info.name}</h3>
                <p><strong>版本：</strong>${info.version}</p>
                <p><strong>描述：</strong>${info.description}</p>
                
                <h4 style="margin-top: 20px; color: var(--primary-color);">系统能力：</h4>
                <ul>
                    ${info.capabilities.map(cap => `<li>${cap}</li>`).join('')}
                </ul>
                
                <h4 style="margin-top: 20px; color: var(--primary-color);">服务状态：</h4>
                <p><strong>腾讯元宝大模型：</strong>
                    <span class="service-status ${health.services.hunyuan ? 'active' : 'pending'}">
                        ${health.services.hunyuan ? '✅ 正常' : '⏸️ 待配置'}
                    </span>
                </p>
                <p><strong>MCP服务数量：</strong>${info.mcp_services_count} 个</p>
                <p><strong>系统状态：</strong>
                    <span class="service-status active">${health.status}</span>
                </p>
                <p style="margin-top: 20px; color: #666; font-size: 14px;">
                    <em>最后更新：${new Date(health.timestamp).toLocaleString('zh-CN')}</em>
                </p>
            </div>
        `;
        
    } catch (error) {
        modalBody.innerHTML = '<p style="color: red;">加载系统信息失败</p>';
        console.error('加载系统信息失败:', error);
    }
}

// 显示MCP服务
async function showServices() {
    const sidebar = document.getElementById('sidebar');
    const sidebarContent = document.getElementById('sidebarContent');
    
    sidebar.classList.add('active');
    sidebarContent.innerHTML = '<p>加载中...</p>';
    
    try {
        const response = await fetch('/api/mcp/services');
        const data = await response.json();
        
        if (data.success) {
            let html = '<div>';
            
            data.services.forEach(service => {
                html += `
                    <div class="service-card">
                        <h4>🔧 ${service.description || service.name}</h4>
                        <p><strong>类型：</strong>${service.type}</p>
                        <p><strong>方法：</strong>${service.methods.join(', ')}</p>
                        <span class="service-status ${service.status}">
                            ${service.status === 'active' ? '✅ 已激活' : '⏸️ 待配置'}
                        </span>
                        ${service.url ? `<p style="margin-top: 8px; font-size: 12px; color: #666;">URL: ${service.url}</p>` : ''}
                    </div>
                `;
            });
            
            html += '</div>';
            sidebarContent.innerHTML = html;
        } else {
            sidebarContent.innerHTML = '<p style="color: red;">加载服务列表失败</p>';
        }
        
    } catch (error) {
        sidebarContent.innerHTML = '<p style="color: red;">加载服务列表失败</p>';
        console.error('加载MCP服务失败:', error);
    }
}

// 关闭侧边栏
function closeSidebar() {
    document.getElementById('sidebar').classList.remove('active');
}

// 关闭模态框
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// 键盘事件处理
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    
    // Ctrl+Enter 发送消息
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 点击模态框背景关闭
    document.getElementById('systemModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal('systemModal');
        }
    });
    
    console.log('HydroNet 系统已加载完成 ✅');
});
