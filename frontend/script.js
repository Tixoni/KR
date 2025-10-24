// Глобальные переменные
let currentUser = null;

var lala = new Audio("./sounds/gunshot-mem-short.mp3")
var lala_eagle = new Audio("./sounds/eagle.mp3")

// Список администраторов (в реальном приложении это должно быть в базе данных)
const ADMIN_USERS = ['admin', 'manager', 'root', 'boss']; // Добавьте сюда логины администраторов

function showSection(name){
  document.getElementById('section-tours').classList.toggle('hidden', name!=='tours');
  document.getElementById('section-bookings').classList.toggle('hidden', name!=='bookings');
}

// Функции для работы с модальным окном авторизации
function toggleAuthModal() {
  const modal = document.getElementById('auth-modal');
  modal.classList.toggle('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
  // Очищаем формы
  document.getElementById('login-form').reset();
  document.getElementById('register-form').reset();
  // Очищаем статусы
  document.getElementById('login-status').textContent = '';
  document.getElementById('register-status').textContent = '';
}

function switchAuthTab(tab) {
  // Убираем активный класс со всех табов
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.auth-tab').forEach(tab => tab.classList.remove('active'));
  
  // Добавляем активный класс к выбранному табу
  if (tab === 'login') {
    document.querySelector('.tab-btn:first-child').classList.add('active');
    document.getElementById('login-tab').classList.add('active');
  } else {
    document.querySelector('.tab-btn:last-child').classList.add('active');
    document.getElementById('register-tab').classList.add('active');
  }
}

// Функции для управления авторизацией
function setToken(token){
  if(token){ 
    localStorage.setItem('token', token); 
    updateAuthState(true);
  } else { 
    localStorage.removeItem('token'); 
    updateAuthState(false);
  }
}

function getToken(){ 
  return localStorage.getItem('token'); 
}

function authHeader(){
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

// Универсальная функция для обработки 401 ошибок
function handleUnauthorized() {
  console.log('Токен истек, выходим из системы');
  setToken(null);
  updateAuthState(false);
}

// Функция проверки роли администратора
function isAdmin() {
  const isAdminUser = currentUser && ADMIN_USERS.includes(currentUser.username);
  console.log('🔍 Проверка прав администратора:', {
    currentUser: currentUser?.username,
    isAdmin: isAdminUser,
    adminUsers: ADMIN_USERS
  });
  return isAdminUser;
}

function updateAuthState(isAuthenticated) {
  const authBtn = document.getElementById('auth-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const userDisplay = document.getElementById('user-display');
  const bookingsNav = document.getElementById('bookings-nav');
  const adminSection = document.getElementById('admin-section');
  
  if (isAuthenticated) {
    authBtn.classList.add('hidden');
    logoutBtn.classList.remove('hidden');
    userDisplay.classList.remove('hidden');
    bookingsNav.classList.add('authenticated');
    
    // Показываем секцию администратора только для админов
    if (isAdmin()) {
      console.log('👑 Показываем секцию администратора');
      adminSection.classList.remove('hidden');
      // Показываем кнопку создания тура
      const createButton = document.getElementById('create-tour-button');
      if (createButton) {
        createButton.style.display = 'block';
      }
      // Загружаем список пользователей для администратора
      loadUsers();
    } else {
      console.log('👤 Скрываем секцию администратора');
      adminSection.classList.add('hidden');
      // Скрываем кнопку создания тура
      const createButton = document.getElementById('create-tour-button');
      if (createButton) {
        createButton.style.display = 'none';
      }
    }
    
    loadCurrentUser();
    // loadTours() будет вызван в loadCurrentUser() после загрузки данных пользователя
  } else {
    authBtn.classList.remove('hidden');
    logoutBtn.classList.add('hidden');
    userDisplay.classList.add('hidden');
    bookingsNav.classList.remove('authenticated');
    adminSection.classList.add('hidden');
    currentUser = null;
    // Обновляем туры после выхода, чтобы скрыть кнопки администратора
    loadTours();
  }
}

async function loadCurrentUser() {
  try {
    console.log('👤 Загружаем данные пользователя...');
    const res = await fetch('/api/auth/users/me', { headers: authHeader() });
    console.log('Response status:', res.status);
    
    if (res.ok) {
      const userData = await res.json();
      console.log('Данные пользователя:', userData);
      currentUser = userData;
      const usernameDisplay = document.getElementById('username-display');
      const userDisplay = document.getElementById('user-display');
      const adminSection = document.getElementById('admin-section');
      
      usernameDisplay.textContent = userData.username || userData.name || 'Пользователь';
      
      // Добавляем индикатор администратора
      if (isAdmin()) {
        userDisplay.classList.add('admin');
        adminSection.classList.remove('hidden');
        // Показываем кнопку создания тура
        const createButton = document.getElementById('create-tour-button');
        if (createButton) {
          createButton.style.display = 'block';
        }
        // Загружаем список пользователей для администратора
        loadUsers();
      } else {
        userDisplay.classList.remove('admin');
        adminSection.classList.add('hidden');
        // Скрываем кнопку создания тура
        const createButton = document.getElementById('create-tour-button');
        if (createButton) {
          createButton.style.display = 'none';
        }
      }
      
      // Обновляем туры после загрузки данных пользователя
      loadTours();
    } else if (res.status === 401) {
      // Если токен истек (401), выходим из системы
      handleUnauthorized();
    }
  } catch (error) {
    console.error('Ошибка загрузки пользователя:', error);
  }
}

async function loadTours(){
  try {
  const dest = document.getElementById('filter-destination').value.trim();
  const url = dest ? `/api/tours/tours?destination=${encodeURIComponent(dest)}` : `/api/tours/tours`;
    // GET /tours не требует аутентификации, поэтому не передаем токен
    const res = await fetch(url);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
  const data = await res.json();
  const root = document.getElementById('tours-list');
    const isAuthenticated = !!getToken();
    const isAdminUser = isAdmin();
    
    console.log('🔍 Состояние при загрузке туров:', {
      isAuthenticated,
      isAdminUser,
      currentUser: currentUser?.username,
      adminUsers: ADMIN_USERS
    });
    
  root.innerHTML = data.map(t => {
    console.log(`🔍 Обрабатываем тур ${t.id}:`, {
      title: t.title,
      isAdminUser,
      isAuthenticated
    });
    
    return `<div class="card">
        <h4>${escapeHtml(t.title)}</h4>
        <div class="destination">📍 ${escapeHtml(t.destination)}</div>
        ${t.description ? `<div class="description">${escapeHtml(t.description)}</div>` : ''}
        <div class="price">${t.price} ₽</div>
        <div class="duration">⏱️ ${t.duration_days} дней</div>
        <div class="available ${t.available ? 'true' : 'false'}">
          ${t.available ? '✅ Доступен' : '❌ Недоступен'}
        </div>
        ${t.features && t.features.length > 0 ? 
          `<div class="features">${t.features.map(f => `• ${escapeHtml(f)}`).join('<br>')}</div>` : 
          ''
        }
        <div class="card-actions">
          <button class="book-btn" onclick="bookTour(${t.id})" ${!t.available || !isAuthenticated ? 'disabled' : ''}>
            ${!isAuthenticated ? '🔒 Войдите для бронирования' : !t.available ? '❌ Недоступен' : '🎯 Забронировать'}
          </button>
          ${isAdminUser ? `
            <div class="admin-actions">
              <button class="edit-btn" onclick="editTour(${t.id})">✏️ Редактировать</button>
              <button class="delete-btn" onclick="deleteTour(${t.id})">🗑️ Удалить</button>
            </div>
          ` : ''}
        </div>
    </div>`;
  }).join('');
  } catch (error) {
    console.error('Ошибка загрузки туров:', error);
    document.getElementById('tours-list').innerHTML = `<div class="card error">Ошибка загрузки туров: ${escapeHtml(error.message)}</div>`;
  }
}

// Функция бронирования тура в один клик
async function bookTour(tourId) {
  lala.play();
  if (!getToken()) {
    toggleAuthModal();
    return;
  }
  
  if (!currentUser) {
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert('Ошибка: информация о пользователе не загружена. Попробуйте войти заново.');
    }
    return;
  }
  
  if (!currentUser.id) {
    console.error('currentUser:', currentUser);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert('Ошибка: ID пользователя не найден. Попробуйте войти заново.');
    }
    return;
  }
  
  try {
    console.log('Начинаем бронирование тура:', tourId);
    console.log('Данные пользователя:', currentUser);
    
    // Получаем информацию о туре
    const tourRes = await fetch(`/api/tours/tours/${tourId}`, { headers: authHeader() });
    if (!tourRes.ok) {
      throw new Error(`Тур не найден: HTTP ${tourRes.status}`);
    }
    const tour = await tourRes.json();
    console.log('Данные тура:', tour);
    
    // Создаем бронирование
    const bookingPayload = {
      title: tour.title,
      user_id: currentUser.id,
      tour_id: parseInt(tourId),
      participants_count: 1,
      travel_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // через неделю
      contact_phone: currentUser.phone || '',
      contact_email: currentUser.email || '',
      special_requests: null
    };
    
    console.log('Отправляем данные бронирования:', bookingPayload);
    
    const res = await fetch('/api/bookings/bookings', { 
      method: 'POST', 
      headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
      body: JSON.stringify(bookingPayload)
    });
    
    console.log('Ответ сервера:', res.status, res.statusText);
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      console.error('Детали ошибки:', errorData);
      throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    
    const bookingResult = await res.json();
    console.log('Результат бронирования:', bookingResult);
    
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`✅ Тур "${tour.title}" успешно забронирован!`);
    } else {
      console.log(`✅ Тур "${tour.title}" успешно забронирован!`);
    }
    loadTours(); // Обновляем список туров
  } catch (error) {
    console.error('Ошибка бронирования:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`❌ Ошибка бронирования: ${error.message}`);
    }
  }
}

