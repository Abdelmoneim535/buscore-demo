# -*- coding: utf-8 -*-
"""Routers - كل الـ routers المسجلة"""

# الاساسية
from app.routers.auth_routes import router as auth_router
from app.routers.settings_routes import router as settings_router

# ادارة الحافلات
from app.routers.stations_routes import router as stations_router
from app.routers.trips_routes import router as trips_router
from app.routers.buses_routes import router as buses_router

# الحجوزات والدفع
from app.routers.bookings_routes import router as bookings_router
from app.routers.payments_routes import router as payments_router

# الفروع والعملاء
from app.routers.branches_routes import router as branches_router
from app.routers.customers_routes import router as customers_router

# النظام المحاسبي (جديد)
from app.routers.accounts_routes import router as accounts_router
from app.routers.journal_entries_routes import router as journal_entries_router
from app.routers.fiscal_periods_routes import router as fiscal_periods_router
from app.routers.accounting_settings_routes import router as accounting_settings_router


from app.routers.bi_routes import router as bi_router

routers_list = [
    bi_router,
    auth_router,
    settings_router,
    stations_router,
    trips_router,
    buses_router,
    bookings_router,
    payments_router,
    branches_router,
    customers_router,
    accounts_router,
    journal_entries_router,
    fiscal_periods_router,
    accounting_settings_router,
]
