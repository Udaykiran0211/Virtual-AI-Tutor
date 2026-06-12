/**
 * ResilientAPIClient
 * Centralizes all backend communication with built-in heartbeat, 
 * automatic reconnection, and exponential backoff retry logic.
 */
class ResilientAPIClient {
    constructor(baseUrl = '') {
        const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
        const isLiveServer = window.location.port !== '5000' && window.location.port !== '';
        this.baseUrl = baseUrl || ((isLocal && isLiveServer) ? 'http://127.0.0.1:5000' : '');
        this.status = 'disconnected'; 
        this.isAuthenticated = false; // New: track authentication state
        this.listeners = [];
        this.heartbeatInterval = 5000;
        this.heartbeatFailures = 0;
        this.maxHeartbeatFailures = 2; 

        this.isStaticBypass = this._checkStaticBypass();
        this.startHeartbeat();
    }

    _checkStaticBypass() {
        // Detect if running on localhost via Live Server or directly via file://
        const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
        const isFile = window.location.protocol === 'file:';
        const isLiveServer = window.location.port !== '5000' && window.location.port !== '';
        return (isLocal && isLiveServer) || isFile;
    }



    /**
     * Subscribe to connection status changes
     * @param {Function} callback (status) => {}
     */
    onStatusChange(callback) {
        this.listeners.push(callback);
    }

    _updateStatus(newStatus) {
        if (this.status !== newStatus) {
            this.status = newStatus;
            this.listeners.forEach(cb => cb(newStatus));
            console.log(`[API Client] Status transitioned to: ${newStatus} (Static Bypass: ${this.isStaticBypass})`);
        }
    }


    async startHeartbeat() {
        const check = async () => {
            try {
                const response = await fetch(`${this.baseUrl}/api/heartbeat`, {
                    method: 'GET',
                    mode: 'cors'
                });
                if (response.ok) {
                    const data = await response.json();
                    this.isAuthenticated = data.authenticated || false;
                    this.heartbeatFailures = 0;
                    this._updateStatus('connected');
                } else {
                    this.heartbeatFailures++;
                    if (this.heartbeatFailures > this.maxHeartbeatFailures) {
                        this._updateStatus('disconnected');
                    }
                }
            } catch (error) {
                this.heartbeatFailures++;
                if (this.heartbeatFailures > this.maxHeartbeatFailures) {
                    this._updateStatus('disconnected');
                }
            }
        };

        // Run immediately
        await check();
        
        // Schedule subsequent runs
        setInterval(check, this.heartbeatInterval);
    }

