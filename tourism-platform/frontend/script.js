


// --------------------------------------------------------------------------------Глобальные переменные
let currentUser = null;

var lala = new Audio("./sounds/gunshot-mem-short.mp3")
console.log(lala)

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
  const usersNav = document.getElementById('users-nav');
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
      usersNav.classList.remove('hidden');
      // Показываем кнопки для админов
      const createButton = document.getElementById('create-tour-button');
      const testButton = document.getElementById('test-tour-button');
      if (createButton) {
        createButton.style.display = 'block';
      }
      if (testButton) {
        testButton.style.display = 'block';
      }
    } else {
      console.log('👤 Скрываем секцию администратора');
      adminSection.classList.add('hidden');
      usersNav.classList.add('hidden');
      // Скрываем кнопки для админов
      const createButton = document.getElementById('create-tour-button');
      const testButton = document.getElementById('test-tour-button');
      if (createButton) {
        createButton.style.display = 'none';
      }
      if (testButton) {
        testButton.style.display = 'none';
      }
    }
    
    loadCurrentUser();
    // loadTours() будет вызван в loadCurrentUser() после загрузки данных пользователя
  } else {
    authBtn.classList.remove('hidden');
    logoutBtn.classList.add('hidden');
    userDisplay.classList.add('hidden');
    bookingsNav.classList.remove('authenticated');
    usersNav.classList.add('hidden');
    adminSection.classList.add('hidden');
    currentUser = null;
    
    // Скрываем все кнопки для админов
    const createButton = document.getElementById('create-tour-button');
    const testButton = document.getElementById('test-tour-button');
    if (createButton) {
      createButton.style.display = 'none';
    }
    if (testButton) {
      testButton.style.display = 'none';
    }
    
    // Обновляем туры после выхода, чтобы скрыть кнопки администратора
    loadTours();
  }
}

async function loadCurrentUser() {
  try {
    console.log('👤 Загружаем данные пользователя...');
    
    // Добавляем таймаут для запроса
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 секунд таймаут
    
    const res = await fetch('/api/auth/users/me', { 
      headers: authHeader(),
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    
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
    }
  } catch (error) {
    console.error('Ошибка загрузки пользователя:', error);
    
    // Если токен истек или недействителен, выходим из системы
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      console.log('Токен истек, выходим из системы');
      setToken(null);
      updateAuthState(false);
    }
  }
}

async function loadTours(){
  try {
    // Показываем индикатор загрузки
    const toursList = document.getElementById('tours-list');
    toursList.innerHTML = '<div class="card loading">🔄 Загрузка туров...</div>';
    
    const dest = document.getElementById('filter-destination').value.trim();
    const url = dest ? `/api/tours/tours?destination=${encodeURIComponent(dest)}` : `/api/tours/tours`;
    
    // Добавляем таймаут для запроса
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 секунд таймаут
    
    try {
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      
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
    } catch (fetchError) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        throw new Error('Превышено время ожидания. Попробуйте еще раз.');
      }
      throw fetchError;
    }
  } catch (error) {
    console.error('Ошибка загрузки туров:', error);
    let errorMessage = 'Ошибка загрузки туров';
    
    if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Сервер недоступен. Проверьте подключение к интернету.';
    } else if (error.message.includes('timeout')) {
      errorMessage = 'Превышено время ожидания. Попробуйте еще раз.';
    } else if (error.message.includes('404')) {
      errorMessage = 'Сервис туров недоступен.';
    } else {
      errorMessage = `Ошибка: ${escapeHtml(error.message)}`;
    }
    
    document.getElementById('tours-list').innerHTML = `<div class="card error">${errorMessage}</div>`;
  }
}

