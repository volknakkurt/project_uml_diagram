# Copyright 2024 Akkurt Volkan
# License AGPL-3.0.


{
    "name": "Project Update Management",
    "version": "17.0.1.0.1",
    "author": "Volkan",
    "license": "AGPL-3",
    "complexity": "normal",
    "depends": ["base", "web", "project", "analytic", "sale", "purchase"],
    "data": [
        'security/ir.model.access.csv',
        'views/mermaid_views.xml',
        'views/project_node.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'project_update_management/static/src/**/*.js',
            'project_update_management/static/src/**/*.xml',
        ],
    },
    "auto_install": False,
    "installable": True,
    "application": True,
}
