// ========================================
// 🚌 BusCore - الوظائف العامة
// ========================================

// تنسيق العملة
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SD', {
        style: 'currency',
        currency: 'SDG',
        minimumFractionDigits: 0
    }).format(amount);
}

// تنسيق التاريخ
function formatDate(dateString) {
    const date = new Date(dateString);
    const months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ];
    
    const day = date.getDate();
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    const hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'مساءً' : 'صباحاً';
    const hour12 = hours % 12 || 12;
    
    return `${day} ${month} ${year}، ${hour12}:${minutes} ${ampm}`;
}

// عرض رسالة
function showMessage(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    const container = document.querySelector('.container');
    if (container) {
        container.prepend(alertDiv);
    }
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// تحميل المحطات في القوائم المنسدلة
async function loadStations() {
    try {
        const stations = await BusCoreAPI.getStations();
        const selects = document.querySelectorAll('.station-select');
        selects.forEach(select => {
            stations.forEach(station => {
                const option = document.createElement('option');
                option.value = station.id;
                option.textContent = station.name;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Error loading stations:', error);
    }
}

// تحميل الحافلات
async function loadBuses() {
    try {
        return await BusCoreAPI.getBuses();
    } catch (error) {
        console.error('Error loading buses:', error);
        return [];
    }
}

// تحميل خيارات الأمتعة
async function loadLuggage() {
    try {
        return await BusCoreAPI.getLuggage();
    } catch (error) {
        console.error('Error loading luggage:', error);
        return [];
    }
}

// عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تحميل المحطات للقوائم المنسدلة
    loadStations();
    
    // معالجة نموذج البحث
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const departure = document.getElementById('departureStation').value;
            const arrival = document.getElementById('arrivalStation').value;
            const date = document.getElementById('travelDate').value;
            
            if (!departure || !arrival || !date) {
                showMessage('الرجاء ملء جميع الحقول', 'warning');
                return;
            }
            
            window.location.href = `/search?departure=${departure}&arrival=${arrival}&date=${date}`;
        });
    }
});