// Обработка формы создания/редактирования тура
async function handleTourForm(e){
  e.preventDefault();
  try {
    console.log('🔧 Обработка формы тура...');
  const form = e.target;
    const tourId = document.getElementById('tour-id').value;
    console.log('Tour ID:', tourId);
    
  const features = (form.features.value || '').split(',').map(s=>s.trim()).filter(Boolean);
  const payload = {
    title: form.title.value,
    destination: form.destination.value,
    price: Number(form.price.value),
    duration_days: Number(form.duration_days.value),
    description: form.description.value || null,
    features: features.length? features : null,
    available: true
  };
    
    console.log('Payload:', payload);
    
    let res;
    if (tourId) {
      // Редактирование существующего тура
      console.log('🔄 Редактирование тура:', tourId);
      console.log('Текущий пользователь:', currentUser);
      console.log('Токен авторизации:', getToken() ? 'Есть' : 'Нет');
      console.log('Заголовки запроса:', {...{'Content-Type': 'application/json'}, ...authHeader()});
      res = await fetch(`/api/tours/tours/${tourId}`, { 
        method: 'PUT', 
        headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
        body: JSON.stringify(payload)
      });
    } else {
      // Создание нового тура
      console.log('➕ Создание нового тура');
      console.log('Текущий пользователь:', currentUser);
      console.log('Токен авторизации:', getToken() ? 'Есть' : 'Нет');
      res = await fetch('/api/tours/tours', { 
        method: 'POST', 
        headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
        body: JSON.stringify(payload)
      });
    }
    
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      let errorData;
      try {
        errorData = await res.json();
      } catch (jsonError) {
        console.error('Ошибка парсинга JSON ответа:', jsonError);
        errorData = { detail: `HTTP ${res.status}: ${res.statusText}` };
      }
      console.error('Ошибка создания/обновления тура:', errorData);
      console.error('Response status:', res.status);
      console.error('Response statusText:', res.statusText);
      throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    
    const statusText = tourId ? 'Тур обновлен' : 'Тур создан';
    document.getElementById('admin-tour-status').textContent = `✅ ${statusText}`;
    document.getElementById('admin-tour-status').className = 'status success';
    
    form.reset();
    document.getElementById('tour-id').value = '';
    resetTourForm();
    loadTours();
  } catch (error) {
    console.error('Ошибка обработки тура:', error);
    document.getElementById('admin-tour-status').textContent = `❌ Ошибка: ${error.message}`;
    document.getElementById('admin-tour-status').className = 'status error';
  }
}