// Функция бронирования тура в один клик
async function bookTour(tourId) {
  // Убираем автоматическое воспроизведение звука для лучшего UX
  // lala.play();// -----------звук
  if (!getToken()) {
    toggleAuthModal();
    return;
  }
  
  if (!currentUser) {
    alert('Ошибка: информация о пользователе не загружена. Попробуйте войти заново.');
    return;
  }
  
  if (!currentUser.id) {
    console.error('currentUser:', currentUser);
    alert('Ошибка: ID пользователя не найден. Попробуйте войти заново.');
    return;
  }
  
  try {
    console.log('Начинаем бронирование тура:', tourId);
    console.log('Данные пользователя:', currentUser);
    
    // Показываем индикатор загрузки
    const bookButton = document.querySelector(`button[onclick="bookTour(${tourId})"]`);
    const originalText = bookButton.textContent;
    bookButton.textContent = '🔄 Бронирование...';
    bookButton.disabled = true;
    
    // Добавляем таймаут для запроса
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 секунд таймаут
    
    try {
      // Получаем информацию о туре
      const tourRes = await fetch(`/api/tours/tours/${tourId}`, { 
        headers: authHeader(),
        signal: controller.signal 
      });
      clearTimeout(timeoutId);
      
      if (!tourRes.ok) {
        if (tourRes.status === 404) {
          throw new Error('Тур не найден или был удален');
        } else if (tourRes.status === 401) {
          throw new Error('Сессия истекла. Войдите в систему заново');
        } else {
          throw new Error(`Ошибка сервера: ${tourRes.status}`);
        }
      }
      const tour = await tourRes.json();
      console.log('Данные тура:', tour);
    
    // Создаем бронирование
    const bookingPayload = {
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
        body: JSON.stringify(bookingPayload),
        signal: controller.signal
      });
      
      console.log('Ответ сервера:', res.status, res.statusText);
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
        console.error('Детали ошибки:', errorData);
        
        if (res.status === 401) {
          throw new Error('Сессия истекла. Войдите в систему заново');
        } else if (res.status === 400) {
          throw new Error(errorData.detail || 'Некорректные данные бронирования');
        } else if (res.status === 404) {
          throw new Error('Тур не найден');
        } else {
          throw new Error(errorData.detail || `Ошибка сервера: ${res.status}`);
        }
      }
      
      const bookingResult = await res.json();
      console.log('Результат бронирования:', bookingResult);
      
      alert(`✅ Тур "${tour.title}" успешно забронирован!`);
      loadTours(); // Обновляем список туров
      
    } catch (fetchError) {
      clearTimeout(timeoutId);
      if (fetchError.name === 'AbortError') {
        throw new Error('Превышено время ожидания. Попробуйте еще раз.');
      }
      throw fetchError;
    }
  } catch (error) {
    console.error('Ошибка бронирования:', error);
    
    let errorMessage = 'Ошибка бронирования';
    if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Сервер недоступен. Проверьте подключение к интернету.';
    } else if (error.message.includes('timeout')) {
      errorMessage = 'Превышено время ожидания. Попробуйте еще раз.';
    } else {
      errorMessage = error.message;
    }
    
    alert(`❌ ${errorMessage}`);
  } finally {
    // Восстанавливаем кнопку
    const bookButton = document.querySelector(`button[onclick="bookTour(${tourId})"]`);
    if (bookButton) {
      bookButton.textContent = originalText;
      bookButton.disabled = false;
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
      res = await fetch(`/api/tours/tours/${tourId}`, { 
        method: 'PUT', 
        headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
        body: JSON.stringify(payload)
      });
    } else {
      // Создание нового тура
      console.log('➕ Создание нового тура');
      res = await fetch('/api/tours/tours', { 
        method: 'POST', 
        headers: {...{'Content-Type': 'application/json'}, ...authHeader()}, 
        body: JSON.stringify(payload)
      });
    }
    
    console.log('Response status:', res.status);
    
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      console.error('Ошибка создания тура:', errorData);
      throw new Error(errorData.detail || `HTTP ${res.status}`);
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
  // Убираем автоматическое воспроизведение звука
  // lala.play();// -----------звук
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
    alert(`❌ Ошибка: ${error.message}`);
  }
}

