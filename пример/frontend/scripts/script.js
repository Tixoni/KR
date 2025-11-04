async function register() {
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;

    const res = await fetch(`/api/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({username, password})
    });
    const data = await res.json();
    alert(`Создан пользователь: ${data.username}`);
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const res = await fetch(`/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({username, password})
    });
    const data = await res.json();
    if (res.ok && data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        window.location.href = 'upload.html';
    } else {
        alert(data.detail || 'Ошибка входа');
    }
}

async function checkSession() {
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    
    try {
        const res = await fetch(`/api/auth/check-session`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (res.ok) {
            const data = await res.json();
            console.log('User ID:', data.user_id);
            return true;
        }
        else {
            console.log('Session invalid');
            localStorage.removeItem('access_token');
            return false;
        }
    } catch (error) {
        console.error('Session check failed:', error);
        return false;
    }
}

async function logout() {
    const token = localStorage.getItem('access_token');
    if (token) {
        try {
            await fetch(`/api/auth/logout`, { method: 'POST' });
        } catch (error) {
            console.error('Logout error:', error);
        }
        localStorage.removeItem('access_token');
    }
    window.location.href = 'index.html';
}