// Редактирование тура
async function editTour(tourId) {
  lala_eagle.play();
  try {
    console.log('✏️ Редактирование тура:', tourId);
    const res = await fetch(`/api/tours/tours/${tourId}`, { headers: authHeader() });
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || 'Тур не найден');
    }
    
    const tour = await res.json();
    console.log('Загруженный тур:', tour);
    
    // Заполняем форму данными тура
    document.getElementById('tour-id').value = tour.id;
    document.querySelector('input[name="title"]').value = tour.title || '';
    document.querySelector('input[name="destination"]').value = tour.destination || '';
    document.querySelector('input[name="price"]').value = tour.price || '';
    document.querySelector('input[name="duration_days"]').value = tour.duration_days || '';
    document.querySelector('textarea[name="description"]').value = tour.description || '';
    document.querySelector('input[name="features"]').value = tour.features ? tour.features.join(', ') : '';
    
    // Обновляем интерфейс формы
    document.getElementById('admin-form-title').textContent = '✏️ Редактировать тур';
    document.getElementById('submit-tour-btn').textContent = 'Обновить тур';
    document.getElementById('cancel-edit-btn').classList.remove('hidden');
    
    // Прокручиваем к форме
    document.getElementById('admin-section').scrollIntoView({ behavior: 'smooth' });
    
    console.log('✅ Форма заполнена для редактирования');
    
  } catch (error) {
    console.error('Ошибка загрузки тура для редактирования:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`❌ Ошибка: ${error.message}`);
    }
  }
}