// Удаление тура
async function deleteTour(tourId) {
  // Убираем автоматическое воспроизведение звука
  // lala.play();// -----------звук
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
    
    alert('✅ Тур успешно удален!');
    loadTours();
  } catch (error) {
    console.error('Ошибка удаления тура:', error);
    alert(`❌ Ошибка удаления: ${error.message}`);
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
  const res = await fetch(url, { headers: authHeader() });
    
    if (!res.ok) {
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
  // Проверяем, существует ли тур
  const tourInfo = b.tour_info || {};
  const tourExists = tourInfo.title && tourInfo.destination;
  
  return `
    <div class="card booking-card ${b.status}">
      <h4>🎫 Бронирование</h4>
      <div class="booking-info">
        ${tourExists ? `
          <div><strong>🎯 Тур:</strong> ${escapeHtml(tourInfo.title)}</div>
          <div><strong>📍 Направление:</strong> ${escapeHtml(tourInfo.destination)}</div>
        ` : `
          <div class="tour-deleted">⚠️ Тур был удален администратором</div>
        `}
        <div>📅 Дата поездки: ${new Date(b.travel_date).toLocaleDateString('ru-RU')}</div>
        <div>👥 Участники: ${b.participants_count}</div>
        <div class="price">💰 Сумма: ${b.total_price} ₽</div>
        <div class="status">
          <span class="status-badge ${b.status}">${getStatusText(b.status)}</span>
          <span class="payment-badge ${b.payment_status}">${getPaymentText(b.payment_status)}</span>
        </div>
      </div>
      <div class="booking-actions">
        ${b.status==='pending' && tourExists ? `<button class="confirm-btn" onclick="confirmBooking(${b.id})">✅ Подтвердить</button>`:''}
        ${b.status!=='cancelled' && b.status!=='completed' ? `<button class="cancel-btn" onclick="cancelBooking(${b.id})">❌ Отменить</button>`:''}
        ${!tourExists ? `<div class="tour-deleted-note">Бронирование автоматически отменено</div>`:''}
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
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
  loadBookings();
  } catch (error) {
    console.error('Ошибка отмены бронирования:', error);
    alert(`Ошибка отмены бронирования: ${error.message}`);
  }
}

async function confirmBooking(id){
  try {
    const res = await fetch(`/api/bookings/bookings/${id}/confirm`, { method:'POST', headers: authHeader() });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
  loadBookings();
  } catch (error) {
    console.error('Ошибка подтверждения бронирования:', error);
    alert(`Ошибка подтверждения бронирования: ${error.message}`);
  }
}

function escapeHtml(s){
  return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

// Функции авторизации
async function login(e){
  e.preventDefault();
  // Убираем автоматическое воспроизведение звука
  // lala_eagle.play();// -----------звук
  
  // Валидация формы
  const form = e.target;
  const username = form.username.value.trim();
  const password = form.password.value;
  
  if (!username || !password) {
    document.getElementById('login-status').textContent = '❌ Заполните все поля';
    document.getElementById('login-status').className = 'status error';
    return;
  }
  
  if (username.length < 3) {
    document.getElementById('login-status').textContent = '❌ Логин должен содержать минимум 3 символа';
    document.getElementById('login-status').className = 'status error';
    return;
  }
  
  if (password.length < 6) {
    document.getElementById('login-status').textContent = '❌ Пароль должен содержать минимум 6 символов';
    document.getElementById('login-status').className = 'status error';
    return;
  }
  
  try {
    // Показываем индикатор загрузки
    document.getElementById('login-status').textContent = '🔄 Вход в систему...';
    document.getElementById('login-status').className = 'status';
    
    const payload = { username, password };
    const res = await fetch('/api/auth/login', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(payload)
    });
    
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
  
  // Валидация формы
  const form = e.target;
  const username = form.username.value.trim();
  const password = form.password.value;
  const email = form.email.value.trim();
  const name = form.name.value.trim();
  const phone = form.phone.value.trim();
  
  if (!username || !password || !email || !name) {
    document.getElementById('register-status').textContent = '❌ Заполните все обязательные поля';
    document.getElementById('register-status').className = 'status error';
    return;
  }
  
  if (username.length < 3) {
    document.getElementById('register-status').textContent = '❌ Логин должен содержать минимум 3 символа';
    document.getElementById('register-status').className = 'status error';
    return;
  }
  
  if (password.length < 6) {
    document.getElementById('register-status').textContent = '❌ Пароль должен содержать минимум 6 символов';
    document.getElementById('register-status').className = 'status error';
    return;
  }
  
  // Простая валидация email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    document.getElementById('register-status').textContent = '❌ Введите корректный email';
    document.getElementById('register-status').className = 'status error';
    return;
  }
  
  if (name.length < 2) {
    document.getElementById('register-status').textContent = '❌ Имя должно содержать минимум 2 символа';
    document.getElementById('register-status').className = 'status error';
    return;
  }
  
  try {
    // Показываем индикатор загрузки
    document.getElementById('register-status').textContent = '🔄 Создание аккаунта...';
    document.getElementById('register-status').className = 'status';
    
    const payload = { 
      username,
      password,
      email,
      name,
      phone: phone || null
    };
    const res = await fetch('/api/auth/users', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(payload)
    });
    
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

async function logout(){ 
  // Убираем автоматическое воспроизведение звука
  // lala.play();// -----------звук
  setToken(null); 
  showSection('tours'); // Переключаемся на туры
}


// Функция для загрузки всех пользователей (только для админов)
async function loadAllUsers() {
  if (!isAdmin()) {
    alert('❌ Доступ запрещен. Только администраторы могут просматривать список пользователей.');
    return;
  }

  try {
    console.log('👥 Загружаем список всех пользователей...');
    const res = await fetch('/api/auth/users', { 
      headers: authHeader() 
    });
    
    if (!res.ok) {
      throw new Error(`Ошибка загрузки пользователей: ${res.status}`);
    }
    
    const users = await res.json();
    console.log('👥 Получены пользователи:', users);
    
    const root = document.getElementById('users-list');
    if (!root) {
      console.error('❌ Элемент users-list не найден');
      return;
    }
    
    if (users.length === 0) {
      root.innerHTML = '<div class="card info">👥 Пользователи не найдены</div>';
      return;
    }
    
    root.innerHTML = users.map(user => `
      <div class="card">
        <h4>👤 ${escapeHtml(user.username)}</h4>
        <div class="user-details">
          <div><strong>ID:</strong> ${user.id}</div>
          <div><strong>Email:</strong> ${escapeHtml(user.email || 'Не указан')}</div>
          <div><strong>Дата регистрации:</strong> ${new Date(user.created_at).toLocaleDateString()}</div>
          <div class="user-status ${user.is_active ? 'active' : 'inactive'}">
            ${user.is_active ? '✅ Активен' : '❌ Неактивен'}
          </div>
        </div>
      </div>
    `).join('');
    
  } catch (error) {
    console.error('❌ Ошибка загрузки пользователей:', error);
    const root = document.getElementById('users-list');
    if (root) {
      root.innerHTML = `<div class="card error">❌ Ошибка загрузки пользователей: ${escapeHtml(error.message)}</div>`;
    }
  }
}

// Функция для создания тестового тура (только для администраторов)
async function createTestTour() {
  // Проверяем права администратора
  if (!isAdmin()) {
    alert('❌ Только администраторы могут создавать тестовые туры');
    return;
  }
  
  try {
    // Показываем индикатор загрузки
    const testButton = document.getElementById('test-tour-button');
    const originalText = testButton.textContent;
    testButton.textContent = '🔄 Создание...';
    testButton.disabled = true;
    
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
      console.log('✅ Тестовый тур создан');
      alert('✅ Тестовый тур успешно создан!');
      loadTours();
    } else {
      const errorData = await res.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      console.error('Ошибка создания тестового тура:', errorData);
      alert(`❌ Ошибка создания тестового тура: ${errorData.detail || res.status}`);
    }
  } catch (error) {
    console.error('Ошибка создания тестового тура:', error);
    alert(`❌ Ошибка создания тестового тура: ${error.message}`);
  } finally {
    // Восстанавливаем кнопку
    const testButton = document.getElementById('test-tour-button');
    if (testButton) {
      testButton.textContent = originalText;
      testButton.disabled = false;
    }
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
    alert('❌ Необходимо войти в систему для создания тура');
    toggleAuthModal();
    return;
  }
  
  // Проверяем права администратора
  if (!isAdmin()) {
    alert('❌ Только администраторы могут создавать туры');
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
  
  // Добавляем кнопки для администраторов
  // Кнопка создания тестового тура (только для админов)
  const testButton = document.createElement('button');
  testButton.textContent = 'Создать тестовый тур';
  testButton.onclick = createTestTour;
  testButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; background: #dc3545; color: white; padding: 10px 15px; border: none; border-radius: 8px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); display: none;';
  testButton.id = 'test-tour-button';
  document.body.appendChild(testButton);
  
  // Кнопка создания тура (только для админов)
  const createButton = document.createElement('button');
  createButton.textContent = 'Создать тур';
  createButton.onclick = showCreateTourForm;
  createButton.style.cssText = 'position: fixed; bottom: 20px; right: 180px; z-index: 9999; background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 8px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); display: none;';
  createButton.id = 'create-tour-button';
  document.body.appendChild(createButton);
});


