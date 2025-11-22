function punchAction(type) {
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            if (type === 'in') {
                document.querySelector('.punch-item:first-child .punch-time').textContent = time;
                document.querySelector('.status-time').textContent = `Working since ${time}`;
                showNotification('Punched In Successfully!', 'success');
            } else {
                document.querySelector('.punch-item:last-child .punch-time').textContent = time;
                document.querySelector('.status-time').textContent = `Completed work at ${time}`;
                document.querySelector('.status-badge').innerHTML = '<i class="fas fa-circle"></i> Completed';
                document.querySelector('.status-badge').className = 'status-badge status-away';
                showNotification('Punched Out Successfully!', 'success');
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                background: linear-gradient(45deg, #4CAF50, #8BC34A);
                color: white;
                border-radius: 10px;
                font-weight: 600;
                z-index: 1000;
                animation: slideInRight 0.3s ease-out;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Add some dynamic animations
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.stat-card, .card');
            
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
            });

            // Animate counters (excluding hours-today which contains time format)
            const counters = document.querySelectorAll('.stat-value:not(#hours-today)');
            counters.forEach(counter => {
                const target = parseInt(counter.textContent);
                if (!isNaN(target)) {
                    let count = 0;
                    const increment = target / 30;
                    const timer = setInterval(() => {
                        count += increment;
                        if (count >= target) {
                            counter.textContent = target;
                            clearInterval(timer);
                        } else {
                            counter.textContent = Math.ceil(count);
                        }
                    }, 50);
                }
            });
        });

        // Add hover effects for leave items
        document.querySelectorAll('.leave-item').forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.05)';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });