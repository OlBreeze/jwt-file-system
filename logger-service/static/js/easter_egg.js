let clickCount = 0;
let clickTimer = null;

function activateEasterEgg() {
    clickCount++;

    // If clicked 3 times within 2 seconds – trigger enhanced version
    if (clickCount === 1) {
        clickTimer = setTimeout(() => {
            clickCount = 0;
        }, 2000);
    }

    const isTripleClick = clickCount >= 3;

    if (isTripleClick) {
        clickCount = 0;
        clearTimeout(clickTimer);
        createConfetti(150);
    }
}

function createConfetti(amount = 30) {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#FFD700'];

    for (let i = 0; i < amount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            const size = Math.random() * 10 + 5;
            const leftPos = Math.random() * 100;
            const animDuration = Math.random() * 3 + 2;
            const delay = Math.random() * 0.5;

            confetti.style.cssText = `
                position: fixed;
                top: -20px;
                left: ${leftPos}%;
                width: ${size}px;
                height: ${size}px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                animation: fall ${animDuration}s linear ${delay}s;
                z-index: 9999;
                pointer-events: none;
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
            `;
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), (animDuration + delay) * 1000);
        }, i * 30);
    }
};