    /**
     * Reliable request wrapper with auto-retry
     */
    async request(endpoint, options = {}, retries = 3) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            credentials: 'include' // Allow cookies for cross-origin requests
        };

        const mergedOptions = { ...defaultOptions, ...options };

        for (let i = 0; i <= retries; i++) {
            try {
                const response = await fetch(url, mergedOptions);

                // If the response is not ok (e.g. 401, 500) and we are in bypass mode, use mocks
                if (!response.ok && this.isStaticBypass) {
                    console.warn(`[API Client] Request to ${endpoint} returned ${response.status}. Using mock fallback.`);
                    return await this._getMockResponse(endpoint, options);
                }

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`[API Client] Error ${response.status}: ${errorText}`);
                    throw new Error(`HTTP Error ${response.status}: ${errorText}`);
                }

                // Check if response is actually JSON
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    return await response.json();
                } else {
                    // If we got HTML/Text but expected JSON (e.g. redirect to login), use mock in bypass
                    if (this.isStaticBypass) {
                        console.warn(`[API Client] Expected JSON but got ${contentType}. Using mock fallback.`);
                        return await this._getMockResponse(endpoint, options);
                    }
                    throw new Error(`Expected JSON but got ${contentType}`);
                }

            } catch (error) {
                // If fetch itself failed (network error) and we are in bypass mode, use mocks
                if (this.isStaticBypass) {
                    console.warn(`[API Client] Network error for ${endpoint}. Using mock fallback.`);
                    return await this._getMockResponse(endpoint, options);
                }

                console.warn(`[API Client] Request to ${endpoint} failed (Attempt ${i + 1}/${retries + 1}):`, error);

                if (i === retries) {
                    this._updateStatus('disconnected');
                    throw error;
                }

                // Exponential backoff
                const delay = Math.pow(2, i) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    /**
     * Centralized mock responses
     */
    async _getMockResponse(endpoint, options = {}) {
        let body = {};
        if (options.body) {
            try {
                body = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
            } catch (e) {
                console.warn("[API Client] Mock body parse failed", e);
            }
        }

        // 1. User Stats Mock
        if (endpoint.includes('/api/user_stats')) {
            const progress = 45;
            let role = "Explorer";
            if (progress < 25) role = "Beginner";
            else if (progress < 80) role = "Scholar";
            else role = "Academic";
            
            return {
                username: "Static Explorer",
                role: role,
                plan: "Basic Plan",
                streak_count: 5,
                assessments_count: 5,
                progress_percent: progress,
                recent_lessons: [
                    { topic_id: "Python Basics", language: "python", completed: true },
                    { topic_id: "Control Flow", language: "python", completed: true }
                ],
                quiz_history: [
                    { topic_id: "Python Basics", language: "python", score: 3, total_questions: 3, timestamp: new Date().toISOString() },
                    { topic_id: "Variables", language: "python", score: 2, total_questions: 3, timestamp: new Date().toISOString() }
                ]
            };
        }

        // 2. Roadmap Mock
        if (endpoint.includes('/roadmap/')) {
            const lang = endpoint.split('/').pop().split('?')[0];
            try {
                const localResp = await fetch('data/roadmap.json');
                if (localResp.ok) {
                    const allData = await localResp.json();
                    return allData[lang] || {};
                }
            } catch (e) {
                console.error("[API Client] Local roadmap fetch failed:", e);
            }
            return {};
        }

        // 3. Video Mock
        if (endpoint.includes('/api/video')) {
            const lang = body.language || 'python';
            const topic = body.topic || 'basics';

            // Map of varied, high-quality, long-form tutorials
            const videoPool = {
                'python': [
                    'https://www.youtube.com/embed/u-OmVr_fT4s', // Python Tutorial - 30m
                    'https://www.youtube.com/embed/ZDa-Z5JzLYM', // Python Functions & Modules - 25m
                    'https://www.youtube.com/embed/9Os0o3wzS_I'  // Python Functions - 21m
                ],
                'java': [
                    'https://www.youtube.com/embed/qay771mqKOk', // Java Syntax - 22m
                    'https://www.youtube.com/embed/ZFx0ZFQMtH0', // Java Classes - 17m
                    'https://www.youtube.com/embed/-xmJSKRo5ec'  // Java OOP - 20m
                ],
                'cpp': [
                    'https://www.youtube.com/embed/EvYmTCx9BFs', // C++ Basics - 16m
                    'https://www.youtube.com/embed/ePJxpxsnkGw', // C++ Pointers - 22m
                    'https://www.youtube.com/embed/2pAY7Ftlfl0'  // C++ Logic - 15m
                ]
            };

            const pool = videoPool[lang] || videoPool['python'];
            // Rotate based on topic string length/hash to ensure different topics get different videos
            const index = Math.abs(topic.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a }, 0)) % pool.length;

            return {
                video_url: pool[index]
            };
        }

        // 4. Notes Mock
        if (endpoint.includes('/api/notes')) {
            const topic = body.topic || "this topic";
            const lang = body.language || "Programming";
            const langTitle = lang.charAt(0).toUpperCase() + lang.slice(1);

            if (endpoint.includes('/save')) {
                localStorage.setItem(`notes_${body.topic_id}`, body.content);
                return { status: "success" };
            }
            if (endpoint.includes('/load/')) {
                const id = endpoint.split('/').pop();
                return { content: localStorage.getItem(`notes_${id}`) || "" };
            }

            return {
                notes: `
                    <div class="ai-notes-container">
                        <h3>${topic} in ${langTitle}</h3>
                        <p>Welcome to this comprehensive technical guide on <strong>${topic}</strong> formatted specifically for <strong>${langTitle}</strong> developers. This guide covers core concepts, syntax patterns, and industry best practices.</p>
                        
                        <h4>1. Core Concepts</h4>
                        <ul>
                            <li><strong>Definition</strong>: Understanding how ${topic} fits into the ${langTitle} ecosystem.</li>
                            <li><strong>Significance</strong>: Why this topic is critical for building scalable and maintainable ${langTitle} applications.</li>
                            <li><strong>Implementation</strong>: How to leverage ${langTitle}'s unique features to implement this efficiently.</li>
                        </ul>

                        <h4>2. Technical Breakdown</h4>
                        <p>In ${langTitle}, ${topic} is often handled using specific architectural patterns. Below is a detailed look at the internal mechanics:</p>
                        <ul>
                            <li><strong>Memory Management</strong>: How ${langTitle} manages resources when executing ${topic} logic.</li>
                            <li><strong>Error Handling</strong>: Common exceptions and how to catch them using try-catch blocks.</li>
                        </ul>

                        <h4>3. ${langTitle} Code Example</h4>
                        <pre><code>// Example of ${topic} in ${langTitle}
function example() {
    console.log("Applying ${topic} logic...");
    // Technical implementation details here
    return true;
}</code></pre>

                        <h4>4. Best Practices & Pitfalls</h4>
                        <p>When working with ${topic} in ${langTitle}, always keep these points in mind:</p>
                        <ul>
                            <li><strong>Performance</strong>: Avoid nested loops when processing large datasets related to ${topic}.</li>
                            <li><strong>Security</strong>: Sanitize all inputs before passing them to ${topic}-related functions.</li>
                            <li><strong>Type Safety</strong>: Use strict typing (or hints) to prevent runtime errors during execution.</li>
                        </ul>
                        
                        <div style="margin-top:20px; padding:10px; background:rgba(0,184,148,0.1); border-left:4px solid #00b894;">
                            <strong>Pro Tip:</strong> Most modern ${langTitle} frameworks have built-in utilities that simplify the implementation of ${topic} significantly.
                        </div>
                    </div>
                `
            };
        }

        // 5. Quiz Mock
        if (endpoint.includes('/api/quiz')) {
            if (endpoint.includes('/submit')) return { status: "success" };
            const lang = body.language || 'javascript';
            return {
                quiz: [
                    {
                        question: `What is the primary goal of ${body.topic || 'this topic'}?`,
                        options: ["Option A", "Option B", "Option C", "Option D"],
                        answer: 0,
                        explanation: "Option A is the foundational objective upon which all other features are built."
                    },
                    {
                        question: `How does this logic behave?\n\`\`\`javascript\nconst x = 5;\nif (x > 2) console.log("High");\n\`\`\``,
                        options: ["Prints High", "Error", "No output", "Prints Low"],
                        answer: 0,
                        explanation: "The variable x is 5, which is greater than 2, triggering the true branch."
                    },
                    {
                        question: `Which of these is a best practice in ${body.topic || 'this topic'}?`,
                        options: ["Laziness", "Hardcoding", "Documentation", "Ignoring Errors"],
                        answer: 2,
                        explanation: "Comprehensive documentation ensures maintainability and easier collaboration."
                    },
                    {
                        question: `Complexity in ${body.topic || 'this topic'} should be:`,
                        options: ["Increased", "Minimized", "Hidden", "Randomized"],
                        answer: 1,
                        explanation: "Minimizing complexity reduces the surface area for bugs and improves performance."
                    },
                    {
                        question: `Key benefit of ${body.topic || 'this topic'}?`,
                        options: ["ROI", "Speed", "Quality", "Efficiency"],
                        answer: 3,
                        explanation: "Efficiency allows for faster iteration cycles and lower resource overhead."
                    },
                    {
                        question: `What is the output of this snippet?\n\`\`\`javascript\nconsole.log(typeof NaN);\n\`\`\``,
                        options: ["number", "NaN", "undefined", "object"],
                        answer: 0,
                        explanation: "In JavaScript, NaN (Not-a-Number) is technically a type of number."
                    },
                    {
                        question: `Who is the main audience for ${body.topic || 'this topic'}?`,
                        options: ["Developers", "Clients", "Managers", "End Users"],
                        answer: 0,
                        explanation: "Developers are the primary users who interface with the core technical components."
                    },
                    {
                        question: `What is the output of this operation?\n\`\`\`javascript\n[1, 2].map(x => x * 2)\n\`\`\``,
                        options: ["[1, 2]", "[2, 4]", "Error", "[3, 4]"],
                        answer: 1,
                        explanation: "The map function iterates over the array and multiplies each element by 2."
                    },
                    {
                        question: `Ideal setting for ${body.topic || 'this topic'}?`,
                        options: ["Cloud", "Local", "Edge", "Any"],
                        answer: 0,
                        explanation: "Cloud environments provide the necessary scale and redundancy for most use cases."
                    },
                    {
                        question: `Standard tool for ${body.topic || 'this topic'}?`,
                        options: ["Tool X", "Tool Y", "Tool Z", "None"],
                        answer: 1,
                        explanation: "Tool Y is the most widely adopted solution in the current ecosystem."
                    },
                    {
                        question: `Debug this code:\n\`\`\`javascript\nlet a = [1];\nlet b = a;\nb.push(2);\nconsole.log(a);\n\`\`\``,
                        options: ["[1]", "[1, 2]", "Error", "undefined"],
                        answer: 1,
                        explanation: "Arrays are reference types in JavaScript, so 'b' points to the same memory as 'a'."
                    },
                    {
                        question: `First step in ${body.topic || 'this topic'}?`,
                        options: ["Analysis", "Build", "Test", "Ship"],
                        answer: 0,
                        explanation: "Thorough analysis prevents design flaws that are expensive to fix later."
                    },
                    {
                        question: `What does this return?\n\`\`\`javascript\nBoolean("false")\n\`\`\``,
                        options: ["true", "false", "Error", "undefined"],
                        answer: 0,
                        explanation: "Any non-empty string is 'truthy' in JavaScript, including the string 'false'."
                    },
                    {
                        question: `Modern standard for ${body.topic || 'this topic'}?`,
                        options: ["Legacy", "Agile", "DevOps", "ES6+"],
                        answer: 3,
                        explanation: "Current best practices leverage the latest language features and modular standards."
                    },
                    {
                        question: `Final check: ${body.topic || 'this topic'} is:`,
                        options: ["Static", "Dynamic", "Complex", "Simplified"],
                        answer: 1,
                        explanation: "Most modern implementations are dynamic to handle varying data inputs."
                    }
                ]
            };
        }

        // 6. Chat Mock
        if (endpoint.includes('/api/chat')) {
            const isBackendRunning = this.status === 'connected';
            const isAuth = this.isAuthenticated;
            
            let msg = `I'm currently in Offline Mode. I can't access my full LLM brain, but I can tell you that ${body.topic} is a fascinating subject!`;
            if (isBackendRunning && !isAuth) {
                msg += `<br><br>⚠️ <strong>Authentication Required:</strong> The backend server is running on port 5000, but you are not logged in or are viewing the app from port 5500. Please navigate to <a href="http://127.0.0.1:5000/login" style="color:var(--primary-purple); font-weight:bold;">http://127.0.0.1:5000/login</a>, log in, and use the app there to enable the live AI tutor!`;
            } else if (!isBackendRunning) {
                msg += `<br><br>🔌 <strong>Backend Offline:</strong> Please start the Python backend (<code>python app.py</code>) to enable full live AI capabilities.`;
            }
            return { response: msg };
        }

        // 7. Custom Roadmap Mock
        if (endpoint.includes('/api/custom_roadmap')) {
            return {
                beginner: [{ id: "c_01", topic: `${body.goal} Intro`, description: "Getting started with your goal." }],
                intermediate: [{ id: "c_02", topic: `${body.goal} Deep Dive`, description: "Advancing your skills." }],
                advanced: [{ id: "c_03", topic: `${body.goal} Mastery`, description: "Final projects and optimization." }]
            };
        }

        // 8. Friends & Social Mocks
        if (endpoint.includes('/api/friends/requests')) {
            return {
                requests: [
                    { id: 101, sender_id: 202, sender_name: "Alex Mercer" }
                ]
            };
        }

        if (endpoint.includes('/api/friends/list')) {
            return {
                friends: [
                    { id: 203, username: "Sarah Connor" },
                    { id: 204, username: "David Lee" }
                ]
            };
        }

        if (endpoint.includes('/api/friends/search')) {
            const q = new URLSearchParams(endpoint.split('?')[1]).get('q') || "";
            return {
                users: [
                    { id: 999, username: q || "System Admin" }
                ]
            };
        }

        if (endpoint.includes('/api/friends/request') || endpoint.includes('/api/friends/accept')) {
            return { status: "success" };
        }

        // 9. Messaging Mocks
        if (endpoint.includes('/api/messages/history/')) {
            const friendId = endpoint.split('/').pop();
            return {
                messages: [
                    { id: 1, sender_id: friendId, content: "Hey! Ready to study?", timestamp: "10:00 AM" },
                    { id: 2, sender_id: 1, content: "Sure, I'm working on Python mocks right now.", timestamp: "10:05 AM" }
                ]
            };
        }

        if (endpoint.includes('/api/messages/send')) {
            return { status: "success" };
        }

        if (endpoint.includes('/api/execute')) {
            const lang = body.language || 'python';
            const code = body.code || '';
            let output = `[Mock Output for ${lang.toUpperCase()}]\n`;
            
            // Smarter logic for simple assignments and print statements
            try {
                const lines = code.split('\n').map(l => l.trim()).filter(l => l);
                const vars = {};
                lines.forEach(line => {
                    // Match a = 10 or a=10
                    const assignMatch = line.match(/^([a-zA-Z_]\w*)\s*=\s*(\d+)$/);
                    if (assignMatch) {
                        vars[assignMatch[1]] = parseInt(assignMatch[2]);
                    }
                    
                    // Match print(a+b) or print(10+20) or print("hello")
                    const printMatch = line.match(/^print\((.*)\)$/);
                    if (printMatch) {
                        const expr = printMatch[1].trim();
                        // Handle simple addition a+b
                        const addMatch = expr.match(/^([a-zA-Z_]\w*)\s*\+\s*([a-zA-Z_]\w*)$/);
                        if (addMatch && vars[addMatch[1]] !== undefined && vars[addMatch[2]] !== undefined) {
                            output += (vars[addMatch[1]] + vars[addMatch[2]]) + '\n';
                        } 
                        // Handle simple numbers 10+20
                        else if (expr.match(/^\d+\s*\+\s*\d+$/)) {
                            output += eval(expr) + '\n';
                        }
                        // Handle strings "hello"
                        else if (expr.match(/^['"].*['"]$/)) {
                            output += expr.slice(1, -1) + '\n';
                        }
                        // Fallback
                        else {
                            output += "Executed successfully.\n";
                        }
                    }
                });
            } catch (e) {
                output += "Executed successfully.\n";
            }
            
            return { output: output.trim() };
        }

        if (endpoint.includes('/api/heartbeat')) return { status: "ok", mode: "static-bypass" };

        throw new Error("No mock available for this endpoint: " + endpoint);
    }
}

// Global instance
const apiClient = new ResilientAPIClient();

// UI integration for the status dot
window.addEventListener('DOMContentLoaded', () => {
    const statusDots = document.querySelectorAll('[id^="api-status"]');

    apiClient.onStatusChange((status) => {
        statusDots.forEach(dot => {
            if (status === 'connected') {
                dot.style.background = '#00dfd8';
                dot.style.boxShadow = '0 0 10px #00dfd8';
                dot.title = 'Backend Status: Connected';
            } else if (status === 'reconnecting') {
                dot.style.background = '#ffca28';
                dot.style.boxShadow = '0 0 10px #ffca28';
                dot.title = 'Backend Status: Reconnecting...';
            } else {
                dot.style.background = '#ff4b4b';
                dot.style.boxShadow = '0 0 10px #ff4b4b';
                dot.title = 'Backend Status: Disconnected';
            }
        });
    });
});
