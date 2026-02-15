{
    'name': 'Style Hub Module',
    'version': '1.0',
    'summary': 'Modulo para tener una gestion organizada de una peluqueria',
    'description': 'Modulo para gestionar citas, clientes y servicios en una peluqueria de manera eficiente.',
    'author': 'Mauro',
    'category': 'Style Hub',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/stylehub_estilista_view.xml',
        'views/stylehub_servicios_view.xml',
        'views/stylehub_citas_view.xml',
        'views/stylehub_clientes_view.xml',
        'views/stylehub_menu.xml',
    ],
    'application': True,
}