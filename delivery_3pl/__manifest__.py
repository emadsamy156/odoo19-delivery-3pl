{
    'name': '3PL Delivery Operations Management',
    'version': '18.0.3.0.0',
    'category': 'Operations/Delivery',
    'summary': 'Third-Party Logistics delivery operations for Saudi food delivery platforms',
    'description': """
        3PL Delivery Operations Management System
        ==========================================
        Comprehensive module for managing delivery operations with food delivery platforms
        (Keeta, HungerStation, Jahez, Noon Food, Ninja Food, etc.)

        Features:
        - Company & Branch Management (per city)
        - Versioned Contract Management (per branch) with Parcel/Service types
        - Rider Management (Independent Contractors, NOT hr.employee)
        - Advanced Pricing Engine (Per-Order, Per-Distance, Tiered Slabs, Fixed Salary, Experience & Capacity Incentives)
        - Valid DA Criteria & Experience Score Configuration
        - Daily & Monthly Performance Tracking (color-coded validity)
        - Company Target Management (A/B/C/D levels)
        - Rider Deduction Management (fuel, rent, housing, advance, food)
        - Excel Import Engine with Column Mapping
        - Settlement & Multi-stage Approval Workflow with Incentive Breakdown
        - Wallet & Penalty Management
        - BI Reports & Dashboards
    """,
    'author': '3PL Solutions',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/delivery_dashboard_views.xml',
        'views/delivery_menu.xml',
        'views/delivery_company_views.xml',
        'views/delivery_branch_views.xml',
        'views/delivery_contract_views.xml',
        'views/delivery_city_views.xml',
        'views/delivery_rider_views.xml',
        'views/delivery_pricing_views.xml',
        'views/delivery_incentive_views.xml',
        'views/delivery_performance_views.xml',
        'views/delivery_target_views.xml',
        'views/delivery_import_views.xml',
        'views/delivery_settlement_views.xml',
        'views/delivery_penalty_views.xml',
        'views/delivery_wallet_views.xml',
        'data/delivery_data.xml',
    ],
    'demo': [
        'data/delivery_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'delivery_3pl/static/src/scss/dashboard.scss',
            'delivery_3pl/static/src/js/dashboard.js',
            'delivery_3pl/static/src/xml/dashboard.xml',
        ],
    },
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 10,
}