// Удаление тура
async function deleteTour(tourId) {
  console.log('🗑️ Удаление тура:', tourId);
  
  // Убираем подтверждение для localhost
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    if (!confirm('Вы уверены, что хотите удалить этот тур?')) {
      return;
    }
  }
  
  try {
    console.log('Отправляем запрос на удаление...');
    const res = await fetch(`/api/tours/tours/${tourId}`, { 
      method: 'DELETE', 
      headers: authHeader() 
    });
    
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      console.error('Ошибка удаления:', errorData);
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert('✅ Тур успешно удален!');
    } else {
      console.log('✅ Тур успешно удален!');
    }
    loadTours();
  } catch (error) {
    console.error('Ошибка удаления тура:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`❌ Ошибка удаления: ${error.message}`);
    }
  }
}

// Отмена редактирования
function cancelEditTour() {
  resetTourForm();
}

// Сброс формы к состоянию создания
function resetTourForm() {
  document.getElementById('admin-form-title').textContent = '➕ Создать новый тур';
  document.getElementById('submit-tour-btn').textContent = 'Создать тур';
  document.getElementById('cancel-edit-btn').classList.add('hidden');
  document.getElementById('tour-id').value = '';
  document.getElementById('admin-tour-status').textContent = '';
  document.getElementById('admin-tour-status').className = 'status';
}

