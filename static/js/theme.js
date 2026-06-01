(function() {
    // Immediately check localStorage and apply theme to html to prevent flash of unstyled content
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.documentElement.classList.add('light-theme');
    } else {
        document.documentElement.classList.remove('light-theme');
    }

    document.addEventListener('DOMContentLoaded', () => {
        // Sync body class
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
        } else {
            document.body.classList.remove('light-theme');
        }

        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isLight = document.body.classList.contains('light-theme');
                if (isLight) {
                    document.body.classList.remove('light-theme');
                    document.documentElement.classList.remove('light-theme');
                    localStorage.setItem('theme', 'dark');
                } else {
                    document.body.classList.add('light-theme');
                    document.documentElement.classList.add('light-theme');
                    localStorage.setItem('theme', 'light');
                }
            });
        }
    });
})();
