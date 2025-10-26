// HydroNet Pro - 主前端逻辑

class HydroNetApp {
    constructor() {
        this.currentConversationId = null;
        this.userId = 'default_user'; // 生产环境应从认证系统获取
        this.socket = null;
        this.useWebSocket = false; // 默认使用SSE，可切换到WebSocket
        
        this.init();
    }
    
    init() {
        console.log('🌊 HydroNet Pro 初始化...');
        
        // 初始化WebSocket（可选）
        if (this.useWebSocket) {
            this.initWebSocket();
        }
        
        // 绑定事件
        this.bindEvents();
        
        // 加载数据
        this.loadConversations();
        this.loadQuota();
        
        // 自动调整textarea高度
        this.setupAutoResize();
        
        console.log('✅ HydroNet Pro 初始化完成');
    }
    
    // ==================== WebSocket ====================
    
    initWebSocket() {
        console.log('🔌 连接WebSocket...');
        this.socket = io({
            transports: ['websocket', 'polling']
        });
        
        this.socket.on('connect', () => {
            console.log('✅ WebSocket 已连接');
            this.showToast('已连接到服务器');
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket 断开连接');
            this.showToast('与服务器断开连接', 'error');
        });
        
        this.socket.on('chat_chunk', (chunk) => {
            this.handleChatChunk(chunk);
        });
        
        this.socket.on('chat_complete', () => {
            this.onChatComplete();
        });
        
        this.socket.on('error', (error) => {
            console.error('WebSocket错误:', error);
            this.showToast(error.message, 'error');
        });
    }
    
    // ==================== 事件绑定 ====================
    
    bindEvents() {
        // 新对话按钮
        document.getElementById('newChatBtn').addEventListener('click', () => {
            this.createNewConversation();
        });
        
        // 发送消息
        document.getElementById('sendButton').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 输入框Enter发送
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // 功能卡片点击
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.dataset.prompt;
                if (prompt) {
                    document.getElementById('messageInput').value = prompt;
                    this.sendMessage();
                }
            });
        });
        
        // 清除对话
        const clearBtn = document.getElementById('clearChatBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearCurrentConversation();
            });
        }
        
        // 用户菜单
        document.getElementById('userButton').addEventListener('click', () => {
            const dropdown = document.getElementById('userDropdown');
            dropdown.classList.toggle('show');
        });
        
        // 点击外部关闭dropdown
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu')) {
                document.getElementById('userDropdown').classList.remove('show');
            }
        });
        
        // 推荐链接
        document.getElementById('referralLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showReferralModal();
        });
        
        // 关闭推荐弹窗
        document.getElementById('closeReferralModal').addEventListener('click', () => {
            document.getElementById('referralModal').classList.remove('show');
        });
        
        // 复制推荐码
        document.getElementById('copyReferralCode').addEventListener('click', () => {
            this.copyReferralCode();
        });
        
        // 升级链接
        document.getElementById('upgradeLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showUpgradeModal();
        });
    }
    
    // ==================== 对话管理 ====================
    
    async loadConversations() {
        try {
            const response = await fetch('/api/conversations', {
                headers: {
                    'X-User-ID': this.userId
                }
            });
            
            if (!response.ok) throw new Error('加载对话列表失败');
            
            const data = await response.json();
            this.renderConversations(data.conversations);
        } catch (error) {
            console.error('加载对话失败:', error);
            this.showToast('加载对话列表失败', 'error');
        }
    }
    
    renderConversations(conversations) {
        const list = document.getElementById('conversationsList');
        list.innerHTML = '';
        
        if (conversations.length === 0) {
            list.innerHTML = '<div class="empty-state">暂无对话</div>';
            return;
        }
        
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            if (conv.id === this.currentConversationId) {
                item.classList.add('active');
            }
            
            item.innerHTML = `
                <div>
                    <div class="conversation-title">${this.escapeHtml(conv.title)}</div>
                    <div class="conversation-time">${this.formatTime(conv.updated_at)}</div>
                </div>
            `;
            
            item.addEventListener('click', () => {
                this.loadConversation(conv.id);
            });
            
            list.appendChild(item);
        });
    }
    
    async loadConversation(conversationId) {
        try {
            this.showLoading();
            
            const response = await fetch(`/api/conversations/${conversationId}`, {
                headers: {
                    'X-User-ID': this.userId
                }
            });
            
            if (!response.ok) throw new Error('加载对话失败');
            
            const data = await response.json();
            
            this.currentConversationId = conversationId;
            this.renderConversation(data.conversation, data.messages);
            
            // 更新UI
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('chatArea').style.display = 'flex';
            
            // 更新侧边栏active状态
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.conversation-item')?.classList.add('active');
            
            this.hideLoading();
        } catch (error) {
            console.error('加载对话失败:', error);
            this.showToast('加载对话失败', 'error');
            this.hideLoading();
        }
    }
    
    renderConversation(conversation, messages) {
        // 设置标题
        document.getElementById('chatTitle').textContent = conversation.title;
        
        // 渲染消息
        const messagesList = document.getElementById('messagesList');
        messagesList.innerHTML = '';
        
        messages.forEach(msg => {
            this.appendMessage(msg.role, msg.content, msg.tool_calls);
        });
        
        // 滚动到底部
        this.scrollToBottom();
    }
    
    createNewConversation() {
        this.currentConversationId = null;
        
        // 显示欢迎屏幕
        document.getElementById('welcomeScreen').style.display = 'flex';
        document.getElementById('chatArea').style.display = 'none';
        
        // 清除侧边栏active状态
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 清空输入框
        document.getElementById('messageInput').value = '';
    }
    
    async clearCurrentConversation() {
        if (!this.currentConversationId) return;
        
        if (!confirm('确定要删除这个对话吗？')) return;
        
        try {
            const response = await fetch(`/api/conversations/${this.currentConversationId}`, {
                method: 'DELETE',
                headers: {
                    'X-User-ID': this.userId
                }
            });
            
            if (!response.ok) throw new Error('删除对话失败');
            
            this.showToast('对话已删除');
            this.createNewConversation();
            this.loadConversations();
        } catch (error) {
            console.error('删除对话失败:', error);
            this.showToast('删除对话失败', 'error');
        }
    }
    
    // ==================== 发送消息 ====================
    
    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // 禁用输入
        input.disabled = true;
        document.getElementById('sendButton').disabled = true;
        
        // 清空输入框
        input.value = '';
        input.style.height = 'auto';
        
        // 显示用户消息
        this.appendMessage('user', message);
        
        // 显示加载动画
        this.showTypingIndicator();
        
        // 隐藏欢迎屏幕
        if (document.getElementById('welcomeScreen').style.display !== 'none') {
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('chatArea').style.display = 'flex';
        }
        
        try {
            if (this.useWebSocket && this.socket && this.socket.connected) {
                // 使用WebSocket
                await this.sendMessageViaWebSocket(message);
            } else {
                // 使用SSE
                await this.sendMessageViaSSE(message);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.hideTypingIndicator();
            this.appendMessage('assistant', `❌ 发送失败: ${error.message}`);
        } finally {
            // 重新启用输入
            input.disabled = false;
            document.getElementById('sendButton').disabled = false;
            input.focus();
            
            // 更新配额
            this.loadQuota();
            
            // 刷新对话列表
            this.loadConversations();
        }
    }
    
    async sendMessageViaSSE(message) {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': this.userId
            },
            body: JSON.stringify({
                conversation_id: this.currentConversationId,
                message: message
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '发送失败');
        }
        
        // 处理SSE流
        await this.processSSEStream(response.body);
    }
    
    async processSSEStream(stream) {
        const reader = stream.getReader();
        const decoder = new TextDecoder();
        
        let assistantMessageElement = null;
        let assistantContent = '';
        
        // 移除加载动画
        this.hideTypingIndicator();
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'text') {
                            // 文本内容
                            if (!assistantMessageElement) {
                                assistantMessageElement = this.createMessageElement('assistant', '');
                                document.getElementById('messagesList').appendChild(assistantMessageElement);
                            }
                            
                            assistantContent += data.content;
                            const contentDiv = assistantMessageElement.querySelector('.message-content');
                            contentDiv.textContent = assistantContent;
                            
                            this.scrollToBottom();
                            
                        } else if (data.type === 'tool_call') {
                            // 工具调用
                            this.showToolCall(data);
                            
                        } else if (data.type === 'tool_result') {
                            // 工具结果
                            this.updateToolCall(data);
                            
                        } else if (data.type === 'complete') {
                            // 完成
                            console.log('✅ 对话完成');
                            
                        } else if (data.type === 'error') {
                            // 错误
                            throw new Error(data.error);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
    
    async sendMessageViaWebSocket(message) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('发送超时'));
            }, 60000);
            
            this.socket.once('chat_complete', () => {
                clearTimeout(timeout);
                resolve();
            });
            
            this.socket.once('error', (error) => {
                clearTimeout(timeout);
                reject(new Error(error.message));
            });
            
            this.socket.emit('chat_message', {
                user_id: this.userId,
                conversation_id: this.currentConversationId,
                message: message
            });
        });
    }
    
    handleChatChunk(chunk) {
        // WebSocket chunk处理（类似SSE）
        if (chunk.type === 'text') {
            // 追加文本...
        } else if (chunk.type === 'tool_call') {
            this.showToolCall(chunk);
        } else if (chunk.type === 'tool_result') {
            this.updateToolCall(chunk);
        }
    }
    
    onChatComplete() {
        this.hideTypingIndicator();
        this.scrollToBottom();
    }
    
    // ==================== 消息渲染 ====================
    
    appendMessage(role, content, toolCalls = null) {
        const messagesList = document.getElementById('messagesList');
        const messageElement = this.createMessageElement(role, content);
        
        messagesList.appendChild(messageElement);
        
        // 如果有工具调用数据，显示
        if (toolCalls) {
            try {
                const calls = typeof toolCalls === 'string' ? JSON.parse(toolCalls) : toolCalls;
                calls.forEach(call => {
                    if (call.type === 'tool_call' || call.type === 'tool_result') {
                        this.showToolCall(call);
                    }
                });
            } catch (e) {
                console.error('解析工具调用失败:', e);
            }
        }
        
        this.scrollToBottom();
    }
    
    createMessageElement(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const roleName = role === 'user' ? '您' : 'HydroNet';
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">${avatar}</div>
                <div class="message-role">${roleName}</div>
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;
        
        return messageDiv;
    }
    
    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant loading';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">🤖</div>
                <div class="message-role">HydroNet</div>
            </div>
            <div class="message-content">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        
        document.getElementById('messagesList').appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // ==================== 工具调用显示 ====================
    
    showToolCall(data) {
        const { tool_name, status, arguments: args } = data;
        
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call';
        toolDiv.id = `tool-${tool_name}-${Date.now()}`;
        
        toolDiv.innerHTML = `
            <div class="tool-call-header">
                <div class="tool-call-name">
                    ⚙️ ${this.getToolDisplayName(tool_name)}
                </div>
                <div class="tool-call-status ${status}">${this.getStatusText(status)}</div>
            </div>
            ${args ? `<div class="tool-call-args">参数: ${JSON.stringify(args, null, 2)}</div>` : ''}
            <div class="tool-call-result-container"></div>
        `;
        
        document.getElementById('messagesList').appendChild(toolDiv);
        this.scrollToBottom();
        
        return toolDiv;
    }
    
    updateToolCall(data) {
        const { tool_name, status, result, error } = data;
        
        // 找到对应的工具调用元素
        const toolDivs = document.querySelectorAll('.tool-call');
        const toolDiv = Array.from(toolDivs).find(div => 
            div.querySelector('.tool-call-name').textContent.includes(this.getToolDisplayName(tool_name))
        );
        
        if (!toolDiv) return;
        
        // 更新状态
        const statusSpan = toolDiv.querySelector('.tool-call-status');
        statusSpan.className = `tool-call-status ${status}`;
        statusSpan.textContent = this.getStatusText(status);
        
        // 显示结果
        const resultContainer = toolDiv.querySelector('.tool-call-result-container');
        if (result) {
            resultContainer.innerHTML = `
                <div class="tool-call-result">${this.formatToolResult(result)}</div>
            `;
        } else if (error) {
            resultContainer.innerHTML = `
                <div class="tool-call-result error">❌ ${this.escapeHtml(error)}</div>
            `;
        }
        
        this.scrollToBottom();
    }
    
    getToolDisplayName(toolName) {
        const names = {
            'simulation': '水网仿真',
            'identification': '系统辨识',
            'scheduling': '优化调度',
            'control': '控制策略',
            'testing': '性能测试'
        };
        return names[toolName] || toolName;
    }
    
    getStatusText(status) {
        const texts = {
            'running': '⏳ 执行中...',
            'completed': '✅ 完成',
            'failed': '❌ 失败'
        };
        return texts[status] || status;
    }
    
    formatToolResult(result) {
        if (typeof result === 'string') {
            return this.escapeHtml(result);
        }
        
        // 格式化JSON结果
        return `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    }
    
    // ==================== 配额管理 ====================
    
    async loadQuota() {
        try {
            const response = await fetch('/api/user/quota', {
                headers: {
                    'X-User-ID': this.userId
                }
            });
            
            if (!response.ok) return;
            
            const data = await response.json();
            this.updateQuotaDisplay(data.quota);
        } catch (error) {
            console.error('加载配额失败:', error);
        }
    }
    
    updateQuotaDisplay(quota) {
        const { used, limit, remaining, tier } = quota;
        
        document.getElementById('quotaUsed').textContent = used;
        document.getElementById('quotaLimit').textContent = limit === -1 ? '∞' : limit;
        
        const percentage = limit === -1 ? 0 : (used / limit * 100);
        document.getElementById('quotaFill').style.width = `${percentage}%`;
        
        // 根据使用情况改变颜色
        const fillDiv = document.getElementById('quotaFill');
        if (percentage > 80) {
            fillDiv.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
        } else if (percentage > 50) {
            fillDiv.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
        } else {
            fillDiv.style.background = 'linear-gradient(90deg, var(--primary-color), #60a5fa)';
        }
    }
    
    // ==================== 推荐系统 ====================
    
    async showReferralModal() {
        try {
            const response = await fetch('/api/user/referral', {
                headers: {
                    'X-User-ID': this.userId
                }
            });
            
            if (!response.ok) throw new Error('获取推荐信息失败');
            
            const data = await response.json();
            
            document.getElementById('referralCodeInput').value = data.referral_code;
            document.getElementById('referralTotal').textContent = data.stats.total;
            document.getElementById('referralConverted').textContent = data.stats.converted;
            
            document.getElementById('referralModal').classList.add('show');
        } catch (error) {
            console.error('加载推荐信息失败:', error);
            this.showToast('加载推荐信息失败', 'error');
        }
    }
    
    copyReferralCode() {
        const input = document.getElementById('referralCodeInput');
        input.select();
        document.execCommand('copy');
        this.showToast('推荐码已复制！');
    }
    
    showUpgradeModal() {
        this.showToast('升级功能开发中...', 'info');
    }
    
    // ==================== UI工具函数 ====================
    
    showLoading() {
        document.getElementById('loadingOverlay').classList.add('show');
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('show');
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    scrollToBottom() {
        const container = document.getElementById('messagesContainer');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    setupAutoResize() {
        const textarea = document.getElementById('messageInput');
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        });
    }
    
    // ==================== 辅助函数 ====================
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return '刚刚';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new HydroNetApp();
});
