document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const topicInput = document.getElementById('topic');
    const roundsInput = document.getElementById('rounds');
    const loadingIndicator = document.getElementById('loading');
    const transcriptContainer = document.getElementById('transcript');

    startBtn.addEventListener('click', async () => {
        const topic = topicInput.value.trim();
        const rounds = parseInt(roundsInput.value);

        if (!topic) {
            alert('Please enter a debate topic.');
            return;
        }

        if (rounds < 1 || rounds > 5) {
            alert('Number of rounds must be between 1 and 5.');
            return;
        }

        // Reset UI
        startBtn.disabled = true;
        loadingIndicator.style.display = 'block';
        transcriptContainer.innerHTML = '';
        transcriptContainer.style.display = 'none';

        try {
            const response = await fetch('/debate/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    rounds: rounds
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            renderTranscript(data.messages);

        } catch (error) {
            console.error('Debate simulation failed:', error);
            alert(`Error: ${error.message}`);
        } finally {
            startBtn.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    });

    function renderTranscript(messages) {
        if (!messages || messages.length === 0) {
            transcriptContainer.innerHTML = '<p>No messages generated.</p>';
            transcriptContainer.style.display = 'flex';
            return;
        }

        // Add header
        const header = document.createElement('h2');
        header.style.marginBottom = '1.5rem';
        header.style.color = 'var(--text-main)';
        header.textContent = 'Debate Transcript';
        transcriptContainer.appendChild(header);

        messages.forEach((msg, index) => {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${msg.agent.toLowerCase()}`;
            messageEl.style.animationDelay = `${index * 0.15}s`;

            const date = new Date(msg.timestamp);
            const timeString = isNaN(date.getTime()) ? msg.timestamp : date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            messageEl.innerHTML = `
                <div class="message-header">
                    <div>
                        <span class="agent-name">${msg.agent}</span>
                        <span style="margin-left: 0.6rem; opacity: 0.6; font-size: 0.9em;">Round ${msg.round}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.8rem;">
                        <span class="stance ${msg.stance}">${msg.stance}</span>
                        <span style="font-size: 0.85em; opacity: 0.7;">${timeString}</span>
                    </div>
                </div>
                <div class="message-content">
                    ${msg.message}
                </div>
            `;
            
            transcriptContainer.appendChild(messageEl);
        });

        transcriptContainer.style.display = 'flex';
        // Scroll to transcript smoothly
        setTimeout(() => {
            transcriptContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
});
