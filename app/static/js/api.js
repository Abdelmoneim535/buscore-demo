// عنوان API الأساسي
const API_BASE = '';

// دالة مساعدة للطلبات
async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
    
    const options = {
        method: method,
        headers: headers,
        credentials: 'same-origin'   // ✅ إرسال Cookie تلقائيًا
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'حدث خطأ في الطلب');
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// دوال API
const BusCoreAPI = {
    // المدن والمحطات
    getCities: () => apiRequest('/stations/cities'),
    getStations: () => apiRequest('/stations'),
    
    // المسارات والرحلات
    searchTrips: (params) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/trips/search?${query}`);
    },
    getTrips: () => apiRequest('/trips'),
    createTrip: (data) => apiRequest('/trips', 'POST', data),
    
    // الحجوزات
    createBooking: (data) => apiRequest('/bookings', 'POST', data),
    createPassenger: (data) => apiRequest('/bookings/passengers', 'POST', data),
    getLuggage: () => apiRequest('/bookings/luggage'),
    getAvailableSeats: (tripId) => apiRequest(`/bookings/available-seats/${tripId}`),
    getBookings: () => apiRequest('/bookings'),
    
    // الحافلات
    getBuses: () => apiRequest('/buses'),
    
    // ✅ المصادقة - يجب أن تكون هذه الدوال موجودة
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData,
            credentials: 'same-origin'   // ✅ استقبال Cookie من السيرفر
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'فشل تسجيل الدخول');
        }
        return response.json();
    },
    
    register: (data) => apiRequest('/auth/register', 'POST', data),
    
    getMe: () => {
        // ✅ Cookie تلقائي في الطلب
        return fetch(`${API_BASE}/auth/me`, {
            credentials: 'same-origin'
        }).then(response => {
            if (!response.ok) throw new Error('فشل جلب بيانات المستخدم');
            return response.json();
        });
    },

    logout: async () => {
        // ✅ يحذف الـ Cookie من السيرفر
        return fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'same-origin'
        });
    },
};