async function loadBookings(){
  if (!getToken()) {
    document.getElementById('bookings-list').innerHTML = '<div class="card error">🔒 Войдите в систему для просмотра бронирований</div>';
    return;
  }
  
  try {
    const url = `/api/bookings/bookings/user/${currentUser.id}`;
    console.log('Загружаем бронирования для пользователя:', currentUser.id);
    console.log('URL:', url);
    console.log('Заголовки:', authHeader());
    
    const res = await fetch(url, { headers: authHeader() });
    
    if (!res.ok) {
      // Если токен истек (401), выходим из системы
      if (res.status === 401) {
        handleUnauthorized();
        document.getElementById('bookings-list').innerHTML = '<div class="card error">🔒 Сессия истекла. Войдите в систему заново.</div>';
        return;
      }
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
  const data = await res.json();
  const root = document.getElementById('bookings-list');
    
    if (data.length === 0) {
      root.innerHTML = '<div class="card">📋 У вас пока нет бронирований</div>';
      return;
    }
    
    // Разделяем бронирования на актуальные и отменённые
    const activeBookings = data.filter(b => b.status !== 'cancelled');
    const cancelledBookings = data.filter(b => b.status === 'cancelled');
    
    let html = '';
    
    // Актуальные бронирования
    if (activeBookings.length > 0) {
      html += `
        <div class="bookings-section">
          <h3>📋 Актуальные бронирования</h3>
          <div class="bookings-grid">
            ${activeBookings.map(b => createBookingCard(b)).join('')}
          </div>
        </div>
      `;
    }
    
    // Отменённые бронирования
    if (cancelledBookings.length > 0) {
      html += `
        <div class="bookings-section">
          <h3>❌ Отменённые бронирования</h3>
          <div class="bookings-grid cancelled">
            ${cancelledBookings.map(b => createBookingCard(b)).join('')}
          </div>
        </div>
      `;
    }
    
    if (activeBookings.length === 0 && cancelledBookings.length === 0) {
      html = '<div class="card">📋 У вас пока нет бронирований</div>';
    }
    
    root.innerHTML = html;
  } catch (error) {
    console.error('Ошибка загрузки бронирований:', error);
    document.getElementById('bookings-list').innerHTML = `<div class="card error">Ошибка загрузки бронирований: ${escapeHtml(error.message)}</div>`;
  }
}

// Функция создания карточки бронирования
function createBookingCard(b) {
  return `
    <div class="card booking-card ${b.status}">
      <h4>🎫 Бронь #${b.id}</h4>
      <div class="booking-info">
        <div>🏨 Тур: ${b.title}</div>
        <div>📅 Дата поездки: ${new Date(b.travel_date).toLocaleDateString('ru-RU')}</div>
        <div>👥 Участники: ${b.participants_count}</div>
        <div class="price">💰 Сумма: ${b.total_price} ₽</div>
        <div class="status">
          <span class="status-badge ${b.status}">${getStatusText(b.status)}</span>
          <span class="payment-badge ${b.payment_status}">${getPaymentText(b.payment_status)}</span>
        </div>
      </div>
      <div class="booking-actions">
        ${b.status==='pending' ? `<button class="confirm-btn" onclick="confirmBooking(${b.id})">✅ Подтвердить</button>`:''}
        ${b.status!=='cancelled' && b.status!=='completed' ? `<button class="cancel-btn" onclick="cancelBooking(${b.id})">❌ Отменить</button>`:''}
      </div>
    </div>
  `;
}

function getStatusText(status) {
  const statusMap = {
    'pending': '⏳ Ожидает',
    'confirmed': '✅ Подтверждено',
    'cancelled': '❌ Отменено',
    'completed': '🎉 Завершено'
  };
  return statusMap[status] || status;
}

function getPaymentText(status) {
  const paymentMap = {
    'pending': '⏳ Ожидает оплаты',
    'paid': '✅ Оплачено',
    'refunded': '💸 Возвращено'
  };
  return paymentMap[status] || status;
}


async function cancelBooking(id){
  try {
    const res = await fetch(`/api/bookings/bookings/${id}/cancel`, { method:'PUT', headers: authHeader() });
    if (!res.ok) {
      // Если токен истек (401), выходим из системы
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
  loadBookings();
  } catch (error) {
    console.error('Ошибка отмены бронирования:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`Ошибка отмены бронирования: ${error.message}`);
    }
  }
}

async function confirmBooking(id){
  try {
    const res = await fetch(`/api/bookings/bookings/${id}/confirm`, { method:'POST', headers: authHeader() });
    if (!res.ok) {
      // Если токен истек (401), выходим из системы
      if (res.status === 401) {
        handleUnauthorized();
        return;
      }
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
  loadBookings();
  } catch (error) {
    console.error('Ошибка подтверждения бронирования:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`Ошибка подтверждения бронирования: ${error.message}`);
    }
  }
}

function escapeHtml(s){
  return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

// Функции авторизации
async function login(e){
  e.preventDefault();
  try {
  const form = e.target;
  const payload = { username: form.username.value, password: form.password.value };
  const res = await fetch('/api/auth/login', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    
  const data = await res.json();
    if (data.access_token) {
      setToken(data.access_token);
      document.getElementById('login-status').textContent = '✅ Успешно!';
      document.getElementById('login-status').className = 'status success';
      form.reset();
      closeAuthModal();
    } else {
      throw new Error('Токен не получен');
    }
  } catch (error) {
    console.error('Ошибка входа:', error);
    document.getElementById('login-status').textContent = `❌ ${error.message}`;
    document.getElementById('login-status').className = 'status error';
  }
}

async function registerUser(e){
  e.preventDefault();
  try {
  const form = e.target;
  const payload = { 
    username: form.username.value,
    password: form.password.value,
    email: form.email.value,
    name: form.name.value,
    phone: form.phone.value || null
  };
  const res = await fetch('/api/auth/users', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    
    document.getElementById('register-status').textContent = '✅ Аккаунт создан!';
    document.getElementById('register-status').className = 'status success';
    form.reset();
    // Переключаемся на вкладку входа
    switchAuthTab('login');
  } catch (error) {
    console.error('Ошибка регистрации:', error);
    document.getElementById('register-status').textContent = `❌ ${error.message}`;
    document.getElementById('register-status').className = 'status error';
  }
}

function logout(){ 
  setToken(null); 
  showSection('tours'); // Переключаемся на туры
}


// Функция для создания тестового тура (только для отладки)
async function createTestTour() {
  try {
    const testTour = {
      title: "Тестовый тур в Анталью",
      destination: "Анталья",
      price: 50000,
      duration_days: 7,
      description: "Отличный тестовый тур для проверки функционала",
      features: ["Всё включено", "Экскурсии", "Трансфер"],
      available: true
    };
    
    const res = await fetch('/api/tours/tours', { 
      method: 'POST', 
      headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
      body: JSON.stringify(testTour)
    });
    
    if (res.ok) {
      console.log('Тестовый тур создан');
      loadTours();
    } else {
      console.error('Ошибка создания тестового тура:', res.status);
    }
  } catch (error) {
    console.error('Ошибка создания тестового тура:', error);
  }
}

// Функция для показа формы создания тура
function showCreateTourForm() {
  console.log('📝 Показываем форму создания тура');
  console.log('Текущий пользователь:', currentUser);
  console.log('Токен:', !!getToken());
  console.log('Является админом:', isAdmin());
  
  // Проверяем, что пользователь авторизован
  if (!getToken()) {
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert('❌ Необходимо войти в систему для создания тура');
    }
    toggleAuthModal();
    return;
  }
  
  // Проверяем права администратора
  if (!isAdmin()) {
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert('❌ Только администраторы могут создавать туры');
    }
    return;
  }
  
  // Сбрасываем форму
  resetTourForm();
  
  // Показываем секцию администратора
  const adminSection = document.getElementById('admin-section');
  adminSection.classList.remove('hidden');
  
  // Прокручиваем к форме
  adminSection.scrollIntoView({ behavior: 'smooth' });
  
  console.log('✅ Форма создания тура показана');
}

// Функции для управления пользователями
async function loadUsers() {
  if (!getToken()) {
    document.getElementById('users-list').innerHTML = '<div class="card error">🔒 Войдите в систему</div>';
    return;
  }
  
  if (!isAdmin()) {
    document.getElementById('users-list').innerHTML = '<div class="card error">❌ Недостаточно прав</div>';
    return;
  }
  
  try {
    const res = await fetch('/api/auth/users', { headers: authHeader() });
    
    if (!res.ok) {
      // Если токен истек (401), выходим из системы
      if (res.status === 401) {
        handleUnauthorized();
        document.getElementById('users-list').innerHTML = '<div class="card error">🔒 Сессия истекла. Войдите в систему заново.</div>';
        return;
      }
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const users = await res.json();
    const root = document.getElementById('users-list');
    
    if (users.length === 0) {
      root.innerHTML = '<div class="card">👥 Пользователи не найдены</div>';
      return;
    }
    
    root.innerHTML = users.map(user => createUserCard(user)).join('');
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error);
    document.getElementById('users-list').innerHTML = `<div class="card error">Ошибка загрузки пользователей: ${escapeHtml(error.message)}</div>`;
  }
}

// Функция создания карточки пользователя
function createUserCard(user) {
  const isCurrentUser = currentUser && user.id === currentUser.id;
  const isAdminUser = ADMIN_USERS.includes(user.username);
  
  return `
    <div class="card user-card ${isCurrentUser ? 'current-user' : ''}">
      <h4>👤 ${escapeHtml(user.username)} ${isCurrentUser ? '(Вы)' : ''}</h4>
      <div class="user-info">
        <div>📧 ${escapeHtml(user.email)}</div>
        <div>👋 ${escapeHtml(user.name)}</div>
        ${user.phone ? `<div>📱 ${escapeHtml(user.phone)}</div>` : ''}
        <div class="user-meta">
          <span class="user-id">ID: ${user.id}</span>
          ${isAdminUser ? '<span class="admin-badge">👑 Админ</span>' : ''}
        </div>
      </div>
      <div class="user-actions">
        ${!isCurrentUser && !isAdminUser ? `
          <button class="delete-btn" onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')">🗑️ Удалить</button>
        ` : ''}
        ${isCurrentUser ? '<span class="current-user-text">Текущий пользователь</span>' : ''}
        ${isAdminUser && !isCurrentUser ? '<span class="admin-protected">Защищенный аккаунт</span>' : ''}
      </div>
    </div>
  `;
}

// Функция удаления пользователя
async function deleteUser(userId, username) {
  console.log('🗑️ Удаление пользователя:', userId, username);
  
  // Убираем подтверждение для localhost
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    if (!confirm(`Вы уверены, что хотите удалить пользователя "${username}"?`)) {
      return;
    }
  }
  
  try {
    console.log('Отправляем запрос на удаление пользователя...');
    const res = await fetch(`/api/auth/users/${userId}`, { 
      method: 'DELETE', 
      headers: authHeader() 
    });
    
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      console.error('Ошибка удаления:', errorData);
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`✅ Пользователь "${username}" успешно удален!`);
    } else {
      console.log(`✅ Пользователь "${username}" успешно удален!`);
    }
    loadUsers(); // Обновляем список пользователей
  } catch (error) {
    console.error('Ошибка удаления пользователя:', error);
    // Убираем alert для localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      alert(`❌ Ошибка удаления: ${error.message}`);
    }
  }
}


// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Проверяем авторизацию при загрузке
  const token = getToken();
  if (token) {
    updateAuthState(true);
  } else {
    updateAuthState(false);
  }
  
  // Загружаем туры
  loadTours();
  
  // Закрываем модальное окно при клике вне его
  document.getElementById('auth-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      closeAuthModal();
    }
  });
  
  // Добавляем кнопки для отладки (только для localhost)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Кнопка создания тестового тура
    const testButton = document.createElement('button');
    testButton.textContent = 'Создать тестовый тур';
    testButton.onclick = createTestTour;
    testButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; background: #dc3545; color: white; padding: 10px 15px; border: none; border-radius: 8px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);';
    document.body.appendChild(testButton);
    
    // Кнопка создания тура (только для админов)
    const createButton = document.createElement('button');
    createButton.textContent = 'Создать тур';
    createButton.onclick = showCreateTourForm;
    createButton.style.cssText = 'position: fixed; bottom: 20px; right: 180px; z-index: 9999; background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 8px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);';
    createButton.id = 'create-tour-button';
    document.body.appendChild(createButton);
    
    // Скрываем кнопку по умолчанию
    createButton.style.display = 'none';
  }
});


