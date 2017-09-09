{
	'name': 'Amapola Contability Integrate',
	'description': """
		Modulo especifico para importar ingresos de efectivo, depositos y cheques
		desde un formato especifico de excel.""",
    'author': "LIBRASOFT",
    'website': "http://libra-soft.com",

	'depends': ['base','account_accountant'],
	'data': [
		'views/contability_integration.xml',
		],
    'application': True,
}